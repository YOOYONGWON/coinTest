import time
import pyupbit
from collections import deque
import requests

# py -3.9 -m pip install pyupbit

#주문은 초당 8회, 분당 200회 / 주문 외 요청은 초당 30회, 분당 900회 사용 가능합니다.

# 21.12.03 home wifi ip : 61.252.114.230 
# 업비트 access key, secret key 변수  
# upbit_access = "QvwJsFcjx0FOXWxxAJvskcEuLx1zmNx2Tuum5p12"
# upbit_secret = "qVUGb1anosrFh9BI3GkQiJnHkjaCFXcKenTUb8Yj"

# 21.12.03 aws server ip : 3.135.237.142
# 업비트 access key, secret key 변수  
upbit_access = "qLF3XABxpNgjDHx11CexKIdhhx6xgQi76iwRpOB"
upbit_secret = "KhheD3EL90O5y7PJ3NvzoozTk70OXqZVlH8uQqFF"


# slack 
def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    ) 
myToken = "xoxb-2764724083696-2798012578180-BhA8Mj0CQ5HnQuoZXorxWgFk"
# post_message(myToken,"#upbit",'Hello fellow ~~~~~~~~!')


# 코인 리스트
tickers = []   
# 코인 종가 담을 deque 변수
ma05 = deque(maxlen=5)
ma20 = deque(maxlen=20)
ma60 = deque(maxlen=60)
# ma120 = deque(maxlen=120)

# 원화로 매매 가능한 코인 리스트 만들기
tickers = pyupbit.get_tickers(fiat="KRW")

# login
upbit = pyupbit.Upbit(upbit_access, upbit_secret)
# print("autotrade start")
# print(tickers)
post_message(myToken,"#upbit","won's autotrade start!")


# 잔고 조회 krw
def get_balance_krw():    
    balance = upbit.get_balance("KRW")
    return balance


# 잔고 조회 coin
def get_balance_wallet(ticker):
    
    balances = upbit.get_balances()

    for b in balances:
    
        if b['currency'] == ticker: 
            # print(f"balance: {b['balance']},  avg_buy_price: {b['avg_buy_price']}" ) 
            return float(b['avg_buy_price']), float(b['balance']) 
    
    # print('get_balance_wallet ticker-------'+ticker)    
    return int(0), int(0)




# 코인 심볼 하나씩 받아와서 이동평균선 구한 후 매수 조건 탐색
def get_ticker_ma(ticker):  

    '''get_ohlcv 함수는 고가/시가/저가/종가/거래량을 DataFrame으로 반환합니다'''
    df = pyupbit.get_ohlcv(ticker, interval='day') # 일봉 데이터 프레임 생성 
    # print(df)

    ma05.extend(df['close'])    # ma05 변수에 종가 넣기
    ma20.extend(df['close'])    # ma20 변수에 종가 넣기
    ma60.extend(df['close'])    # ma60 변수에 종가 넣기
    # ma120.extend(df['close'])   # ma120 변수에 종가 넣기

    curr_ma05 = sum(ma05) / len(ma05)       # ma05값 더해서 나누기 = 05일선 이동평균
    curr_ma20 = sum(ma20) / len(ma20)       # ma20값 더해서 나누기 = 20일선 이동평균
    curr_ma60 = sum(ma60) / len(ma60)       # ma60값 더해서 나누기 = 60일선 이동평균
    # curr_ma120 = sum(ma120) / len(ma120)    # ma20값 더해서 나누기 = 120일선 이동평균

    now_price = pyupbit.get_current_price(ticker)       # 코인의 현재가
    open_pirce = df['open'][-1]                 # 당일 시가 구하기
    buy_target_price = open_pirce + (open_pirce * 0.03) # 목표가 = 당일 시가 보다 3프로 이상 상승 금액

    # print('ticker[4:]>-------'+ticker[4:])
    coin_check = get_balance_wallet(ticker[4:]) # 코인 보유 하고 있는지 체크
    avg_pirce = coin_check[0]       # 매수 평균가
    balance = coin_check[1]         # 코인 보유 개수
 
    # 매수 평균가가 int 이면 매수 조건 체크 float이면 매도 조건 체크
    if avg_pirce == int(0): 
        # print(f"시세Check!!!  코인:{ticker}, 현재가:{now_price}" )
        # print(f"이동평균  ma20:{curr_ma20}, ma60:{curr_ma60}, ma120:{curr_ma120}" )

        # 이동 평균선 정배열 / 목표가보다 현재가 보다 높을 경우 매수 
        # if curr_ma05 <= curr_ma20 and buy_target_price <= now_price: 
        if curr_ma05 <= curr_ma20 and curr_ma20 <= curr_ma60 and buy_target_price <= now_price: 
        # if curr_ma20 <= curr_ma60 and curr_ma60 <= curr_ma120 and buy_target_price <= now_price:
            # buyPrice = round(20000 * 1, 1) 
            # print(f">>> 코인 매수!!! : {ticker},  현재가격: {now_price}, 주문가격: {buyPrice} " )

            buy_order(ticker, "A")
        else:
            # print('시세 감시 중! '+ticker) 
            pass
    else:
        # print(f"코인:{ticker},  매수평균가:{avg_pirce}, 보유개수:{balance}")

        # 현재 보유 코인 수익률 계산 
        if avg_pirce > 0.0:
            buy_profit = ((now_price - avg_pirce) / avg_pirce) * 100
            profit = round(buy_profit, 2)

            # 평균 매수가 보다 상승 시 매도
            if profit >= 3.0:
                # print(f"{ticker} : 목표가 도달 후 전량 매도")
                post_message(myToken,"#upbit",f"목표가 도달 매도!!! 코인:{ticker}, 수익률: {profit}")
                sell_order(ticker, balance)
                time.sleep(3) 
            elif profit < -15.0:
                # buyPrice = round(10000 * 1, 1) 
                # print(f">>> 추매 !!! : {ticker},  수익률: {profit}, 주문가격: {buyPrice}")
                post_message(myToken,"#upbit",f"추매 !!! 코인:{ticker}, 현재수익률: {profit}")
                buy_order(ticker, "B")
            else:
                # print(f"코인: {ticker}, 수익률: {profit}%" )
                pass

            # print(f">>>보유코인:{ticker},  매수평균가:{avg_pirce}, 수익률: {profit}%" )
            # print(f">>>보유코인:{ticker}, 수익률: {profit}%" )
        else:
            # print('매수 평균가 없음!')
            pass

       

