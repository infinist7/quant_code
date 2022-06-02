# 패키지 설치 코드
# pip install pandas-datareader
# pip install finance-datareader
# 이미 설치되어 있는 상황에서 에러가 발생하는 경우 버전업이 필요

# pip install pandas-datareader --upgrade
# pip install finance-datareader --upgrade

from pandas_datareader import data as pdr
from FinanceDataReader import DataReader as fdr
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import *
import math


#1. 자료 읽어오기
# pandas_datareader를 사용하여 시계열 가격 자료 읽어오기(as pbr)
world_stock = pdr.get_data_yahoo('VT','1/1/1990')
longterm_bond = pdr.get_data_yahoo('VUSTX', '1/1/1990')
midterm_bond = pdr.get_data_yahoo('IEF', '1/1/1990')
commodity = pdr.get_data_yahoo('GSG', '1/1/1990')
gold = pdr.get_data_yahoo('GLD','1/1/1990')

# FinanceDataReader를 사용하여 시계열 가격 자료 읽어오기(as fdr)
# world_stock = fdr('VT', '1990-01-01')
# longterm_bond = fdr('VUSTX','1990-01-01')
# midterm_bond = fdr('IEF', '1990-01-01')
# commodity = fdr('GSG', '1990-01-01')
# gold = fdr('GLD', '1990-01-01')


# 2. 자료 정리
  # 2-1. 변수 이름 변경, 이후 필요한 정보만 남기기
world_stock.rename(columns = {'Adj Close': 'world_stock'}, inplace=True)
longterm_bond.rename(columns = {'Adj Close': 'longterm_bond'}, inplace=True)
midterm_bond.rename(columns = {'Adj Close': 'midterm_bond'}, inplace=True)
commodity.rename(columns = {'Adj Close': 'commodity'}, inplace=True)
gold.rename(columns = {'Adj Close': 'gold'}, inplace=True)

world_stock_price = pd.DataFrame(world_stock['world_stock'])
longterm_bond_price = pd.DataFrame(longterm_bond['longterm_bond'])
midterm_bond_price =  pd.DataFrame(midterm_bond['midterm_bond'])
commodity_price = pd.DataFrame(commodity['commodity'])
gold_price = pd.DataFrame(gold['gold'])

  #2-2. 중복 시점 자료가 존재할 경우 처리
world_stock_price = world_stock_price[~world_stock_price.index.duplicated(keep='first')]
longterm_bond_price = longterm_bond_price[~longterm_bond_price.index.duplicated(keep='first')]
midterm_bond_price = midterm_bond_price[~midterm_bond_price.index.duplicated(keep='first')]
commodity_price = commodity_price[~commodity_price.index.duplicated(keep='first')]
gold_price = gold_price[~gold_price.index.duplicated(keep='first')]

  #2-3. 상품 가격 정보를 merge
benchmark_data = pd.DataFrame()

benchmark_data = pd.merge(world_stock_price,longterm_bond_price,left_index=True, right_index=True, how='outer')
benchmark_data = pd.merge(benchmark_data, midterm_bond_price,left_index=True, right_index=True, how='outer')
benchmark_data = pd.merge(benchmark_data, commodity_price, left_index=True, right_index=True, how='outer')
benchmark_data = pd.merge(benchmark_data, gold_price, left_index=True, right_index=True, how='outer')



#3. 인덱스 조정 및 모든 상품의 가격이 존재하는 기간만 남기는 작업
  #3-1. index 형태를 문자로 전환
benchmark_data.set_index(keys=[[j.date().strftime('%Y-%m-%d') for j in benchmark_data.index]], inplace=True)

  #3-2. 모든 상품의 가격이 존재하는 기간만 남기기
benchmark_data=benchmark_data.dropna()


#4. 리밸런싱 날짜 계산
   #4-1.리밸런싱 기준 날짜 얻기
start_date =benchmark_data.index[0]
end_date = benchmark_data.index[-1]

   #4-2.리밸런싱 주기 설정. 여기서는 입력값의 단위를 월(month)로 받을 예정.
step = 6 # 6개월마다 리밸런싱할 날짜 계산

   #4-3. 리밸런싱 날짜 계산. 최종 결과값은 rebalancing_day에 저장
rebalancing_day = []
dateformat_recent_date = start_date

while dateformat_recent_date <= end_date:
    rebalancing_day.append(dateformat_recent_date)
    recent_yr, recent_month, recent_day = dateformat_recent_date.split('-')
    calculated_date = date(int(recent_yr), int(recent_month), int(recent_day)) + relativedelta(months=step)
    dateformat_recent_date = calculated_date.strftime("%Y-%m-%d")



# 5. 수익률 계산 예제
    #5-1.기본설정
initial_money = 1000
asset_share = {'world_stock':0.3, 'longterm_bond':0.3, 'midterm_bond':0.25, 'commodity':0.075, 'gold':0.075}

    # 5-2.백테스트 결과 저장을 위한 dataframe 생성
backtest_result = pd.DataFrame(index=benchmark_data.index)
backtest_result['stock_asset'] = 0

    # 5-3. 백테스트 결과 저장
for col in benchmark_data.columns:
    initial_buy = math.trunc(asset_share[col] * initial_money / benchmark_data[col][0])
    backtest_result['stock_asset'] = backtest_result['stock_asset'] + initial_buy * benchmark_data[col]
backtest_result['cash_asset'] = initial_money - backtest_result['stock_asset'][0]
backtest_result['total_asset'] = backtest_result['stock_asset'] + backtest_result['cash_asset']
backtest_result['daily_return'] = backtest_result['total_asset'].pct_change() * 100



