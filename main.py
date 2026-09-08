from fastapi import FastAPI
from pydantic import BaseModel
import json
import os

DATA_FILE = "data.json"  # 데이터를 저장할 파일 이름


# 📂 파일에서 데이터 불러오기
def load_data():
    if os.path.exists(DATA_FILE):  # 파일이 있으면
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)  # 읽어서 반환
    return []  # 없으면 빈 리스트


# 💾 데이터를 파일에 저장하기
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# FastAPI 앱(서버) 생성
app = FastAPI()


# 📋 공부 기록 데이터 설계도
class StudyRecord(BaseModel):
    date: str    # 날짜 (예: "2025-01-15")
    value: int   # 공부 시간(분) (예: 120)
    memo: str    # 메모 (예: "수학 공부")


# 💾 데이터를 임시로 저장할 리스트 (지금은 파일에서 불러옴)
records = load_data()


# 첫 번째 경로: 접속하면 인사 메시지 반환
@app.get("/")
def read_root():
    return {"message": "AI 비서 서버가 켜졌습니다!"}


# 📥 [저장] 공부 기록 추가하기
@app.post("/records")
def create_record(record: StudyRecord):
    records.append(record.dict())  # .dict()로 변환해서 추가
    save_data(records)             # 파일에 저장
    return {"message": "저장 완료!", "data": record}


# 📤 [조회] 저장된 모든 기록 불러오기
@app.get("/records")
def get_records():
    return {"total": len(records), "records": records}