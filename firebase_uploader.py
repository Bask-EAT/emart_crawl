# firebase_uploader.py

import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import glob
import sys # sys 모듈을 임포트하여 명령줄 인자를 처리합니다.

def initialize_firebase():
    """
    Firebase Admin SDK를 초기화합니다.
    서비스 계정 키 파일이 필요하며, 파일 이름을 'serviceAccountKey.json'으로 가정합니다.
    """
    try:
        if not firebase_admin._apps:
            # 서비스 계정 키 파일 경로를 지정합니다.
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

def upload_json_to_firestore(directory_path):
    """
    지정된 디렉토리의 모든 JSON 파일을 Firestore에 업로드합니다.
    
    Args:
        directory_path (str): JSON 파일이 있는 로컬 디렉토리 경로.
    """
    # Firebase 초기화
    try:
        initialize_firebase()
    except Exception as e:
        return {"status": "error", "error": str(e)}

    db = get_db()

    try:
        # 지정된 디렉토리의 모든 JSON 파일을 찾습니다.
        json_files = glob.glob(os.path.join(directory_path, "*.json"))
        if not json_files:
            print(f"경고: '{directory_path}' 폴더에 JSON 파일이 없습니다.")
            return {"status": "warning", "message": f"No JSON files found in '{directory_path}'"}

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                products = json.load(f)

            # JSON 파일명에서 카테고리 이름을 추출하여 컬렉션 이름을 동적으로 생성
            file_name = os.path.basename(json_file).split(".")[0]

            print(f"\n파일 '{json_file}'의 데이터를 Firestore 컬렉션 '{file_name}'에 업로드합니다.")

            batch = db.batch()
            doc_count = 0
            for product in products:
                # 'id' 필드를 사용하여 문서 ID를 지정
                product_id = product.get("id")
                if product_id:
                    doc_ref = db.collection(file_name).document(product_id)
                    # merge=True를 사용하여 기존 문서가 있으면 필드를 업데이트합니다.
                    batch.set(doc_ref, product, merge=True)
                    doc_count += 1
                
                    # Firestore 쓰기 배치 제한(500)을 고려하여 450개마다 커밋
                    if doc_count % 450 == 0:
                        batch.commit()
                        batch = db.batch()
                        print(f"  --> {doc_count}개 문서 커밋 완료...")

            # 남은 문서 커밋
            batch.commit()
            print(f"'{json_file}' 파일 업로드 완료. 총 {doc_count}개의 문서가 업로드되었습니다.")

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
    # 명령줄 인자를 확인하고, 인자에 따라 다른 함수를 호출합니다.
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
