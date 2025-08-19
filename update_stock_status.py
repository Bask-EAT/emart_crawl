# 오래된 상품 재고 없음으로 변경

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

def initialize_firebase():
    """ Firebase Admin SDK를 초기화합니다. """
    try:
        if not firebase_admin._apps:
            # 서비스 계정 키 파일 경로를 지정합니다.
            cred = credentials.Certificate("repository/serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK가 성공적으로 초기화되었습니다.")
    except Exception as e:
        print(f"Firebase 초기화 중 오류가 발생했습니다: {e}")
        raise

def update_old_products_to_out_of_stock():
    """
    'emart_product' 컬렉션에서 마지막 업데이트가 일주일 이상 된 상품의
    'out_of_stock' 상태를 'Y'로 변경합니다.
    """
    try:
        initialize_firebase()
        db = firestore.client()

        # 1. 일주일 전의 날짜와 시간을 계산합니다.
        one_week_ago = datetime.now() - timedelta(weeks=1)
        print(f"기준 시간: {one_week_ago.isoformat()} 이전의 데이터를 확인합니다.")

        # 2. 'emart_product' 컬렉션의 모든 문서를 가져옵니다.
        products_ref = db.collection("emart_price")
        docs = products_ref.stream()

        batch = db.batch()
        update_count = 0
        total_count = 0

        print("상품 데이터 확인을 시작합니다...")

        for doc in docs:
            total_count += 1
            product_data = doc.to_dict()
            
            # 3. 문서에 'last_updated' 필드가 있는지 확인합니다.
            last_updated_str = product_data.get("last_updated")
            if not last_updated_str:
                continue # 필드가 없으면 건너뜁니다.
            
            try:
                # 4. 업데이트 시간을 datetime 객체로 변환합니다.
                last_updated_time = datetime.fromisoformat(last_updated_str)

                # 5. 업데이트 시간이 일주일보다 오래되었는지 비교합니다.
                if last_updated_time < one_week_ago:
                    # 조건에 맞으면, 업데이트할 내용을 배치(batch)에 추가합니다.
                    doc_ref = products_ref.document(doc.id)
                    batch.update(doc_ref, {"out_of_stock": "Y"})
                    update_count += 1
                    print(f"  - ID: {doc.id} 상태 변경 예정 (마지막 업데이트: {last_updated_str})")

                    # 6. 배치에 450개 작업이 쌓이면, 한 번에 커밋하여 서버 부담을 줄입니다.
                    if update_count % 450 == 0:
                        batch.commit()
                        batch = db.batch()
                        print(f"--- 중간 커밋: {update_count}개 문서 업데이트 완료 ---")

            except (ValueError, TypeError):
                # 날짜 형식이 잘못된 경우를 대비한 예외 처리
                print(f"  - 경고: ID {doc.id}의 'last_updated' 필드 형식이 잘못되었습니다: {last_updated_str}")
                continue
        
        # 7. 남아있는 모든 업데이트 작업을 최종 커밋합니다.
        if update_count > 0 and update_count % 450 != 0:
            batch.commit()

        print("\n===== 작업 완료 =====")
        print(f"총 {total_count}개의 상품을 확인했습니다.")
        print(f"총 {update_count}개 상품의 재고 상태를 'Y'로 변경했습니다.")

    except Exception as e:
        print(f"작업 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    update_old_products_to_out_of_stock()