import time
import pyupbit
from collections import deque
import requests 
import uuid
import datetime
import logging

# INTERVAL_MIN = 1 # 간격
logging.basicConfig(level=logging.INFO)
  
# 업비트 access key, secret key 변수  
upbit_access = "QvwJsFcjx0FOXWxxAJvskcEuLx1zmNx2Tuum5p12"
upbit_secret = "qVUGb1anosrFh9BI3GkQiJnHkjaCFXcKenTUb8Yj"
 
# 코인 리스트
tickers = []   
# 코인 종가 담을 deque 변수
ma01 = deque(maxlen=1)
ma05 = deque(maxlen=5)
ma20 = deque(maxlen=20)
ma60 = deque(maxlen=60)
# ma120 = deque(maxlen=120)

vol_01 = deque(maxlen=1)
vol_05 = deque(maxlen=5)

# 원화로 매매 가능한 코인 리스트 만들기
tickers = pyupbit.get_tickers(fiat="KRW")

# login
upbit = pyupbit.Upbit(upbit_access, upbit_secret)
logging.info("autotrade start!")
# logging.info(tickers) 


# 잔고 조회 krw
def get_balance_krw():    
    balance = upbit.get_balance("KRW")
    return balance


# 잔고 조회 coin
def get_balance_wallet(ticker):
    
    balances = upbit.get_balances()

    for b in balances:
    
        if b['currency'] == ticker: 
            # logging.info(f"balance: {b['balance']},  avg_buy_price: {b['avg_buy_price']}" ) 
            return float(b['avg_buy_price']), float(b['balance']) 
    
    # logging.info('get_balance_wallet ticker-------'+ticker)    
    return int(0), int(0)



# candle 요청 회수 제한이 걸리면 1초 sleep
def check_remaining_candles_req(upbit):
    ret = upbit.get_remaining_req()
    if ret is None:
        return
    if 'candles' not in ret.keys():
        return
    if int(ret['candles']['sec']) == 0:
        # logging.info('>>> sleep 1 seconds')
        time.sleep(1)


# 코인 심볼 하나씩 받아와서 이동평균선 구한 후 매수 조건 탐색
def get_ticker_ma(ticker):  

    '''get_ohlcv 함수는 고가/시가/저가/종가/거래량을 DataFrame으로 반환합니다'''
    df = pyupbit.get_ohlcv(ticker, interval='day') # 일봉 데이터 프레임 생성 
    # df = pyupbit.get_ohlcv(ticker, interval="minute60")
    # logging.info(df)
    # {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})

    # OPEN HIGH	LOW	CLOS
    ma05.extend(df['close'])    # ma05 변수에 종가 넣기
    ma20.extend(df['close'])    # ma20 변수에 종가 넣기
    ma60.extend(df['close'])    # ma60 변수에 종가 넣기
    # ma120.extend(df['close'])   # ma120 변수에 종가 넣기

    vol_01.extend(df['volume'])    # 
    vol_05.extend(df['volume'])    # 
 
    curr_ma05 = sum(ma05) / len(ma05)       # ma05값 더해서 나누기 = 05일선 이동평균
    curr_ma20 = sum(ma20) / len(ma20)       # ma20값 더해서 나누기 = 20일선 이동평균
    curr_ma60 = sum(ma60) / len(ma60)       # ma60값 더해서 나누기 = 60일선 이동평균
    # curr_ma120 = sum(ma120) / len(ma120)    # ma20값 더해서 나누기 = 120일선 이동평균

    curr_vol_01 = sum(vol_01) / len(vol_01)  
    curr_vol_05 = sum(vol_05) / len(vol_05)  
    # logging.info(f">>> 코인 거래량!!! : {ticker},  curr_vol_05: {curr_vol_05}, curr_vol_01: {curr_vol_01} " )

    now_price = pyupbit.get_current_price(ticker)       # 코인의 현재가
    open_pirce = df['open'][-1]                 # 당일 시가 구하기
    buy_target_price = open_pirce + (open_pirce * 0.03) # 목표가 = 당일 시가 보다 3프로 이상 상승 금액

    # logging.info('ticker[4:]>-------'+ticker[4:])
    coin_check = get_balance_wallet(ticker[4:]) # 코인 보유 하고 있는지 체크
    avg_pirce = coin_check[0]       # 매수 평균가
    balance = coin_check[1]         # 코인 보유 개수
 
   

    # 매수 평균가가 int 이면 매수 조건 체크 float이면 매도 조건 체크
    if avg_pirce == int(0):  
        # 이동 평균선 정배열 / 목표가보다 현재가 보다 높을 경우 매수 
        # if curr_ma05 <= curr_ma20 and buy_target_price <= now_price: 
        if curr_ma05 <= curr_ma20 and curr_ma20 <= curr_ma60 and buy_target_price <= now_price and curr_vol_05 < curr_vol_01 : 
            # logging.info(f">>> 코인 매수!!! : {ticker},  현재가격: {now_price}, 주문가격: {buyPrice} " )
            buy_order(ticker, "A")
        else:
            # logging.info('시세 감시 중! '+ticker) 
            pass
    else:
        # logging.info(f"코인:{ticker},  매수평균가:{avg_pirce}, 보유개수:{balance}")

        # 현재 보유 코인 수익률 계산 
        if avg_pirce > 0.0:
            buy_profit = ((now_price - avg_pirce) / avg_pirce) * 100
            profit = round(buy_profit, 2)

            # 평균 매수가 보다 상승 시 매도
            if profit >= 5.0:
                # logging.info(f"{ticker} : 목표가 도달 후 전량 매도")
                # post_message(myToken,"#upbit",f"목표가 도달 매도!!! 코인:{ticker}, 수익률: {profit}")
                sell_order(ticker, balance)
                time.sleep(3)  
            else:
                # logging.info(f"코인: {ticker}, 수익률: {profit}%" )
                pass 
        else:
            # logging.info('매수 평균가 없음!')
            pass

       

