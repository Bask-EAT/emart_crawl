# 1. 베이스 이미지 선택 (Python 3.9 공식 이미지 사용)
FROM python:3.12.9-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 호스트의 파일들을 컨테이너의 작업 디렉토리로 복사
# .dockerignore에 명시된 파일들은 제외됩니다.
COPY . .

# 4. 파이썬 의존성 설치
# --no-cache-dir 옵션은 불필요한 캐시를 남기지 않아 이미지 크기를 줄여줍니다.
RUN pip install --no-cache-dir -r requirements.txt

# 5. FastAPI 서버 실행 포트 노출
EXPOSE 8420

# 6. 컨테이너가 시작될 때 실행할 명령어
# uvicorn을 사용하여 main1.py의 app 객체를 실행합니다.
# --host 0.0.0.0 옵션은 컨테이너 외부에서 접근 가능하도록 합니다.
CMD ["uvicorn", "main1:app", "--host", "0.0.0.0", "--port", "8420"]