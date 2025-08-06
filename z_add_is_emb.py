import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("repository/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)

def add_is_emb_to_all_emart_product():
    initialize_firebase()
    db = firestore.client()
    collection_ref = db.collection("emart_product")
    docs = collection_ref.stream()

    batch = db.batch()
    count = 0
    for doc in docs:
        doc_ref = collection_ref.document(doc.id)
        batch.update(doc_ref, {"is_emb": "R"})
        count += 1
        if count % 450 == 0:
            batch.commit()
            batch = db.batch()
            print(f"{count}개 문서 업데이트 완료...")

    # 남은 문서 커밋
    if count % 450 != 0:
        batch.commit()
    print(f"총 {count}개 문서에 'is_emb' 필드가 추가(업데이트)되었습니다.")

if __name__ == "__main__":
    add_is_emb_to_all_emart_product()