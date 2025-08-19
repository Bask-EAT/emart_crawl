# 오래된 상품 정보를 갱신

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, Union, List
import random

# ==============================================================================
# 1. Firebase 연동 및 스크래핑 로직 (기존과 동일)
# ==============================================================================


def initialize_firebase():
    """Firebase Admin SDK를 초기화합니다."""
    # ... (내용 동일)
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate("repository/serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK가 성공적으로 초기화되었습니다.")
        except Exception as e:
            print(f"🔥 Firebase 초기화 중 오류 발생: {e}")
            raise


def scrape_single_product(product_id: str, retry_count=0) -> Union[Dict, None]:
    """[수정됨] 429 에러 발생 시 10번 재시도하고, 원가 대체 경로를 추가한 스크래핑 함수"""
    # ... (내용 동일)
    url = f"https://emart.ssg.com/item/itemView.ssg?itemId={product_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        selling_price_tag = soup.select_one("span.cdtl_new_price.notranslate > em")
        selling_price = (
            selling_price_tag.get_text(strip=True).replace(",", "").replace("원", "")
            if selling_price_tag
            else None
        )
        original_price_tag = soup.select_one("span.cdtl_old_price > em")
        if not original_price_tag:
            original_price_tag = soup.select_one("span.cdtl_first_price > em")
        original_price = (
            original_price_tag.get_text(strip=True).replace(",", "").replace("원", "")
            if original_price_tag
            else None
        )
        if original_price and not selling_price:
            selling_price = original_price
        elif selling_price and not original_price:
            original_price = selling_price
        elif not original_price and not selling_price:
            price_tag = soup.select_one(".cdtl_row_price em.ssg_price")
            price = (
                price_tag.get_text(strip=True).replace(",", "").replace("원", "")
                if price_tag
                else "0"
            )
            original_price, selling_price = price, price
        quantity_tag = soup.select_one("div.cdtl_optprice_wrap > p.cdtl_txt_info")
        quantity = (
            " ".join(quantity_tag.get_text(strip=True).split()) if quantity_tag else ""
        )
        out_of_stock = "Y" if "품절" in str(soup.select_one(".cdtl_btn_wrap3")) else "N"
        return {
            "id": product_id,
            "original_price": original_price,
            "selling_price": selling_price,
            "quantity": quantity,
            "out_of_stock": out_of_stock,
            "last_updated": datetime.now().isoformat(),
        }
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 429:
            if retry_count < 10:
                wait_time = 10 + random.uniform(0, 5)
                print(
                    f"  -> ⏳ 429 에러: {int(wait_time)}초 후 재시도... ({retry_count+1}/10)"
                )
                time.sleep(wait_time)
                return scrape_single_product(product_id, retry_count + 1)
            else:
                print(f"  -> 🚨 오류: ID {product_id} 재시도 실패.")
                return None
        else:
            print(
                f"  -> 🚨 오류: ID {product_id} 스크래핑 실패 (HTTP 에러 {http_err.response.status_code})"
            )
            return None
    except Exception as e:
        print(f"  -> 🚨 오류: ID {product_id} 스크래핑 실패: {e}")
        return None


# ==============================================================================
# 3. 메인 로직 (핵심 수정)
# ==============================================================================


def find_and_update_stale_products():
    """Firestore 쿼리를 사용하여 업데이트가 하루 이상 지난 상품만 찾아 갱신합니다."""
    # ... (내용 동일)
    try:
        initialize_firebase()
        db = firestore.client()
        one_day_ago_iso = (datetime.now() - timedelta(days=6)).isoformat()
        print(f"🚀 기준 시간: {one_day_ago_iso} 이전에 업데이트된 상품을 찾습니다.\n")
        product_collection_ref = db.collection("emart_product")
        query = product_collection_ref.where(
            filter=FieldFilter("last_updated", "<", one_day_ago_iso)
        )
        docs_to_update = list(query.stream())
        if not docs_to_update:
            print("✅ 모든 상품이 최신 상태입니다.")
            return
        stale_product_ids = [doc.id for doc in docs_to_update]
        print(
            f"🔍 총 {len(stale_product_ids)}개의 오래된 상품을 찾았습니다. 업데이트를 시작합니다.\n"
        )
        scrape_and_update_products_by_ids(stale_product_ids)
    except Exception as e:
        print(f"\n🔥 작업 중 심각한 오류가 발생했습니다: {e}")


def scrape_and_update_products_by_ids(product_ids: List[str]):
    """
    [수정됨] 주어진 ID 목록의 정보를 스크래핑하고, 모든 DB 업데이트를 Batch로 처리합니다.
    """
    db = firestore.client()
    price_collection_ref = db.collection("emart_price")
    product_collection_ref = db.collection("emart_product")

    batch = db.batch()
    updated_count = 0

    for i, product_id in enumerate(product_ids):
        print(f"({i+1}/{len(product_ids)}) ID: {product_id} 처리 중...")

        scraped_data = scrape_single_product(product_id)
        if not scraped_data:
            continue

        # --- [핵심 수정] 모든 DB 작업을 Batch에 추가 ---

        # 1. emart_price 문서 참조 및 기존 데이터 가져오기 (쓰기 전 읽기는 필요)
        price_doc_ref = price_collection_ref.document(product_id)
        price_doc = price_doc_ref.get()
        price_history = (
            price_doc.to_dict().get("price_history", []) if price_doc.exists else []
        )

        # 2. 가격 변경 여부 확인
        price_info = {
            "original_price": scraped_data["original_price"],
            "selling_price": scraped_data["selling_price"],
            "last_updated": scraped_data["last_updated"],
        }
        prices_changed = (
            not price_history
            or str(price_history[-1].get("original_price"))
            != price_info["original_price"]
            or str(price_history[-1].get("selling_price"))
            != price_info["selling_price"]
        )

        # 3. emart_price 업데이트 내용 구성
        price_update_payload = {
            "id": product_id,
            "out_of_stock": scraped_data["out_of_stock"],
            "quantity": scraped_data["quantity"],
            "last_updated": scraped_data["last_updated"],
        }
        if prices_changed:
            price_history.append(price_info)
            price_update_payload["price_history"] = price_history

        # 4. emart_price와 emart_product 업데이트를 모두 Batch에 추가
        batch.set(price_doc_ref, price_update_payload, merge=True)

        product_doc_ref = product_collection_ref.document(product_id)
        batch.update(product_doc_ref, {"last_updated": scraped_data["last_updated"]})

        updated_count += 1
        if (
            updated_count > 0 and updated_count % 50 == 0
        ):  # 배치 쓰기는 최대 500개, 읽기 1 + 쓰기 1 = 2개 작업이므로 225쌍이 안전
            batch.commit()
            batch = db.batch()

        time.sleep(random.uniform(1, 2))

    if updated_count > 0:
        batch.commit()

    print(f"\n✨ 총 {updated_count}개 상품 정보를 성공적으로 갱신했습니다.")


if __name__ == "__main__":
    find_and_update_stale_products()
