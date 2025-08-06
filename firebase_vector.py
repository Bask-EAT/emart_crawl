import firebase_admin
from firebase_admin import credentials, firestore
import requests
import dotenv,os

dotenv.load_dotenv()

# 1. 서비스 계정 키 경로 입력
cred = credentials.Certificate("repository/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# 2. Firestore 클라이언트 생성
db = firestore.client()
server = str(os.environ.get("EMB_SERVER"))

rag_products_ref = db.collection("rag_products")
batch_size = 500
last_doc = None

i=0

while True:
    query = rag_products_ref.limit(batch_size)
    if last_doc:
        query = query.start_after(last_doc)
    docs = list(query.stream())
    if not docs:
        break
    for doc in docs:
        i+=1
        if i>10 :
            break
        data = doc.to_dict()
        if "embedding" not in data:
            # 'id' 필드를 기본으로, 'query' 필드가 있으면 그 값으로 대체
            string_for_vec = data.get("id", "")

            if not string_for_vec:
                print(f"문서 {doc.id}에 벡터화할 문자열이 없습니다.")
                continue
            try:
                response = requests.post(f"{server}/string2vec", json={"query": string_for_vec})
                response.raise_for_status()
                embedding_vector = response.json().get("results")
                if embedding_vector:
                    rag_products_ref.document(doc.id).update({"embedding": embedding_vector})
                    print(f"문서 {doc.id}에 embedding 추가 완료.")
                else:
                    print(f"문서 {doc.id}의 벡터 응답이 비어있음.")
            except Exception as e:
                print(f"문서 {doc.id} 벡터화 실패: {e}")
        else:
            print(f"문서 {doc.id}에는 이미 embedding이 존재합니다.")
    last_doc = docs[-1]
        

print("batch 처리 및 벡터화 완료.")