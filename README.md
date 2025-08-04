# 이마트몰 상품 정보 스크래퍼 및 관리 도구

이 프로젝트는 이마트몰의 상품 정보를 스크래핑하고 관리하기 위한 웹 기반의 도구입니다. Python의 FastAPI 프레임워크를 사용하여 백엔드 서버를 구축했으며, 웹 UI를 통해 스크래핑, JSON 파일 생성, 이미지 다운로드, 그리고 Firestore 데이터베이스 업로드를 간편하게 실행할 수 있습니다.

## 🌟 주요 기능

  * **카테고리 정보 관리**: `categories.json` 파일을 웹 UI를 통해 동적으로 업데이트하여 스크래핑할 카테고리를 설정할 수 있습니다.

  * **유연한 스크래핑 옵션**: 필요에 따라 상품 전체 정보, ID 및 가격 정보만, 또는 ID 외의 정보만 선택적으로 스크래핑할 수 있습니다.

  * **데이터 저장**: 스크래핑된 데이터는 `result_json`, `result_price_json`, `result_non_price_json` 디렉토리에 각각 JSON 파일로 저장됩니다.

  * **이미지 다운로드**: 스크래핑된 상품 정보에 포함된 이미지 URL을 기반으로 이미지를 로컬 디렉토리에 다운로드합니다.

  * **Firestore 업로드**: 로컬에 저장된 JSON 파일을 Google Firestore 데이터베이스에 업로드하여 데이터를 영구적으로 관리할 수 있습니다.

  * **페이지 범위 설정**: `.env` 파일을 통해 스크래핑할 페이지 범위를 설정할 수 있습니다.

## 🛠️ 기술 스택

  * **백엔드**: Python, FastAPI

  * **스크래핑**: `requests`, `BeautifulSoup4`

  * **데이터베이스**: Google Firestore (firebase-admin)

  * **환경 설정**: `python-dotenv`

  * **UI**: HTML, CSS, JavaScript (프론트엔드는 FastAPI가 제공하는 `developer.html` 파일로 구성)

## 📦 설치 및 실행 방법

### 1\. 환경 설정

1.  Python 3.8 이상이 설치되어 있는지 확인합니다.

2.  프로젝트의 모든 의존성 패키지를 설치합니다.

    ```
    pip install -r requirements.txt

    ```

3.  Firebase Firestore를 사용하려면 Google Cloud 프로젝트를 설정하고 서비스 계정 키를 발급받아야 합니다.

      * Google Cloud 콘솔에서 새 프로젝트를 생성합니다.

      * Firestore 데이터베이스를 생성하고, 보안 규칙을 설정합니다.

      * **서비스 계정** 메뉴에서 새 키를 생성하고 JSON 파일을 다운로드합니다.

      * `repository`라는 새 폴더를 만들고, 다운로드한 JSON 파일의 이름을 `serviceAccountKey.json`으로 변경하여 이 폴더에 저장합니다.

4.  `.env` 파일에 스크래핑할 페이지 범위를 설정합니다.

    ```
    EMART_START_PAGE=1
    EMART_END_PAGE=2

    ```

5.  `categories.json` 파일에 스크래핑할 이마트몰 카테고리의 이름과 ID를 추가합니다.

    ```
    {
        "과일": "6000213114",
        "김치_반찬_델리": "6000213299"
    }

    ```

### 2\. 프로젝트 실행

  * `main1.py` 파일을 `uvicorn`을 사용하여 실행합니다.

    ```
    uvicorn main1:app --reload

    ```

  * 터미널에 표시되는 로컬 서버 주소(예: `http://127.0.0.1:8000`)로 접속하여 웹 UI를 확인할 수 있습니다.

### 3\. 웹 UI 사용 방법

  * **카테고리 수정**: `categories.json`에 새로운 카테고리를 추가하거나 기존 카테고리를 수정할 수 있습니다.

  * **페이지 범위 설정**: `.env` 파일에 설정된 시작 및 종료 페이지를 웹 UI에서 변경할 수 있습니다.

  * **스크래핑 실행**: 버튼을 클릭하여 원하는 스크래핑 작업을 실행합니다.

      * `모든 상품 정보 스크래핑`: 모든 상품 정보를 스크래핑하여 `result_json`에 저장합니다.

      * `ID 및 가격 정보 스크래핑`: 상품 ID와 가격 정보만 스크래핑하여 `result_price_json`에 저장합니다.

      * `ID 외 정보 스크래핑`: 상품 ID와 가격 외의 정보만 스크래핑하여 `result_non_price_json`에 저장합니다.

      * `이미지 다운로드`: 스크래핑된 JSON 파일을 기반으로 이미지를 다운로드하여 `result_image`에 저장합니다.

  * **Firestore 업로드**:

      * `모든 상품 정보 Firestore에 업로드`: `result_json` 폴더의 데이터를 Firestore에 업로드합니다.

      * `ID 및 가격 정보 Firestore에 업로드`: `result_price_json` 폴더의 데이터를 Firestore에 업로드합니다.

      * `ID 외 정보 Firestore에 업로드`: `result_non_price_json` 폴더의 데이터를 Firestore에 업로드합니다.
