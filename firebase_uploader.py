# firebase_uploader.py

import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import glob
import sys
import requests
from dotenv import load_dotenv

def initialize_firebase():
    """ Firebase Admin SDK를 초기화합니다. """
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate("repository/serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK가 성공적으로 초기화되었습니다.")
    except Exception as e:
        print(f"Firebase 초기화 중 오류가 발생했습니다: {e}")
        raise

def get_db():
    """ Firestore 클라이언트 인스턴스를 반환합니다. """
    return firestore.client()

def update_price_history(db, product_id, out_of_stock, quantity, last_updated, price_info):
    """
    가격을 비교하여, 변경 시에만 price_history를 업데이트하고 상태를 반환합니다.
    - 'updated': 가격이 변경되어 history가 추가됨
    - 'skipped': 가격이 동일하여 history는 추가되지 않음 (상위 필드는 갱신됨)
    """
    price_ref = db.collection("emart_price").document(product_id)
    
    try:
        doc = price_ref.get()
        price_history = doc.to_dict().get("price_history", []) if doc.exists else []

        price_has_changed = True
        if price_history:
            last_record = price_history[-1]
            if (last_record.get("original_price") == price_info.get("original_price") and
                last_record.get("selling_price") == price_info.get("selling_price")):
                price_has_changed = False

        top_level_update_data = {
            "id": product_id, "out_of_stock": out_of_stock,
            "quantity": quantity, "last_updated": last_updated,
        }

        if price_has_changed:
            price_history.append(price_info)
            top_level_update_data["price_history"] = price_history
            price_ref.set(top_level_update_data, merge=True)
            return "updated"
        else:
            price_ref.set(top_level_update_data, merge=True)
            return "skipped"

    except Exception as e:
        print(f"상품 ID '{product_id}'의 가격 업데이트 중 오류 발생: {e}")
        return "error"

def upload_json_to_firestore(directory_path):
    """ 지정된 디렉토리의 모든 JSON 파일을 Firestore에 업로드합니다. """
    try:
        initialize_firebase()
    except Exception as e:
        return {"status": "error", "error": str(e)}

    db = get_db()
    beacon = 1 if directory_path == "result_json" else 2 if directory_path == "result_price_json" else 3

    try:
        json_files = glob.glob(os.path.join(directory_path, "*.json"))
        if not json_files:
            return {"status": "warning", "message": f"'{directory_path}' 폴더에 JSON 파일이 없습니다."}

        # --- [추가] 상세 카운터 초기화 ---
        price_updated_count = 0
        price_skipped_count = 0
        product_new_count = 0
        product_updated_count = 0
        product_skipped_count = 0

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                products = json.load(f)

            print(f"\n파일 '{json_file}'의 데이터를 Firestore에 업로드합니다.")

            for product in products:
                product_id = product.get("id")
                if not product_id:
                    continue

                # --- 가격 정보 처리 및 카운팅 ---
                if beacon in (1, 2):
                    price_info = {
                        "original_price": product.get("original_price"),
                        "selling_price": product.get("selling_price"),
                        "last_updated": product.get("last_updated"),
                    }
                    result = update_price_history(
                        db, product_id, product.get("out_of_stock"),
                        product.get("quantity"), product.get("last_updated"), price_info
                    )
                    if result == "updated":
                        price_updated_count += 1
                        print(f"가격 ID '{product_id}'가 업데이트 되었습니다 [{price_updated_count}]")
                    elif result == "skipped":
                        price_skipped_count += 1
                        print(f"가격 ID '{product_id}'가 패스 되었습니다 [{price_skipped_count}]")
                
                # --- 상품 정보 처리 및 카운팅 ---
                if beacon in (1, 3):
                    product_ref = db.collection("emart_product").document(product_id)
                    doc = product_ref.get()
                    
                    if doc.exists:
                        existing_data = doc.to_dict()
                        if (existing_data.get("product_name") != product.get("product_name") or
                            existing_data.get("image_url") != product.get("image_url")):
                            update_data = {
                                "product_name": product.get("product_name"),
                                "image_url": product.get("image_url"),
                                "last_updated": product.get("last_updated"),
                                "is_emb": "R"
                            }
                            product_ref.update(update_data)
                            product_updated_count += 1
                            print(f"상품 ID '{product_id}'가 업데이트 되었습니다 [{product_updated_count}]")
                        else:
                            product_ref.update({"last_updated": product.get("last_updated")})
                            product_skipped_count += 1
                            print(f"상품 ID '{product_id}'가 패스 되었습니다 [{product_skipped_count}]")
                    else:
                        product_data = {
                            k: v for k, v in product.items() 
                            if k in ["id", "category", "image_url", "last_updated", "product_address", "product_name"]
                        }
                        product_data["is_emb"] = "R"
                        product_ref.set(product_data)
                        product_new_count += 1
            
            try:
                os.remove(json_file)
            except OSError as e:
                print(f"파일 삭제 중 오류 발생: {e}")

        # --- [추가] 최종 결과 상세 출력 ---
        print("\n===== Firestore 업로드 최종 결과 =====")
        if beacon in (1, 2):
            print("--- 가격 정보 (emart_price) ---")
            print(f"  - 가격 변경되어 history 추가: {price_updated_count}개")
            print(f"  - 가격 동일하여 history 생략: {price_skipped_count}개")
        if beacon in (1, 3):
            print("--- 상품 정보 (emart_product) ---")
            print(f"  - 신규 추가된 상품: {product_new_count}개")
            print(f"  - 이름/이미지 변경된 상품: {product_updated_count}개")
            print(f"  - 변경 없어 시간만 갱신된 상품: {product_skipped_count}개")
        print("======================================")

        # 모든 파일 처리 후 임베딩 서버 호출
        print("\n>> 모든 업로드 작업 완료. 임베딩 서버에 시작 신호를 보냅니다...")
        load_dotenv()
        emb_server_url = os.environ.get("EMB_SERVER")
        if emb_server_url:
            try:
                response = requests.get(f"{emb_server_url}", timeout=10)
                response.raise_for_status()
                print(f"임베딩 서버에 성공적으로 신호를 보냈습니다. (상태 코드: {response.status_code})")
            except requests.exceptions.RequestException as e:
                print(f"오류: 임베딩 서버({emb_server_url})에 연결할 수 없습니다: {e}")
        else:
            print("경고: .env 파일에 EMB_SERVER 환경변수가 설정되지 않았습니다.")
            
        return {"status": "success", "message": "All files uploaded successfully."}

    except Exception as e:
        print(f"Firestore 업로드 중 오류가 발생했습니다: {e}")
        return {"status": "error", "error": str(e)}

def upload_all_products_to_firebase():
    return upload_json_to_firestore("result_json")

def upload_id_price_to_firebase():
    return upload_json_to_firestore("result_price_json")

def upload_other_info_to_firebase():
    return upload_json_to_firestore("result_non_price_json")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "all":
            result = upload_all_products_to_firebase()
        elif command == "price":
            result = upload_id_price_to_firebase()
        elif command == "other":
            result = upload_other_info_to_firebase()
        else:
            print("유효하지 않은 명령입니다. 다음 중 하나를 사용하세요: all, price, other")