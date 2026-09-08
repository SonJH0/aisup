from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv    # .env 파일 읽기
from openai import OpenAI         # OpenAI 사용

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

        # 🔥 Firebase 연결하기

# 환경변수에서 Firebase 키 읽기
firebase_json = os.environ.get("FIREBASE_KEY")

if firebase_json:
    # 배포 환경: 환경변수에서 읽기
    cred_dict = json.loads(firebase_json)
    cred = credentials.Certificate(cred_dict)
else:
    # 로컬 환경: 파일에서 읽기
    cred = credentials.Certificate("firebase-key.json")

firebase_admin.initialize_app(cred)  # Firebase 앱 시작
db = firestore.client()               # db로 Firestore 사용!

# 🤖 OpenAI 연결하기
load_dotenv()                    # .env 파일 불러오기
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),   # .env에서 키 읽기
    base_url="https://copa.codyssey.kr/v1" # 코디세이 서버 주소
)


# FastAPI 앱(서버) 생성
app = FastAPI()


# 👇 이 부분 추가! (CORS 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 모든 주소에서 접근 허용
    allow_methods=["*"],      # 모든 요청 방식 허용 (GET, POST 등)
    allow_headers=["*"],      # 모든 헤더 허용
)


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


# 🔥 [저장] 공부 기록 추가하기
@app.post("/records")
def create_record(record: StudyRecord):
    # Firestore의 "records" 컬렉션에 저장!
    db.collection("records").add(record.dict())
    return {"message": "저장 완료!", "data": record}


# 🔥 [조회] 저장된 모든 기록 불러오기
@app.get("/records")
def get_records():
    # Firestore에서 모든 문서 가져오기
    docs = db.collection("records").stream()
    records = [doc.to_dict() for doc in docs]  # 딕셔너리로 변환
    return {"total": len(records), "records": records}

# 🤖 AI 채팅 API
class ChatRequest(BaseModel):     # 사용자가 보낼 메시지 형식
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    # 1) 📊 내 데이터 요약 가져오기
    summary_data = get_summary()
    summary_text = summary_data["summary"]

    # 2) 🤖 시스템 프롬프트 만들기
    system_prompt = f"""너는 공부를 도와주는 친절한 학습 비서야.
아래는 사용자의 실제 공부 기록이야:

{summary_text}

이 데이터를 참고해서 개인 맞춤형으로 답변해줘."""

    # 3) OpenAI에게 질문 보내기
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message}
        ]
    )
    answer = response.choices[0].message.content

    # 4) 💾 대화 자동 저장! (새로 추가된 부분!)
    conversation_data = {
        "title": req.message[:20],  # 질문 앞 20글자를 제목으로
        "messages": [
            {"role": "user", "content": req.message},
            {"role": "assistant", "content": answer}
        ],
        "created_at": datetime.now().isoformat()
    }
    doc_ref = db.collection("conversations").add(conversation_data)
    conv_id = doc_ref[1].id  # 저장된 대화 ID

    # 5) 답변 + 저장된 ID 함께 반환
    return {"reply": answer, "conversation_id": conv_id}

# 📊 [요약] 데이터 분석해서 요약 만들기
@app.get("/data/summary")
def get_summary():
    # 1) Firestore에서 모든 기록 가져오기
    docs = db.collection("records").stream()
    records = [doc.to_dict() for doc in docs]

    # 2) 데이터가 없으면 안내
    if not records:
        return {"summary": "아직 저장된 공부 기록이 없어요."}

    # 3) 공부 시간(value)만 뽑아서 리스트로
    values = [r["value"] for r in records]

    # 4) 통계 계산
    count = len(values)              # 총 개수
    total = sum(values)              # 총 공부 시간
    average = round(total / count)   # 평균
    maximum = max(values)            # 최대
    minimum = min(values)            # 최소

    # 5) 최근 추세 판단 (마지막 3개 비교)
    if count >= 2:
        recent = values[-1]          # 가장 최근
        before = values[-2]          # 그 전
        if recent > before:
            trend = "증가"
        elif recent < before:
            trend = "감소"
        else:
            trend = "유지"
    else:
        trend = "데이터 부족"

    # 6) 요약 결과 반환
    return {
        "count": count,
        "total_minutes": total,
        "average": average,
        "max": maximum,
        "min": minimum,
        "trend": trend,
        "summary": f"총 {count}번 기록, 평균 {average}분 공부, "
                   f"최대 {maximum}분, 최소 {minimum}분, 최근 추세는 '{trend}'입니다."
    }

from datetime import datetime  # ← 파일 맨 위 import 부분에 추가!


# ========================================
# 💬 대화 기록 (conversations) API
# ========================================

# 📋 대화 저장 형식 설계도
class Message(BaseModel):
    role: str      # "user" 또는 "assistant"
    content: str   # 메시지 내용

class Conversation(BaseModel):
    title: str              # 대화 제목
    messages: list[Message] # 메시지 목록


# 🔥 [저장] 대화 저장하기
@app.post("/api/conversations")
def create_conversation(conv: Conversation):
    # 저장할 데이터 만들기 (시간 추가!)
    data = {
        "title": conv.title,
        "messages": [m.dict() for m in conv.messages],
        "created_at": datetime.now().isoformat()  # 저장 시각
    }
    # Firestore에 저장하고, 생성된 문서 ID 받기
    doc_ref = db.collection("conversations").add(data)
    doc_id = doc_ref[1].id  # add()는 (시각, 문서참조) 튜플 반환
    return {"message": "대화 저장 완료!", "id": doc_id}


# 🔥 [목록] 모든 대화 목록 조회 (제목만!)
@app.get("/api/conversations")
def get_conversations():
    docs = db.collection("conversations").stream()
    conversations = []
    for doc in docs:
        d = doc.to_dict()
        conversations.append({
            "id": doc.id,                    # 문서 ID (불러올 때 필요!)
            "title": d.get("title", "제목 없음"),
            "created_at": d.get("created_at", "")
        })
    return {"total": len(conversations), "conversations": conversations}


# 🔥 [불러오기] 특정 대화의 전체 내용 조회
@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str):
    doc = db.collection("conversations").document(conv_id).get()
    if not doc.exists:
        return {"error": "대화를 찾을 수 없어요."}
    return doc.to_dict()


# 🔥 [삭제] 특정 대화 삭제
@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    db.collection("conversations").document(conv_id).delete()
    return {"message": "대화 삭제 완료!"}