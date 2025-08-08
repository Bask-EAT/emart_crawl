# firebase_uploader.py

import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import glob
import sys
from add_is_emb import check_and_add_is_emb 

def initialize_firebase():
    """
    Firebase Admin SDK를 초기화합니다.
    """
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate("repository/serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK가 성공적으로 초기화되었습니다.")
    except Exception as e:
        print(f"Firebase 초기화 중 오류가 발생했습니다: {e}")
        raise

def get_db():
    """
    Firestore 클라이언트 인스턴스를 반환합니다.
    """
    return firestore.client()

def update_price_history(db, product_id, price_info):
    """
    [수정됨] 가장 최근 가격과 동일하면 DB에 추가하지 않습니다.
    """
    price_ref = db.collection("emart_price").document(product_id)
    
    try:
        doc = price_ref.get()

        if doc.exists:
            price_history = doc.to_dict().get("price_history", [])
        else:
            price_history = []

        # --- [추가된 로직] ---
        # 가격 기록이 있고, 가장 마지막 기록의 가격이 현재 가격과 동일하면 함수를 종료합니다.
        if price_history:
            last_record = price_history[-1]
            if (last_record.get("original_price") == price_info.get("original_price") and
                last_record.get("selling_price") == price_info.get("selling_price")):
                return # 아무 작업도 하지 않고 종료

        # 가격이 다르거나 첫 기록일 경우, 새로운 정보를 리스트에 추가합니다.
        price_history.append(price_info)

        # 업데이트된 전체 리스트를 다시 저장합니다.
        price_update_data = {
            "id": product_id,
            "price_history": price_history
        }
        price_ref.set(price_update_data, merge=True)

    except Exception as e:
        print(f"상품 ID '{product_id}'의 가격 업데이트 중 오류 발생: {e}")

def upload_json_to_firestore(directory_path):
    """
    지정된 디렉토리의 모든 JSON 파일을 Firestore에 업로드합니다.
    """
    try:
        initialize_firebase()
    except Exception as e:
        return {"status": "error", "error": str(e)}

    db = get_db()

    # 신호기 1:모두 2:가격 3:상품
    beacon = 0
    if directory_path == "result_json":
        beacon = 1
    elif directory_path == "result_price_json":
        beacon = 2
    else :
        beacon = 3

    try:
        json_files = glob.glob(os.path.join(directory_path, "*.json"))
        if not json_files:
            print(f"경고: '{directory_path}' 폴더에 JSON 파일이 없습니다.")
            return {"status": "warning", "message": f"No JSON files found in '{directory_path}'"}

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                products = json.load(f)

            print(f"\n파일 '{json_file}'의 데이터를 Firestore에 업로드합니다.")

            product_batch = db.batch()
            total_doc_count = 0
            processed_product_ids = []

            for product in products:
                product_id = product.get("id")
                if not product_id:
                    continue
                
                processed_product_ids.append(product_id)

                # --- 1. emart_price 컬렉션 업데이트 (별도 함수 호출) ---
                if beacon in (1, 2):
                    price_info = {
                        "last_updated": product.get("last_updated"),
                        "original_price": product.get("original_price"),
                        "selling_price": product.get("selling_price")
                    }
                    update_price_history(db, product_id, price_info)
                
                # --- 2. emart_product 컬렉션 업데이트 로직 ---
                if beacon in (1, 3):
                    product_data = {
                        k: v for k, v in product.items() 
                        if k in ["id", "category", "image_url", "last_updated", "out_of_stock", "product_address", "product_name", "quantity"]
                    }
                    product_ref = db.collection("emart_product").document(product_id)
                    product_batch.set(product_ref, product_data, merge=True)

                total_doc_count += 1
                if total_doc_count > 0 and total_doc_count % 200 == 0:
                    product_batch.commit()
                    product_batch = db.batch()
                    print(f"  --> {total_doc_count}개 문서 처리 완료...")
            
            # 남은 상품 정보(product_batch) 커밋
            product_batch.commit()
            print(f"'{json_file}' 파일 업로드 완료. 총 {total_doc_count}개 문서가 처리되었습니다.")
            
            # --- 3. 갱신된 ID 목록으로 is_emb 확인 함수 호출 ---
            if beacon in (1,3) :
                print("\n>> 갱신된 상품 목록의 'is_emb' 필드를 확인합니다...")
                check_and_add_is_emb(processed_product_ids)

            try:
                os.remove(json_file)
                print(f"'{json_file}' 파일이 성공적으로 삭제되었습니다.")
            except OSError as e:
                print(f"파일 삭제 중 오류 발생: {json_file} - {e.strerror}")
            
        return {"status": "success", "message": "All files uploaded successfully."}

    except Exception as e:
        print(f"Firestore 업로드 중 오류가 발생했습니다: {e}")
        return {"status": "error", "error": str(e)}

def upload_all_products_to_firebase():
    """ 모든 상품 정보를 Firestore에 업로드하는 함수 """
    return upload_json_to_firestore("result_json")

def upload_id_price_to_firebase():
    """ ID와 가격 정보를 Firestore에 업로드하는 함수 """
    return upload_json_to_firestore("result_price_json")

def upload_other_info_to_firebase():
    """ ID 외 정보를 Firestore에 업로드하는 함수 """
    return upload_json_to_firestore("result_non_price_json")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "all":
            print("모든 상품 정보를 Firestore에 업로드합니다.")
            result = upload_all_products_to_firebase()
            print(f"업로드 결과: {result['status']}")
        elif command == "price":
            print("ID와 가격 정보를 Firestore에 업로드합니다.")
            result = upload_id_price_to_firebase()
            print(f"업로드 결과: {result['status']}")
        elif command == "other":
            print("ID 외 정보를 Firestore에 업로드합니다.")
            result = upload_other_info_to_firebase()
            print(f"업로드 결과: {result['status']}")
        else:
            print("유효하지 않은 명령입니다. 다음 중 하나를 사용하세요: all, price, other")
    else:
        print("사용법: python firebase_uploader.py [all|price|other]")
        print("예시: python firebase_uploader.py all")