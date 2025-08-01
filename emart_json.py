from dotenv import load_dotenv
# .env 파일 로드
load_dotenv()
from bs4 import BeautifulSoup
import json
import requests
import os
from datetime import datetime
import time

def load_categories_from_file(filepath="categories.json"):
    """
    지정된 JSON 파일에서 스크래핑할 카테고리 목록을 로드합니다.
    파일이 없거나 오류가 발생하면 기본 카테고리 목록을 반환합니다.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                categories = json.load(f)
            print(f"'{filepath}' 파일에서 카테고리 목록을 성공적으로 로드했습니다.")
            return categories
        except json.JSONDecodeError as e:
            print(f"경고: '{filepath}' 파일 파싱 오류: {e}. 기본 카테고리 목록을 사용합니다.")
        except Exception as e:
            print(f"경고: '{filepath}' 파일 로드 중 예상치 못한 오류: {e}. 기본 카테고리 목록을 사용합니다.")
    else:
        print(f"경고: '{filepath}' 파일을 찾을 수 없습니다. 기본 카테고리 목록을 사용합니다.")

    # 파일이 없거나 오류가 발생했을 때 사용할 기본 카테고리 목록
    return {
        "과일": "6000213114",
        # 여기에 다른 기본 카테고리들을 추가할 수 있습니다.
        # 예: "채소": "6000213115",
        # 예: "고기": "6000213116",
    }


def scrape_emart_category_page(html_content, category_name):
    """
    제공된 이마트몰 카테고리 HTML 콘텐츠에서 상품 정보를 스크랩합니다.

    Args:
        html_content (str): 이마트몰 카테고리 페이지의 HTML 콘텐츠입니다.
        category_name (str): 현재 스크래핑 중인 카테고리 이름입니다.

    Returns:
        list: 추출된 정보가 담긴 딕셔너리 목록입니다. 각 딕셔너리는 하나의 상품을 나타냅니다.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    products_data = []

    # 상품 목록의 부모 ul 태그를 찾습니다: #ty_thmb_view > ul
    product_list_ul = soup.select_one('#ty_thmb_view > ul')

    product_items = []
    if product_list_ul:
        # ul 태그 내의 모든 li 태그를 상품 항목으로 간주합니다.
        product_items = product_list_ul.find_all('li')
    else:
        print(f"경고: '{category_name}' 카테고리에서 '#ty_thmb_view > ul' 태그를 찾을 수 없습니다. 웹사이트 구조가 변경되었을 수 있습니다.")


    # --- 디버깅을 위한 추가 코드 시작 ---
    print(f"'{category_name}' 카테고리에서 찾은 상품 항목 수: {len(product_items)}개")
    if len(product_items) == 0:
        print(f"경고: '{category_name}' 카테고리에서 'li' 태그를 가진 상품 항목을 찾을 수 없습니다. 웹사이트 구조가 변경되었거나 콘텐츠가 동적으로 로드될 수 있습니다.")
    # --- 디버깅을 위한 추가 코드 끝 ---

    for item in product_items:
        product_name = ""
        product_address = ""
        original_price = "" # '원가'
        selling_price = "" # '판매가'
        image_url = ""
        quantity = ""
        out_of_stock = "N" # '품절 유무'를 'N'으로 초기화

        # 제품 이름 추출: 브랜드명과 제품명을 모두 결합
        brand_span = item.select_one('div.mnemitem_tit > span.mnemitem_goods_brand')
        title_span = item.select_one('div.mnemitem_tit > span.mnemitem_goods_tit')

        product_name_parts = []
        if brand_span:
            product_name_parts.append(f"[{brand_span.get_text(strip=True)}]")
        if title_span:
            product_name_parts.append(title_span.get_text(strip=True))
        product_name = " ".join(product_name_parts).strip()


        # 제품 주소(URL) 추출 및 중복 URL 접두사 문제 해결
        link_tag = item.select_one('div > a') # 가장 가까운 상품 링크
        if link_tag and 'href' in link_tag.attrs:
            raw_url = link_tag['href']
            if raw_url.startswith('//'):
                product_address = "https:" + raw_url
            elif raw_url.startswith('http'): # 이미 완전한 URL인 경우
                product_address = raw_url
            else: # 상대 경로인 경우
                product_address = "https://emart.ssg.com" + raw_url
        else:
            # 다른 경로로 a 태그를 찾아봅니다. (예: 이미지 링크)
            link_tag_alt = item.select_one('div.mnemitem_thmb_v2 > a')
            if link_tag_alt and 'href' in link_tag_alt.attrs:
                raw_url_alt = link_tag_alt['href']
                if raw_url_alt.startswith('//'):
                    product_address = "https:" + raw_url_alt
                elif raw_url_alt.startswith('http'):
                    product_address = raw_url_alt
                else:
                    product_address = "https://emart.ssg.com" + raw_url_alt


        # 판매가 추출 (Selling Price)
        # 1순위: 할인된 가격 (new_price)
        selling_price_tag = item.select_one('div.mnemitem_pricewrap_v2 > div.mnemitem_price_row > div.new_price > em')
        if not selling_price_tag:
            # 2순위: 일반적인 현재 표시 가격 (mnemitem_pricewrap_v2 > div:nth-child(2) > div > em)
            selling_price_tag = item.select_one('div.mnemitem_pricewrap_v2 > div:nth-child(2) > div > em')

        if selling_price_tag:
            selling_price = selling_price_tag.get_text(strip=True).replace('원', '').replace(',', '')


        # 원가 추출 (Original Price)
        # 1순위: 취소선이 있는 정상가격 (ty_oldpr > del)
        original_price_tag = item.select_one('div.mnemitem_pricewrap_v2 > div.mnemitem_price_row.ty_oldpr > div > del > em')
        if not original_price_tag:
            # 2순위: 첫 번째 가격 정보 (최고판매가 등)
            original_price_tag = item.select_one('div.mnemitem_pricewrap_v2 > div:nth-child(1) > div > em')

        if original_price_tag:
            original_price = original_price_tag.get_text(strip=True).replace('원', '').replace(',', '')


        # 이미지 주소 추출 및 중복 URL 접두사 문제 해결
        img_tag = item.select_one('div.mnemitem_thmb_v2 > a > div > img')
        if img_tag:
            raw_image_url = ""
            if 'data-src' in img_tag.attrs:
                raw_image_url = img_tag['data-src']
            elif 'src' in img_tag.attrs:
                raw_image_url = img_tag['src']

            if raw_image_url:
                if raw_image_url.startswith('//'):
                    image_url = "https:" + raw_image_url
                elif raw_image_url.startswith('http'): # 이미 완전한 URL인 경우
                    image_url = raw_image_url
                else: # 상대 경로인 경우 (이미지에는 드물지만 대비)
                    image_url = "https://emart.ssg.com" + raw_image_url

        # 수량 추출
        quantity_tag = item.select_one('div.mnemitem_pricewrap_v2 > div.unit_price')
        if quantity_tag:
            quantity = quantity_tag.get_text(strip=True)

        # 품절 유무 판단
        # 'div.mnemitem_soldout' 태그가 존재하면 품절
        sold_out_tag = item.select_one('div.mnemitem_thmb_v2 > div.mnemitem_soldout')
        if sold_out_tag:
            out_of_stock = "Y"


        products_data.append({
            "category": category_name, # 인자로 받은 카테고리 이름 사용
            "product_name": product_name,
            "product_address": product_address,
            "original_price": original_price,
            "selling_price": selling_price,
            "image_url": image_url,
            "quantity": quantity,
            "out_of_stock": out_of_stock
        })

    return products_data


