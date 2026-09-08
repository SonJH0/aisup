from fastapi import FastAPI
from pydantic import BaseModel

# FastAPI 앱(서버) 생성
app = FastAPI()

# 📋 공부 기록 데이터 설계도
class StudyRecord(BaseModel):
    date: str    # 날짜 (예: "2025-01-15")
    value: int   # 공부 시간(분) (예: 120)
    memo: str    # 메모 (예: "수학 공부")

# 💾 데이터를 임시로 저장할 리스트 (지금은 메모리에 저장)
records = []

# 첫 번째 경로: 접속하면 인사 메시지 반환
@app.get("/")
def read_root():
    return {"message": "AI 비서 서버가 켜졌습니다!"}

# 📥 [저장] 공부 기록 추가하기
@app.post("/records")
def create_record(record: StudyRecord):
    records.append(record)           # 리스트에 저장
    return {"message": "저장 완료!", "data": record}

# 📤 [조회] 저장된 모든 기록 불러오기
@app.get("/records")
def get_records():
    return {"total": len(records), "records": records}