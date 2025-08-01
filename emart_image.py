import json
import requests
import os
import glob
import time # 요청 사이에 딜레이를 주기 위해 time 모듈 임포트
from dotenv import load_dotenv

def find_all_json_files_in_directory(directory, pattern):
    """
    주어진 디렉토리에서 특정 패턴과 일치하는 모든 JSON 파일을 찾습니다.

    Args:
        directory (str): 파일을 검색할 디렉토리 경로입니다.
        pattern (str): 검색할 파일명 패턴 (예: "*_emart_products.json").

    Returns:
        list: 찾은 모든 파일의 전체 경로 목록입니다.
    """
    return glob.glob(os.path.join(directory, pattern))

def download_images_from_json(json_filepath, output_base_dir="result_image"):
    """
    JSON 파일에 지정된 URL에서 이미지를 다운로드합니다.
    파일명을 정리하고, 중복 파일을 파일 크기로 검사하여 처리합니다.
    카테고리별로 하위 디렉토리를 생성하여 저장합니다.

    Args:
        json_filepath (str): 상품 데이터가 포함된 JSON 파일의 경로입니다.
        output_base_dir (str): 이미지를 저장할 기본 디렉토리 (예: "result_image").
                               실제 이미지는 이 디렉토리 아래의 카테고리별 폴더에 저장됩니다.
    """
    if not os.path.exists(json_filepath):
        print(f"오류: JSON 파일 '{json_filepath}'을(를) 찾을 수 없습니다.")
        return

    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            products_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"오류: JSON 파일 '{json_filepath}'을(를) 파싱하는 데 실패했습니다: {e}")
        return

    if not products_data:
        print(f"경고: '{json_filepath}' 파일에 상품 데이터가 없습니다. 건너뜁니다.")
        return

    # JSON 파일의 첫 번째 상품에서 카테고리 이름을 가져옵니다.
    # 모든 상품이 동일한 카테고리에 속한다고 가정합니다.
    category_name = products_data[0].get("category", "unknown_category")
    output_dir = os.path.join(output_base_dir, category_name)

    # 이미지 저장 디렉토리가 없으면 생성합니다.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"'{output_dir}' 디렉토리를 생성했습니다.")

    print(f"'{json_filepath}' 파일에서 총 {len(products_data)}개의 '{category_name}' 상품 이미지를 다운로드합니다.")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for i, product in enumerate(products_data):
        image_url = product.get("image_url")
        product_name = product.get("product_name", "알 수 없는 제품")

        if not image_url:
            print(f"[{i+1}/{len(products_data)}] '{product_name}' 제품의 이미지 주소가 없습니다. 건너뜁니다.")
            continue

        try:
            # 1. 파일명 추출 및 수정
            filename = os.path.basename(image_url)
            # "_i1_290" 또는 "_i1_580" 제거
            if "_i1_290" in filename:
                filename = filename.replace("_i1_290", "")
            elif "_i1_580" in filename:
                filename = filename.replace("_i1_580", "")

            # 쿼리 스트링이나 해시 제거 (예: ?v=123, #anchor)
            if '?' in filename:
                filename = filename.split('?')[0]
            if '#' in filename:
                filename = filename.split('#')[0]

            local_filepath = os.path.join(output_dir, filename)

            # 2. 이미지 다운로드 (헤더만 요청하여 크기 확인)
            # HEAD 요청으로 파일 크기를 미리 가져옵니다.
            response_head = requests.head(image_url, headers=headers, timeout=10)
            response_head.raise_for_status()
            expected_size = int(response_head.headers.get('content-length', 0))

            # 3. 기존 파일 존재 여부 및 크기 비교
            if os.path.exists(local_filepath):
                current_file_size = os.path.getsize(local_filepath)
                if current_file_size == expected_size and expected_size > 0:
                    print(f"[{i+1}/{len(products_data)}] '{product_name}' 이미지 '{filename}' (동일 크기) - 건너뜁니다.")
                    continue
                else:
                    print(f"[{i+1}/{len(products_data)}] '{product_name}' 이미지 '{filename}' (크기 다름 또는 0) - 덮어씁니다.")
            else:
                print(f"[{i+1}/{len(products_data)}] '{product_name}' 이미지 '{filename}' - 다운로드합니다.")

            # 4. 파일 다운로드 및 저장
            response_get = requests.get(image_url, headers=headers, timeout=10)
            response_get.raise_for_status()

            with open(local_filepath, 'wb') as f:
                f.write(response_get.content)

        except requests.exceptions.RequestException as e:
            print(f"[{i+1}/{len(products_data)}] '{product_name}' 이미지 다운로드 중 오류 발생 ({image_url}): {e}")
        except Exception as e:
            print(f"[{i+1}/{len(products_data)}] '{product_name}' 이미지 처리 중 예상치 못한 오류 발생 ({image_url}): {e}")

        # 각 이미지 다운로드 사이에 짧은 딜레이를 줍니다.
        time.sleep(0.1) # 0.1초 딜레이

    print(f"\n'{category_name}' 카테고리의 모든 이미지 다운로드 시도를 완료했습니다.")


def run_emart_image():

    load_dotenv(override=True)
    json_input_dir = "result_json"
    json_pattern = "*.json"
    if not os.path.exists(json_input_dir):
        print(f"오류: JSON 파일을 읽을 폴더 '{json_input_dir}'을(를) 찾을 수 없습니다.")
        print("스크래핑 코드를 실행하여 JSON 파일을 먼저 생성하거나, 해당 폴더를 생성해주세요.")
        return

    json_files = find_all_json_files_in_directory(json_input_dir, json_pattern)

    if not json_files:
        print(f"오류: '{json_input_dir}' 폴더에서 '{json_pattern}' 패턴과 일치하는 JSON 파일을 찾을 수 없습니다.")
        print("스크래핑 코드를 실행하여 JSON 파일을 먼저 생성해주세요.")
        return

    print(f"'{json_input_dir}' 폴더에서 총 {len(json_files)}개의 JSON 파일을 찾았습니다.")

    for json_file in json_files:
        download_images_from_json(json_file)

    print("\n===== 모든 JSON 파일의 이미지 다운로드 프로세스 완료 =====")

if __name__ == "__main__":
    run_emart_image()