def run_emart_json():
    from dotenv import load_dotenv
    load_dotenv(override=True)

    categories_to_scrape = load_categories_from_file()
    start_page = int(os.environ.get("EMART_START_PAGE", 1))
    end_page = int(os.environ.get("EMART_END_PAGE", 5))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for category_name, disp_ctg_id in categories_to_scrape.items():
        
        print(f"\n===== '{category_name}' 카테고리 스크래핑 시작 =====")
        all_scraped_products_for_category = []

        try:
            for page_num in range(start_page, end_page + 1):
                page_url = f"https://emart.ssg.com/disp/category.ssg?dispCtgId={disp_ctg_id}&page={page_num}"
                print(f"--- {category_name} - {page_num} 페이지 스크래핑 시작: {page_url} ---")
                response = requests.get(page_url, headers=headers)
                response.raise_for_status()
                html_content = response.text
                scraped_products_on_page = scrape_emart_category_page(html_content, category_name)
                all_scraped_products_for_category.extend(scraped_products_on_page)
                print(f"--- {category_name} - {page_num} 페이지 스크래핑 완료. {len(scraped_products_on_page)}개의 상품 추출. ---")
                time.sleep(2)

            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"result_json/{current_time}_{category_name}_emart_products.json"

            if not os.path.exists("result_json"):
                os.makedirs("result_json")
                print("result_json 디렉토리를 생성했습니다.")

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_scraped_products_for_category, f, ensure_ascii=False, indent=4)

            print(f"\n'{category_name}' 카테고리 스크래핑이 완료되었습니다. 데이터가 '{output_file}' 파일에 성공적으로 저장되었습니다.")
            print(f"총 {len(all_scraped_products_for_category)}개의 '{category_name}' 상품이 스크랩되었습니다.")

        except requests.exceptions.RequestException as e:
            print(f"'{category_name}' 카테고리 웹사이트에 연결하는 중 오류가 발생했습니다: {e}")

        except Exception as e:
            print(f"'{category_name}' 카테고리 스크래핑 중 예상치 못한 오류가 발생했습니다: {e}")

    print("\n===== 모든 카테고리 스크래핑 프로세스 완료 =====")

if __name__ == "__main__":
    run_emart_json()
