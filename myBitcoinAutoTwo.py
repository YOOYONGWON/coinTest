import time
import pyupbit
from collections import deque

#주문은 초당 8회, 분당 200회 / 주문 외 요청은 초당 30회, 분당 900회 사용 가능합니다.

# 업비트 access key, secret key 변수
upbit_access = "aYPy98ub6JxmqYo5vKbqTemE5OpUO0o84O3oHZaq"
upbit_secret = "TJQMiZ2RGjMsT5yd2dsnYl7nnFraMkK7HKHL68Db"


# 코인 리스트
tickers = []   
# 코인 종가 담을 deque 변수
ma20 = deque(maxlen=20)
ma60 = deque(maxlen=60)
ma120 = deque(maxlen=120)

# 원화로 매매 가능한 코인 리스트 만들기
tickers = pyupbit.get_tickers(fiat="KRW")

# login
upbit = pyupbit.Upbit(upbit_access, upbit_secret)

# 잔고 조회 krw
def get_balance_krw():    
    balance = upbit.get_balance("KRW")
    return balance

# 잔고 조회 coin
def get_balance_wallet(ticker):
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker[4:]:
            balance = b['balance']
            avg_buy_price = b['avg_buy_price']
            return float(avg_buy_price), float(balance)
        else:
            return int(0), int(0)

# 코인 심볼 하나씩 받아와서 이동평균선 구한 후 매수 조건 탐색
def get_ticker_ma(ticker):  

    '''get_ohlcv 함수는 고가/시가/저가/종가/거래량을 DataFrame으로 반환합니다'''
    df = pyupbit.get_ohlcv(ticker, interval='day') # 일봉 데이터 프레임 생성

    ma20.extend(df['close'])    # ma20 변수에 종가 넣기
    ma60.extend(df['close'])    # ma60 변수에 종가 넣기
    ma120.extend(df['close'])   # ma120 변수에 종가 넣기

    curr_ma20 = sum(ma20) / len(ma20)       # ma20값 더해서 나누기 = 20일선 이동평균
    curr_ma60 = sum(ma60) / len(ma60)       # ma60값 더해서 나누기 = 60일선 이동평균
    curr_ma120 = sum(ma120) / len(ma120)    # ma20값 더해서 나누기 = 120일선 이동평균

    now_price = pyupbit.get_current_price(ticker)       # 코인의 현재가
    open_pirce = df['open'][-1]                 # 당일 시가 구하기
    buy_target_price = open_pirce + (open_pirce * 0.02) # 목표가 = 당일 시가 보다 2프로 이상 상승 금액

    coin_check = get_balance_wallet(ticker) # 코인 보유 하고 있는지 체크
    avg_pirce = coin_check[0]   # 매수 평균가
    balance = coin_check[1]         # 코인 보유 개수

    # 매수 평균가가 int 이면 매수 조건 체크 float이면 매도 조건 체크
    if avg_pirce == int:
        # 이동 평균선 정배열 / 목표가보다 현재가 보다 높을 경우 매수
        if curr_ma20 <= curr_ma60 and curr_ma60 <= curr_ma120 and buy_target_price <= now_price:
            # 50만원치 매수
            volume = round(500000 / now_price * 0.995, 4)
            buy_order(ticker, volume)
        else:
            print('시세 감시 중')
            pass
    else:
        # 현재 보유 코인 수익률 계산 
        buy_profit = ((now_price - avg_pirce) / avg_pirce) * 100
        profit = round(buy_profit, 2)

        # 평균 매수가 보다 2% 상승 시 매도
        if profit >= 2.0:
            print(f"{ticker} : 목표가 도달 후 전량 매도")
            sell_order(ticker, balance)
            time.sleep(3) 
        else:
            print(f"코인명: {ticker}, 수익률: {profit}%" )

# 매수 주문
def buy_order(ticker, volume):
    try:
        while True:
            buy_result = upbit.buy_market_order(ticker, volume)
            if buy_result == None or 'error' in buy_result:
                print("매수 재 주문")
                time.sleep(1)
            else:
                return buy_result
    except:
        print("매수 주문 이상")

# 매도 주문
def sell_order(ticker, volume):
    try:
        while True:
            sell_result = upbit.sell_market_order(ticker, volume)
            if sell_result == None or 'error' in sell_result:
                print(f"{sell_result}, 매도 재 주문")
                time.sleep(1)
            else:
                return sell_result
    except:
        print("매도 주문 이상")

# 코인 리스트에서 이동 평균선 함수로 하나씩 꺼내서 보내기
while True:    
    try:        
        for tk in tickers:            
            get_ticker_ma(tk)
            time.sleep(2)
    except:
        print('오류 발생 무시')
        pass