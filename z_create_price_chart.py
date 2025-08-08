import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import plotly.graph_objects as go
import os

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

def plot_price_history_to_html(product_id):
    """
    특정 상품 ID의 가격 변동 이력을 인터랙티브 HTML 차트로 저장합니다.
    """
    try:
        initialize_firebase()
        db = firestore.client()

        # 1. Firestore에서 데이터 가져오기
        price_ref = db.collection("emart_price").document(product_id)
        doc = price_ref.get()

        if not doc.exists:
            print(f"상품 ID '{product_id}'에 대한 데이터가 없습니다.")
            return

        price_history = doc.to_dict().get("price_history", [])

        if not price_history:
            print(f"상품 ID '{product_id}'에 가격 기록이 없습니다.")
            return

        # 2. 데이터 정제하기
        dates = []
        selling_prices = []
        original_prices = []
        for record in price_history:
            dates.append(datetime.fromisoformat(record.get("last_updated")))
            selling_prices.append(int(record.get("selling_price", 0)))
            original_prices.append(int(record.get("original_price", 0)))

        # 3. 인터랙티브 차트 그리기 (Plotly 사용)
        fig = go.Figure()

        # 판매가 라인 추가
        fig.add_trace(go.Scatter(
            x=dates,
            y=selling_prices,
            mode='lines+markers',
            name='판매가',
            line=dict(color='royalblue', width=2),
            marker=dict(size=5)
        ))
        
        # 원가 라인 추가
        fig.add_trace(go.Scatter(
            x=dates,
            y=original_prices,
            mode='lines',
            name='원가',
            line=dict(color='gray', width=1, dash='dash')
        ))

        # 차트 레이아웃 설정
        fig.update_layout(
            title=dict(text=f"<b>상품 ID: {product_id} 가격 변동 차트</b>", x=0.5),
            xaxis_title="날짜",
            yaxis_title="가격 (원)",
            legend_title="범례",
            font=dict(family="Malgun Gothic, AppleGothic, sans-serif")
        )

        # 4. HTML 파일로 저장
        output_dir = "result_chart"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"'{output_dir}' 폴더를 생성했습니다.")

        output_filename = os.path.join(output_dir, f"{product_id}_price_chart.html")
        
        fig.write_html(output_filename)
        
        print(f"인터랙티브 차트가 '{output_filename}' 파일로 성공적으로 저장되었습니다.")

    except Exception as e:
        print(f"차트 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    # 여기에 분석하고 싶은 실제 상품의 ID를 입력하여 테스트할 수 있습니다.
    target_product_id = "0000006810933" # 예시 ID
    plot_price_history_to_html(target_product_id)