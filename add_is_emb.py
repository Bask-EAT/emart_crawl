import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase():
    """
    Firebase Admin SDK를 초기화합니다.
    이미 초기화되어 있다면 다시 초기화하지 않습니다.
    """
    if not firebase_admin._apps:
        cred = credentials.Certificate("repository/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK가 성공적으로 초기화되었습니다.")

def add_is_emb_to_all_emart_product():
    """
    'emart_product' 컬렉션의 모든 문서에 'is_emb' 필드를 추가(업데이트)합니다.
    단, 'is_emb' 필드가 이미 존재하는 문서는 건너뜁니다.
    """
    initialize_firebase()
    db = firestore.client()
    collection_ref = db.collection("emart_product")
    docs = collection_ref.stream()

    batch = db.batch()
    count = 0
    skipped_count = 0

    for doc in docs:
        doc_data = doc.to_dict()
        # 'is_emb' 필드가 이미 존재하는지 확인합니다.
        if "is_emb" in doc_data:
            skipped_count += 1
            print(f"문서 '{doc.id}'에 'is_emb' 필드가 이미 존재하여 건너뜁니다.")
            continue # 필드가 존재하면 다음 문서로 넘어갑니다.

        doc_ref = collection_ref.document(doc.id)
        batch.update(doc_ref, {"is_emb": "R"})
        count += 1
        if count % 450 == 0:
            batch.commit()
            batch = db.batch()
            print(f"{count}개 문서 업데이트 완료...")

    # 남은 문서 커밋
    if count % 450 != 0: # 또는 단순히 `if count > 0:`으로 변경 가능
        batch.commit()
    print(f"총 {count}개 문서에 'is_emb' 필드가 추가(업데이트)되었습니다.")
    print(f"총 {skipped_count}개 문서는 'is_emb' 필드가 이미 존재하여 건너뛰었습니다.")

if __name__ == "__main__":
    add_is_emb_to_all_emart_product()
