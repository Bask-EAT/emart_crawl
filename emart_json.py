# scrape_all_products.py

from dotenv import load_dotenv
import urllib.parse
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
            with open(filepath, "r", encoding="utf-8") as f:
                categories = json.load(f)
            print(f"'{filepath}' 파일에서 카테고리 목록을 성공적으로 로드했습니다.")
            return categories
        except json.JSONDecodeError as e:
            print(
                f"경고: '{filepath}' 파일 파싱 오류: {e}. 기본 카테고리 목록을 사용합니다."
            )
        except Exception as e:
            print(
                f"경고: '{filepath}' 파일 로드 중 예상치 못한 오류: {e}. 기본 카테고리 목록을 사용합니다."
            )
    else:
        print(
            f"경고: '{filepath}' 파일을 찾을 수 없습니다. 기본 카테고리 목록을 사용합니다."
        )

    return {
        "과일": "6000213114",
    }


def scrape_emart_category_page(html_content, category_name):
    """
    제공된 이마트몰 카테고리 HTML 콘텐츠에서 상품 정보를 스크랩합니다.
    Args:
        html_content (str): 이마트몰 카테고리 페이지의 HTML 콘텐츠입니다.
        category_name (str): 현재 스크래핑 중인 카테고리 이름입니다.
    Returns:
        list: 추출된 정보가 담긴 딕셔너리 목록입니다.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    products_data = []

    product_list_ul = soup.select_one("#ty_thmb_view > ul")
    product_items = []
    if product_list_ul:
        product_items = product_list_ul.find_all("li")

    for item in product_items:
        id = ""
        product_name = ""
        product_address = ""
        original_price = ""
        selling_price = ""
        image_url = ""
        quantity = ""
        out_of_stock = "N"

        brand_span = item.select_one("div.mnemitem_tit > span.mnemitem_goods_brand")
        title_span = item.select_one("div.mnemitem_tit > span.mnemitem_goods_tit")
        product_name_parts = []
        if brand_span:
            product_name_parts.append(f"[{brand_span.get_text(strip=True)}]")
        if title_span:
            product_name_parts.append(title_span.get_text(strip=True))
        product_name = " ".join(product_name_parts).strip()

        link_tag = item.select_one("div > a")
        if link_tag and "href" in link_tag.attrs:
            raw_url = link_tag["href"]
            if raw_url.startswith("//"):
                product_address = "https:" + raw_url
            elif raw_url.startswith("http"):
                product_address = raw_url
            else:
                product_address = "https://emart.ssg.com" + raw_url
        else:
            link_tag_alt = item.select_one("div.mnemitem_thmb_v2 > a")
            if link_tag_alt and "href" in link_tag_alt.attrs:
                raw_url_alt = link_tag_alt["href"]
                if raw_url_alt.startswith("//"):
                    product_address = "https:" + raw_url_alt
                elif raw_url_alt.startswith("http"):
                    product_address = raw_url_alt
                else:
                    product_address = "https://emart.ssg.com" + raw_url_alt

        if product_address:
            parsed_url = urllib.parse.urlparse(product_address)
            parsed_query = urllib.parse.parse_qs(parsed_url.query)
            item_id_list = parsed_query.get("itemId")
            if item_id_list:
                id = item_id_list[0]

        selling_price_tag = item.select_one(
            "div.mnemitem_pricewrap_v2 > div.mnemitem_price_row > div.new_price > em"
        )
        if not selling_price_tag:
            selling_price_tag = item.select_one(
                "div.mnemitem_pricewrap_v2 > div:nth-child(2) > div > em"
            )
        if selling_price_tag:
            selling_price = (
                selling_price_tag.get_text(strip=True)
                .replace("원", "")
                .replace(",", "")
            )

        original_price_tag = item.select_one(
            "div.mnemitem_pricewrap_v2 > div.mnemitem_price_row.ty_oldpr > div > del > em"
        )
        if not original_price_tag:
            original_price_tag = item.select_one(
                "div.mnemitem_pricewrap_v2 > div:nth-child(1) > div > em"
            )
        if original_price_tag:
            original_price = (
                original_price_tag.get_text(strip=True)
                .replace("원", "")
                .replace(",", "")
            )

        img_tag = item.select_one("div.mnemitem_thmb_v2 > a > div > img")
        if img_tag:
            raw_image_url = ""
            if "data-src" in img_tag.attrs:
                raw_image_url = img_tag["data-src"]
            elif "src" in img_tag.attrs:
                raw_image_url = img_tag["src"]
            if raw_image_url:
                if raw_image_url.startswith("//"):
                    image_url = "https:" + raw_image_url
                elif raw_image_url.startswith("http"):
                    image_url = raw_image_url
                else:
                    image_url = "https://emart.ssg.com" + raw_image_url

        quantity_tag = item.select_one("div.mnemitem_pricewrap_v2 > div.unit_price")
        if quantity_tag:
            quantity = quantity_tag.get_text(strip=True)

        sold_out_tag = item.select_one("div.mnemitem_thmb_v2 > div.mnemitem_soldout")
        if sold_out_tag:
            out_of_stock = "Y"

        products_data.append(
            {
                "id": id,
                "category": category_name,
                "product_name": product_name,
                "product_address": product_address,
                "original_price": original_price,
                "selling_price": selling_price,
                "image_url": image_url,
                "quantity": quantity,
                "out_of_stock": out_of_stock,
            }
        )

    return products_data

def run_scraper():
def extract_price_info(products_data):
    """
    상품 데이터 리스트에서 id, original_price, selling_price만 추출하여 반환합니다.
    """
    result = []
    for item in products_data:
        result.append({
            "id": item.get("id", ""),
            "original_price": item.get("original_price", ""),
            "selling_price": item.get("selling_price", "")
        })
    return result


def extract_non_price_info(products_data):
    """
    상품 데이터 리스트에서 original_price, selling_price를 제외한 나머지 정보만 추출하여 반환합니다.
    """
    result = []
    for item in products_data:
        filtered = {k: v for k, v in item.items() if k not in ["original_price", "selling_price"]}
        result.append(filtered)
    return result


def save_price_info_json(category_name, products_data, categories):
    """
    카테고리명과 상품 데이터 리스트, 전체 카테고리 dict를 받아 가격 정보만 담긴 json을 result_json_price 폴더에 저장합니다.
    """
    if not os.path.exists("result_json_price"):
        os.makedirs("result_json_price")
    price_only = extract_price_info(products_data)
    price_file = f"result_json_price/{category_name}_price_only.json"
    with open(price_file, "w", encoding="utf-8") as f:
        json.dump(price_only, f, ensure_ascii=False, indent=4)
    print(f"가격 정보만 저장: {price_file}")


def save_non_price_info_json(category_name, products_data, categories):
    """
    카테고리명과 상품 데이터 리스트, 전체 카테고리 dict를 받아 가격을 제외한 정보만 담긴 json을 result_json_non_price 폴더에 저장합니다.
    """
    if not os.path.exists("result_json_non_price"):
        os.makedirs("result_json_non_price")
    non_price = extract_non_price_info(products_data)
    non_price_file = f"result_json_non_price/{category_name}_non_price.json"
    with open(non_price_file, "w", encoding="utf-8") as f:
        json.dump(non_price, f, ensure_ascii=False, indent=4)
    print(f"가격 이외 정보만 저장: {non_price_file}")


def run_emart_json():
    load_dotenv(override=True)
    categories_to_scrape = load_categories_from_file()
    if not os.path.exists("result_json"):
        os.makedirs("result_json")
    start_page = int(os.environ.get("EMART_START_PAGE", 1))
    end_page = int(os.environ.get("EMART_END_PAGE", 5))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    for category_name, disp_ctg_id in categories_to_scrape.items():
        print(f"\n===== '{category_name}' 카테고리 스크래핑 시작 =====")
        all_scraped_products_for_category = []
        try:
            for page_num in range(start_page, end_page + 1):
                page_url = f"https://emart.ssg.com/disp/category.ssg?dispCtgId={disp_ctg_id}&page={page_num}"
                print(
                    f"--- {category_name} - {page_num} 페이지 스크래핑 시작: {page_url} ---"
                )
                response = requests.get(page_url, headers=headers)
                response.raise_for_status()
                html_content = response.text
                scraped_products_on_page = scrape_emart_category_page(
                    html_content, category_name
                )
                all_scraped_products_for_category.extend(scraped_products_on_page)
                print(
                    f"--- {category_name} - {page_num} 페이지 스크래핑 완료. {len(scraped_products_on_page)}개의 상품 추출. ---"
                )
                time.sleep(2)

            output_file = f"result_json/{category_name}_all_products.json"
            if not os.path.exists("result_json"):
                os.makedirs("result_json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    all_scraped_products_for_category, f, ensure_ascii=False, indent=4
                )
            print(
                f"\n'{category_name}' 카테고리 스크래핑이 완료되었습니다. 데이터가 '{output_file}' 파일에 성공적으로 저장되었습니다."
            )
            print(
                f"총 {len(all_scraped_products_for_category)}개의 '{category_name}' 상품이 스크랩되었습니다."
            )

        except requests.exceptions.RequestException as e:
            print(
                f"'{category_name}' 카테고리 웹사이트에 연결하는 중 오류가 발생했습니다: {e}"
            )
        except Exception as e:
            print(
                f"'{category_name}' 카테고리 스크래핑 중 예상치 못한 오류가 발생했습니다: {e}"
            )
    print("\n===== 모든 카테고리 스크래핑 프로세스 완료 =====")


if __name__ == "__main__":
    run_scraper()