# 매수 주문
def buy_order(ticker, buyGubun):
    try:
        krw = round(get_balance_krw(), 1)
        buyPrice = round(10000 * 1, 1) 
        # byVal = float(20000.0)

        if buyGubun == "A":
            buyPrice = round(20000 * 1, 1)  


        # print(f"코인:{ticker}, 잔고:{krw}, 구매가:{buyPrice}")
        # post_message(myToken,"#upbit",f"코인:{ticker}, 잔고:{krw}, 구매가:{buyPrice}")

        # 2만원 미만 잔고부족! 
        # if krw <= buyPrice: 
            # print(f"잔고부족! 잔고:{krw}") 
            # post_message(myToken,"#upbit",f"잔고부족! 코인:{ticker}, 잔고:{krw}") 
        if krw > buyPrice: 
             while True:
                buy_result = upbit.buy_market_order(ticker, buyPrice)
                # print( "매수가 :"+ {buy_result})
                post_message(myToken,"#upbit",f"매도주문!  코인:{ticker}, 구매가:{buyPrice}")

                if buy_result == None or 'error' in buy_result:
                    # print("매수 재 주문")
                    time.sleep(5) 
                else:
                    return buy_result 
        else:
            # print(f"잔고부족 else !!! 잔고:{krw}") 
            pass

    except ValueError as m:
        # print(f"매수 주문 Error!  코인:{ticker}, 잔고:{krw}, 구매가:{buyPrice}")
        print(m)
    except TypeError as m:
        # print(f"매수 주문 Error!  코인:{ticker}, 잔고:{krw}, 구매가:{buyPrice}")
        print(m)
    else:
        pass

# 매도 주문
def sell_order(ticker, volume):
    try:
        post_message(myToken,"#upbit",f"매도주문!  코인:{ticker}, 수량:{volume}")

        while True:
            sell_result = upbit.sell_market_order(ticker, volume)
            if sell_result == None or 'error' in sell_result:
                # print(f"{sell_result}, 매도 재 주문")
                # time.sleep(1)
                pass
            else:
                return sell_result
    except:
        # print("매도 주문 이상")
        pass

# 코인 리스트에서 이동 평균선 함수로 하나씩 꺼내서 보내기
while True:    
    try:        

        for tk in tickers:   
            # print('tickers >>>>> '+tk)         
            get_ticker_ma(tk)
            # time.sleep(2)

            if tk == 'KRW-BTC':
                # print('repeat sleep~')
                time.sleep(300)
            else:
                time.sleep(3)

    except:
        # print('오류 발생 무시')
        pass