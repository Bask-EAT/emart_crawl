import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("repository/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)

def keep_only_id_and_price_history():
    initialize_firebase()
    db = firestore.client()
    collection_ref = db.collection("emart_price")
    docs = collection_ref.stream()

    batch = db.batch()
    count = 0
    for doc in docs:
        data = doc.to_dict()
        keep_fields = {
            "id": data.get("id"),
            "price_history": data.get("price_history", [])
        }
        doc_ref = collection_ref.document(doc.id)
        batch.set(doc_ref, keep_fields, merge=False)  # merge=False로 기존 필드 전체 덮어쓰기
        count += 1
        if count % 450 == 0:
            batch.commit()
            batch = db.batch()
            print(f"{count}개 문서 업데이트 완료...")

    if count % 450 != 0:
        batch.commit()
    print(f"총 {count}개 문서가 id와 price_history만 남도록 정리되었습니다.")

if __name__ == "__main__":
    keep_only_id_and_price_history()