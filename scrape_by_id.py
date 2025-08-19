import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import sys
import time
from typing import List, Dict, Union


def scrape_single_product(product_id: str) -> Union[Dict, None]:
    """
    [수정됨] 가격 뒤에 붙는 '원' 글자를 제거합니다.
    """
    url = f"https://emart.ssg.com/item/itemView.ssg?itemId={product_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"ID: {product_id} 스크래핑 시작...")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # --- [핵심 수정] ---

        # 할인가
        selling_price_tag = soup.select_one("span.cdtl_new_price.notranslate > em")
        selling_price = (
            selling_price_tag.get_text(strip=True).replace(",", "").replace("원", "")
            if selling_price_tag
            else None
        )

        # 원가
        original_price_tag = soup.select_one("span.cdtl_old_price > em")
        original_price = (
            original_price_tag.get_text(strip=True).replace(",", "").replace("원", "")
            if original_price_tag
            else None
        )

        # 가격 교차 보정 로직
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
            original_price = price
            selling_price = price

        # 용량/단위 정보
        quantity_tag = soup.select_one("div.cdtl_optprice_wrap > p.cdtl_txt_info")
        quantity = (
            " ".join(quantity_tag.get_text(strip=True).split()) if quantity_tag else ""
        )

        # 품절 정보
        out_of_stock = "Y" if "품절" in str(soup.select_one(".cdtl_btn_wrap3")) else "N"

        product_data = {
            "id": product_id,
            "original_price": original_price,
            "selling_price": selling_price,
            "quantity": quantity,
            "out_of_stock": out_of_stock,
            "last_updated": datetime.now().isoformat(),
        }

        print(f"  -> ID: {product_id} 스크래핑 완료.")
        return product_data

    except Exception as e:
        print(f"  -> 오류: ID {product_id} 정보 파싱 중 문제 발생: {e}")
        return None


def scrape_products_by_ids(product_ids: List[str]) -> List[Dict]:
    # ... (이 함수는 수정할 필요가 없습니다) ...
    if not isinstance(product_ids, list):
        return []
    all_products_data = []
    for pid in product_ids:
        clean_pid = pid.strip().strip(",")
        if not clean_pid:
            continue
        data = scrape_single_product(clean_pid)
        if data:
            all_products_data.append(data)
        time.sleep(1)
    return all_products_data


if __name__ == "__main__":
    # ... (이 부분은 수정할 필요가 없습니다) ...
    product_ids = sys.argv[1:]
    if not product_ids:
        print("사용법: python scrape_by_id.py <ID_1> <ID_2> ...")
    else:
        results = scrape_products_by_ids(product_ids)
        print("\n===== 최종 스크래핑 결과 =====")
        print(json.dumps(results, indent=4, ensure_ascii=False))
