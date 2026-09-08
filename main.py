from fastapi import FastAPI

# FastAPI 앱(서버) 생성
app = FastAPI()

# 첫 번째 경로: 접속하면 인사 메시지 반환
@app.get("/")
def read_root():
    return {"message": "AI 비서 서버가 켜졌습니다!"}