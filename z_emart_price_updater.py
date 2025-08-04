# emart_price_updater.py

import sys
import json
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import time

def scrape_single_product_price(item_id):
    """
    단일 상품 ID에 대한 가격 정보를 스크래핑합니다.
    Args:
        item_id (str): 스크래핑할 상품의 ID.
    Returns:
        dict: 상품 ID, 판매가, 원가를 포함하는 딕셔너리.
    """
    url = f"https://www.ssg.com/item/itemView.ssg?itemId={item_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"상품 ID '{item_id}'의 가격 정보를 스크래핑합니다.")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        
        # 판매 가격 추출
        selling_price_element = soup.select_one(".ssg_price")
        selling_price = selling_price_element.get_text(strip=True).replace(",", "") if selling_price_element else None

        # 원가 (할인 전 가격) 추출
        original_price_element = soup.select_one(".ssg_price_strikethrough")
        original_price = original_price_element.get_text(strip=True).replace(",", "") if original_price_element else None

        # 결과 딕셔너리 생성
        result = {
            "id": item_id,
            "selling_price": selling_price,
            "original_price": original_price,
            "last_updated": datetime.now().isoformat(),
        }
        
        print(f"상품 ID '{item_id}' 스크래핑 완료: 판매가 {selling_price}, 원가 {original_price}")
        return result

    except requests.exceptions.RequestException as e:
        print(f"상품 ID '{item_id}' 웹사이트 연결 중 오류 발생: {e}")
        return {"item_id": item_id, "error": str(e)}
    except Exception as e:
        print(f"상품 ID '{item_id}' 스크래핑 중 예상치 못한 오류 발생: {e}")
        return {"item_id": item_id, "error": str(e)}

def run_price_updater(item_ids):
    """
    주어진 상품 ID 목록을 순회하며 가격을 업데이트합니다.
    Args:
        item_ids (list): 가격을 업데이트할 상품 ID 목록.
    """
    updated_products = []
    for i, item_id in enumerate(item_ids):
        # 짧은 딜레이를 주어 서버에 부담을 줄입니다.
        if i > 0:
            time.sleep(1)
        
        product_data = scrape_single_product_price(item_id)
        if product_data:
            updated_products.append(product_data)
    
    # 결과를 파일로 저장하는 로직을 추가할 수 있습니다.
    # 예시:
    # output_dir = "updated_price_data"
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)
    # output_file = os.path.join(output_dir, "updated_prices.json")
    # with open(output_file, "w", encoding="utf-8") as f:
    #     json.dump(updated_products, f, ensure_ascii=False, indent=4)
    # print(f"\n{len(updated_products)}개의 상품 가격 정보가 '{output_file}'에 저장되었습니다.")

if __name__ == "__main__":
    # 명령줄 인자를 확인합니다.
    if len(sys.argv) > 1:
        # 첫 번째 인자(파일 이름)를 제외하고 상품 ID를 인자로 사용합니다.
        product_ids = sys.argv[1:]
        print(f"명령줄 인자로 받은 상품 ID를 업데이트합니다: {product_ids}")
        run_price_updater(product_ids)
    else:
        print("업데이트할 상품 ID를 찾을 수 없습니다.")
