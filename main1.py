import os
import uvicorn
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse, FileResponse
import json
import sys
from io import StringIO

from emart_json import run_emart_json
from emart_image import run_emart_image

# http://127.0.0.1:8000/docs
# http://127.0.0.1:8000/redoc
# uvicorn main1:app --reload --port 8420

app = FastAPI()

@app.get("/")
async def root():
    return FileResponse("developer.html")

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
async def run_json():
    try:
        run_emart_json()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/run_image")
async def run_image():
    try:
        run_emart_image()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main1:app", host="0.0.0.0", port=8420, reload=True)
