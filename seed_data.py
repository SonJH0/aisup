import requests
import random
from datetime import datetime, timedelta

# 서버 주소
API = "http://localhost:8000/records"

# 공부 과목 후보 (메모에 랜덤으로 들어감)
subjects = [
    "파이썬 공부", "영어 단어 암기", "수학 문제풀이",
    "알고리즘 연습", "독서", "복습", "인강 시청",
    "코딩 실습", "자격증 공부", "노트 정리"
]

# 오늘 날짜부터 과거로 거슬러 올라가며 100일치 생성
today = datetime.now()
count = 0

for i in range(100):
    # i일 전 날짜 계산
    date = (today - timedelta(days=i)).strftime("%Y-%m-%d")

    # 공부 시간: 30분 ~ 180분 사이 랜덤
    value = random.randint(30, 180)

    # 메모: 과목 리스트에서 랜덤 선택
    memo = random.choice(subjects)

    # 서버로 POST 요청 (데이터 저장)
    res = requests.post(API, json={
        "date": date,
        "value": value,
        "memo": memo
    })

    count += 1
    print(f"[{count}/100] {date} - {value}분 - {memo} ✅")

print(f"\n🎉 완료! 총 {count}개 데이터 저장됨!")