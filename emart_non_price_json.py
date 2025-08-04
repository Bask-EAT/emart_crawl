# scrape_other_info.py

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
    load_dotenv(override=True)
    categories_to_scrape = load_categories_from_file()
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

                # ID와 가격 정보를 제외한 나머지 정보만 추출
                other_info_data = []
                for product in scraped_products_on_page:
                    other_info_data.append(
                        {
                            "id": product.get("id"),
                            "category": product.get("category"),
                            "product_name": product.get("product_name"),
                            "product_address": product.get("product_address"),
                            "image_url": product.get("image_url"),
                            "quantity": product.get("quantity"),
                            "out_of_stock": product.get("out_of_stock"),
                        }
                    )
                all_scraped_products_for_category.extend(other_info_data)

                print(
                    f"--- {category_name} - {page_num} 페이지 스크래핑 완료. {len(other_info_data)}개의 상품 추출. ---"
                )
                time.sleep(2)

            output_file = f"result_non_price_json/{category_name}.json"
            if not os.path.exists("result_non_price_json"):
                os.makedirs("result_non_price_json")
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
