import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
import json
import sys
from io import StringIO
from firebase_uploader import (upload_all_products_to_firebase,upload_id_price_to_firebase,upload_other_info_to_firebase)

# 스크래핑 스크립트 파일들을 임포트합니다.
# scrape_all_products.py의 run_scraper를 run_all_scraper로 임포트
from emart_json import run_scraper as run_all_scraper
from emart_price_json import run_scraper as run_price_scraper
from emart_non_price_json import run_scraper as run_non_price_scraper

# run_image 엔드포인트를 위해 emart_image.py의 run_emart_image를 임포트
from emart_image import run_emart_image

from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

def scheduler_all():
    """ 전체 상품 스크래핑 및 업로드 작업 """
    try:
        print("===== 정기 작업 시작 (매일 11시): 모든 상품 스크래핑 =====")
        run_all_scraper()
        print("===== 스크래핑 완료. 파이어베이스 업로드를 시작합니다. =====")
        upload_all_products_to_firebase()
        print("===== 모든 정기 작업 완료 =====")
    except Exception as e:
        print(f"정기 작업(전체) 중 오류 발생: {e}")

def scheduler_price():
    """ 가격 정보 스크래핑 및 업로드 작업 """
    try:
        print("===== 정기 작업 시작 (매시 정각): 상품 가격 스크래핑 =====")
        run_price_scraper()
        print("===== 스크래핑 완료. 가격 파이어베이스 업로드를 시작합니다. =====")
        upload_id_price_to_firebase()
        print("===== 모든 정기 작업 완료 =====")
    except Exception as e:
        print(f"정기 작업(가격) 중 오류 발생: {e}")

# http://127.0.0.1:8000/docs
# http://127.0.0.1:8000/redoc
# uvicorn main1:app --reload --port 8420

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱이 시작될 때 실행할 코드
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduler_all, 'cron', hour=11, minute=0)
    scheduler.add_job(scheduler_price, 'cron', minute=22)
    scheduler.start()
    print("스케줄러가 시작되었습니다.")
    
    yield # 앱이 실행되는 동안 이 지점에서 대기합니다.
    
    # 앱이 종료될 때 실행할 코드
    scheduler.shutdown()
    print("스케줄러가 종료되었습니다.")

app = FastAPI(lifespan=lifespan)
scheduler = BackgroundScheduler()

@app.get("/")
async def root():
    return FileResponse("developer.html")

# @app.get("/chart")
# async def root():
#     return FileResponse("chart_viewer.html")

@app.post("/save_categories")
async def save_categories(request: Request):
    data = await request.json()
    with open("categories.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return {"status": "success"}


@app.post("/save_env")
async def save_env(request: Request):
    data = await request.json()
    lines = []
    # 기존 .env 파일 읽기
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    env_dict = {}
    for line in lines:
        if "=" in line:
            k, v = line.strip().split("=", 1)
            env_dict[k] = v
    # 값 업데이트
    env_dict["EMART_START_PAGE"] = str(data.get("EMART_START_PAGE", 1))
    env_dict["EMART_END_PAGE"] = str(data.get("EMART_END_PAGE", 30))
    # 파일로 저장
    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in env_dict.items():
            f.write(f"{k}={v}\n")
    return {"status": "success"}


@app.post("/run_json")
async def run_all_products():
    """모든 상품 정보를 스크랩하여 JSON으로 저장합니다."""
    try:
        run_all_scraper()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/run_price_json")
async def run_id_price():
    """ID와 가격 정보만 스크랩하여 JSON으로 저장합니다."""
    try:
        run_price_scraper()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/run_non_price_json")
async def run_other_info():
    """ID와 가격 외의 정보만 스크랩하여 JSON으로 저장합니다."""
    try:
        run_non_price_scraper()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/run_image")
async def run_image():
    """emart_image.py의 run_emart_image 함수를 실행합니다."""
    try:
        run_emart_image()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/run_firebase_all")
async def run_firebase_all():
    """모든 상품 정보를 Firestore에 업로드합니다."""
    try:
        upload_all_products_to_firebase()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/run_firebase_price")
async def run_firebase_price():
    """ID와 가격 정보를 Firestore에 업로드합니다."""
    try:
        upload_id_price_to_firebase()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/run_firebase_other")
async def run_firebase_other():
    """ID 외 정보를 Firestore에 업로드합니다."""
    try:
        upload_other_info_to_firebase()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/scheduler/on")
async def resume_scheduler():
    """일시정지된 스케줄러를 다시 시작합니다."""
    try:
        scheduler.resume()
        return {"status": "success", "message": "스케줄러가 다시 시작되었습니다."}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/scheduler/off")
async def pause_scheduler():
    """실행 중인 스케줄러를 일시정지합니다."""
    try:
        scheduler.pause()
        return {"status": "success", "message": "스케줄러가 일시정지되었습니다."}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main1:app", host="0.0.0.0", port=8420, reload=True)
