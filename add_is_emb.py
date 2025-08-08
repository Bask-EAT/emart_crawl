# z_add_is_emb.py

import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase():
    """ Firebase Admin SDK를 초기화합니다. """
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate("repository/serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK가 성공적으로 초기화되었습니다.")
        except Exception as e:
            print(f"Firebase 초기화 중 오류 발생: {e}")
            raise

def check_and_add_is_emb(product_ids):
    """
    주어진 ID 목록을 확인하여 'is_emb' 상태를 관리합니다. (최종 최적화 버전)
    - 'emart_vector'에 문서가 있으면 'is_emb'를 'D'(Done)로 설정합니다.
    - 없으면, 'emart_product'에 'is_emb' 필드가 없을 경우에만 'R'(Ready)로 설정합니다.
    """
    if not product_ids:
        print("'is_emb' 상태를 확인할 상품 ID가 없습니다.")
        return

    initialize_firebase()
    db = firestore.client()
    product_collection = db.collection("emart_product")
    vector_collection = db.collection("emart_vector")

    batch = db.batch()
    updated_to_D_count = 0
    updated_to_R_count = 0
    skipped_count = 0

    for product_id in product_ids:
        product_doc_ref = product_collection.document(product_id)
        vector_doc_ref = vector_collection.document(product_id)
        
        try:
            # 1. 'emart_vector'에 문서가 있는지 비용 효율적으로 확인
            vector_doc = vector_doc_ref.get(field_paths=[])
            
            if vector_doc.exists:
                # 2. 있으면 'is_emb'를 'D'로 업데이트 (이미 'D'라도 덮어쓰지만, 이 경우는 상태 전이를 위해 허용)
                batch.update(product_doc_ref, {"is_emb": "D"})
                updated_to_D_count += 1
            else:
                # 3. 없으면, 'emart_product'의 현재 상태를 비용 효율적으로 확인
                product_doc = product_doc_ref.get(field_paths={"is_emb"})
                
                # 4. 'is_emb' 필드가 이미 존재하면 불필요한 쓰기를 막기 위해 건너뜀
                if product_doc.exists and "is_emb" in product_doc.to_dict():
                    skipped_count += 1
                    continue
                
                # 5. 'is_emb' 필드가 없는 신규 상품에만 'R'로 추가
                batch.update(product_doc_ref, {"is_emb": "R"})
                updated_to_R_count += 1

            if (updated_to_D_count + updated_to_R_count) > 0 and (updated_to_D_count + updated_to_R_count) % 450 == 0:
                batch.commit()
                batch = db.batch()

        except Exception as e:
            print(f"문서 '{product_id}' 처리 중 오류 발생: {e}")

    # 남은 작업을 커밋
    if (updated_to_D_count + updated_to_R_count) > 0 and (updated_to_D_count + updated_to_R_count) % 450 != 0:
        batch.commit()
    
    print(f"총 {updated_to_D_count}개 문서의 'is_emb'를 'D'로 업데이트했습니다.")
    print(f"총 {updated_to_R_count}개 문서에 'is_emb' 필드를 'R'로 추가했습니다.")
    print(f"총 {skipped_count}개 문서는 이미 'is_emb' 필드가 있어 건너뛰었습니다.")

def add_is_emb_to_all_emart_product():
    """ [기존 함수] 'emart_product' 컬렉션의 모든 문서를 스캔합니다. """
    initialize_firebase()
    db = firestore.client()
    collection_ref = db.collection("emart_product")
    docs = collection_ref.stream()

    batch = db.batch()
    count = 0
    skipped_count = 0

    for doc in docs:
        doc_data = doc.to_dict()
        if "is_emb" in doc_data:
            skipped_count += 1
            continue

        doc_ref = collection_ref.document(doc.id)
        batch.update(doc_ref, {"is_emb": "R"})
        count += 1
        if count % 450 == 0:
            batch.commit()
            batch = db.batch()
            print(f"{count}개 문서 업데이트 완료...")

    if count > 0 and count % 450 != 0:
        batch.commit()
    print(f"총 {count}개 문서에 'is_emb' 필드가 추가(업데이트)되었습니다.")
    print(f"총 {skipped_count}개 문서는 'is_emb' 필드가 이미 존재하여 건너뛰었습니다.")

if __name__ == "__main__":
    add_is_emb_to_all_emart_product()