# 매수 주문
def buy_order(ticker, buyGubun):
    try:
        krw = round(get_balance_krw(), 1)
        buyPrice = round(10000 * 1, 1)  

        if buyGubun == "A":
            buyPrice = round(20000 * 1, 1)  

        logging.info(f"코인:{ticker}, 잔고:{krw}, 구매가:{buyPrice}")
        # post_message(myToken,"#upbit",f"코인:{ticker}, 잔고:{krw}, 구매가:{buyPrice}")

        if krw > buyPrice: 
            # post_message(myToken,"#upbit",f"매수주문!  코인:{ticker}, 구매가:{buyPrice}")
            while True:
                buy_result = upbit.buy_market_order(ticker, buyPrice)
                # logging.info( "매수가 :"+ {buy_result})

                if buy_result == None or 'error' in buy_result:
                    # logging.info("매수 재 주문")
                    time.sleep(5) 
                else:
                    return buy_result 
        else:
            # logging.info(f"잔고부족 else !!! 잔고:{krw}") 
            pass

    except ValueError as m:
        # logging.info(f"매수 주문 Error!  코인:{ticker}, 잔고:{krw}, 구매가:{buyPrice}")
        logging.info(m)
    except TypeError as m:
        # logging.info(f"매수 주문 Error!  코인:{ticker}, 잔고:{krw}, 구매가:{buyPrice}")
        logging.info(m)
    else:
        pass

# 매도 주문
def sell_order(ticker, volume):
    try:
        # post_message(myToken,"#upbit",f"매도주문!  코인:{ticker}, 수량:{volume}")
        logging.info(f"매도주문!  코인:{ticker}, 수량:{volume}")

        while True:
            sell_result = upbit.sell_market_order(ticker, volume)
            if sell_result == None or 'error' in sell_result:
                # logging.info(f"{sell_result}, 매도 재 주문")
                # time.sleep(1)
                pass
            else:
                return sell_result
    except:
        # logging.info("매도 주문 이상")
        pass




# 코인 리스트에서 이동 평균선 함수로 하나씩 꺼내서 보내기
while True:    
    try:        

        # logging.basicConfig(level=logging.INFO)

        for tk in tickers:   
            # logging.info('tickers >>>>> '+tk)         
            get_ticker_ma(tk)
            # time.sleep(2)

            if tk == 'KRW-BTC':
                # logging.info('repeat sleep~')
                time.sleep(180)
            else:
                time.sleep(2)

    except:
        # logging.info('오류 발생 무시')
        pass