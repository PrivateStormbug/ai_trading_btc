import os
# 한글 출력을 위한 설정
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')                       # 한글 출력을 위한 설정

from dotenv import load_dotenv

load_dotenv()

def ai_trading():
  # 1. 업비트 차트 데이터 가져오기(30일 일봉 데이터)
  access = os.getenv("UPBIT_ACCESS_KEY")
  secret = os.getenv("UPBIT_SECRET_KEY")
  import pyupbit

  df = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=30)                             # Open(첫거래 가격), High(최고 거래 가격), Low(최저 거래 가격), Close(마지막 거래 가격), Volume(거래량)

  # 2. 오픈AI 데이터 제공하고 거래 판단 받기
  from openai import OpenAI
  client = OpenAI()

  response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
      {
        "role": "system",
        "content": [
          {
            "type": "text",
            "text": "You are an expert in bitcoin investing.\\nTell me if I should buy, sell, or hold at the time of my inquiry based on the chart data provided. The answer will be in JSON format.\nresponse example :\n{\"decision\":\"buy\", \"reason\":\"some technical reason\"}\n{\"decision\":\"sell\", \"reason\":\"some technical reason\"}\n{\"decision\":\"hold\", \"reason\":\"some technical reason\"}"
          }
        ]
      },
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": df.to_json()                                                          # 데이터 프레임을 JSON 형식으로 변환
          }
        ]
      },
    ],
    response_format={
      "type": "json_object"
    },
  )

  result = response.choices[0].message.content
  import json
  result = json.loads(result)

  from deep_translator import GoogleTranslator
  model="gpt-4"                                                                         # 번역할 떄는 gtp-4 사용

  # 판단 출력
  if result["decision"] == "buy":
      decision = "매수"
  elif result["decision"] == "sell":
      decision = "매도"
  elif result["decision"] == "hold":
      decision = "보유"
  
  reason = GoogleTranslator(source='en', target='ko', model=model).translate(result["reason"])
  print(f"### AI 판단 : {decision} ###")
  print(f"### AI 이유 : {reason} ###")

  # 3. 업비트 API로 매매 명령 보내기
  import pyupbit

  upbit = pyupbit.Upbit(access, secret)

  # 잔고 조회
  print("########################################")
  print("### 신규 조회 ###")
  print("### 잔고 조회 ###")

  my_krw = upbit.get_balance("KRW")                                                     # 현재 보유 원화 잔고
  my_btc = upbit.get_balance("KRW-BTC")                                                 # 현재 보유 비트코인 잔고

  print(f"### krw 잔고 : {my_krw} ###")
  print(f"### btc 잔고 : {my_btc} ###")

  if result["decision"] == "buy":
    # 매수
    if my_krw*0.9995 > 5000:
        print(f"### 매수 수량: {upbit.buy_market_order('KRW-BTC', my_krw * 0.9995)} ###")   # 원화 잔고의 99.95% 만큼 BTC 매수(수수료 제외)
        print(f"### 매수 완료: {reason} ###")
    else:
        print(f"### 매수 실패: 5,000원 미만 ###")
  elif result["decision"] == "sell":
    current_price = pyupbit.get_orderbook("KRW-BTC")["orderbook_units"][0]["ask_price"]   # 현재 비트코인 매도 호가 가격
    if my_btc*current_price > 5000:
        print(f"### 매도 수량: {upbit.sell_market_order('KRW-BTC', my_btc)} ###")         # 보유 비트코인 전량 매도(수수료 제외)
        print(f"### 매도 완료: {reason} ###")
    else:
        print(f"### 매도 실패: 5,000원 미만 ###")
  elif result["decision"] == "hold":
    # 보유
    print(f"### 보유 중: {reason} ###")
    pass

while True:
  ai_trading()
  import time
  time.sleep(10)
