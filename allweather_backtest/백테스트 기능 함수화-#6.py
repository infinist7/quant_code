import yfinance as yf
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import *
import matplotlib.pyplot as plt
import math
import numpy as np

#from FinanceDataReader import DataReader as fdr


##함수 부분
def merge_file(etflist):
    benchmark_df = pd.DataFrame()
    for number in range(0, len(etflist)):
        each_etf_df = load_and_arrange_data(etflist[number])
        benchmark_df = pd.merge(benchmark_df, each_etf_df, left_index=True, right_index=True, how='outer')

    benchmark_final = benchmark_df.dropna()
    return benchmark_final


def load_and_arrange_data(etfname):
    item_df =  yf.Ticker(etfname).history(period='max')
    item_df = item_df.rename(columns={'Close': etfname})
    item_df = item_df[[etfname]]
    item_df = item_df[~item_df.index.duplicated(keep='first')]

    return item_df


def find_rebalancing_period(data, start_date, end_date, byperiod):
    period_df = pd.DataFrame(data[start_date:end_date].index)
    select_date = period_df.loc[period_df.groupby(pd.Grouper(key='Date', freq=f'{byperiod}M')).Date.idxmax()]
    backtest_end_date = end_date + relativedelta(months=-1) + relativedelta(day=+40)
    rebalancing_day = [intime for intime in select_date['Date'] if intime <= backtest_end_date]

    return rebalancing_day


def get_backtest_result(rebalancing_period, benchmark_data, asset_share, stock_share=1):
    initial_money = 1000
    total_backtest_result = pd.DataFrame()
    for index in range(len(rebalancing_period) - 1):
        sub_benchmark_data = pd.DataFrame(benchmark_data.loc[rebalancing_period[index]:rebalancing_period[index + 1]])
        backtest_result = do_backtest(initial_money, sub_benchmark_data, asset_share, stock_share)
        initial_money = backtest_result['total_asset'][-1]
        total_backtest_result = pd.concat([total_backtest_result[:-1], backtest_result])

    return total_backtest_result


def do_backtest(initial_money, sub_benchmark_data, asset_share, stock_share):
    stock_money = initial_money * stock_share
    backtest_result = pd.DataFrame(index=sub_benchmark_data.index)
    backtest_result['stock_asset'] = 0

    for col in sub_benchmark_data.columns:
        initial_buy = math.trunc(asset_share[col] * stock_money / sub_benchmark_data[col][0])
        backtest_result['stock_asset'] = backtest_result['stock_asset'] + initial_buy * sub_benchmark_data[col]
    backtest_result['cash_asset'] = initial_money - backtest_result['stock_asset'][0]
    backtest_result['total_asset'] = backtest_result['stock_asset'] + backtest_result['cash_asset']
    backtest_result['daily_return'] = backtest_result['total_asset'].pct_change() * 100

    return backtest_result


def calculate_cagr(total_backtest_result):
    year_period = total_backtest_result.index[-1].year - total_backtest_result.index[0].year
    month_period = (total_backtest_result.index[-1].month - total_backtest_result.index[0].month) / 12
    final_period = year_period + month_period

    CAGR = ((total_backtest_result.iloc[-1]['total_asset'] / total_backtest_result.iloc[0]['total_asset']) ** (
            1 / final_period) - 1) * 100

    return CAGR


def calculate_mdd(total_backtest_result):
    max_value = np.maximum.accumulate(total_backtest_result['total_asset'])
    rate_value = (total_backtest_result['total_asset'] - max_value) / max_value
    mdd = rate_value.min()*100

    return mdd


def calculate_gr_byyear(total_backtest_result):
    yr_list = [j.year for j in total_backtest_result.index]
    first_yr, end_yr = np.min(yr_list), np.max(yr_list)
    yr_index = [yr_list.index(j) for j in range(first_yr, end_yr + 1)]
    yr_index.append(len(total_backtest_result)-1)
    yr_rate = {}
    for index in range(0, len(yr_index[:-1])):
        yr_rate[f'{first_yr + index}'] = round(((total_backtest_result['total_asset'][yr_index[index + 1]] /
                                                 total_backtest_result['total_asset'][yr_index[index]]) - 1) * 100, 2)

    return yr_rate


#실행부분
backtest_etf = ['VT', 'VUSTX', 'IEF', 'GSG', 'GLD']
benchmark_data = merge_file(backtest_etf)

start_date = benchmark_data.index[0]
end_date = benchmark_data.index[-1]
rebalancing_period = find_rebalancing_period(benchmark_data, start_date, end_date, 3)

asset_share = {'VT': 0.3, 'VUSTX': 0.3, 'IEF': 0.25, 'GSG': 0.075, 'GLD': 0.075}
total_backtest_result = get_backtest_result(rebalancing_period, benchmark_data, asset_share)

cagr = calculate_cagr(total_backtest_result)
mdd = calculate_mdd(total_backtest_result)
yr_rate = calculate_gr_byyear(total_backtest_result)

total_backtest_result['total_asset'].plot()
plt.show()




## 2번 코드 예제
etfname = 'vustx'
item_df = yf.Ticker(etfname).history(period='max')
item_df = item_df.rename(columns={'Close': etfname})
item_df = item_df[[etfname]]
item_df = item_df[~item_df.index.duplicated(keep='first')]

etfname = 'vustx'
item_df_vustx = yf.Ticker(etfname).history(period='max')
item_df_vustx = item_df_vustx.rename(columns={'Close': etfname})
item_df_vustx = item_df_vustx[[etfname]]
item_df_vustx = item_df_vustx[~item_df_vustx.index.duplicated(keep='first')]



### 2번 코드 함수화
def load_and_arrange_data(etfname):
    item_df =  yf.Ticker(etfname).history(period='max')
    item_df = item_df.rename(columns={'Close': etfname})
    item_df = item_df[[etfname]]
    item_df = item_df[~item_df.index.duplicated(keep='first')]

    return item_df

item_df = load_and_arrange_data('vt')
item_df_vustx = load_and_arrange_data('vustx')


### 3번 코드 예제
benchmark_df = pd.DataFrame()
benchmark_df = pd.merge(benchmark_df, item_df, left_index=True, right_index=True, how='outer')
benchmark_df = pd.merge(benchmark_df, item_df_vustx, left_index=True, right_index=True, how='outer')



### 3번 코드 함수화
def merge_file(etflist):
    benchmark_df = pd.DataFrame()
    for number in range(0, len(etflist)):
        each_etf_df = load_and_arrange_data(etflist[number])
        benchmark_df = pd.merge(benchmark_df, each_etf_df, left_index=True, right_index=True, how='outer')

    benchmark_final = benchmark_df.dropna()
    return benchmark_final

backtest_etf = ['VT', 'VUSTX', 'IEF', 'GSG', 'GLD']
benchmark_data = merge_file(backtest_etf)


#### 3번코드 포함 후 최종 결과물

def load_and_arrange_data(etfname):
    item_df =  yf.Ticker(etfname).history(period='max')
    item_df = item_df.rename(columns={'Close': etfname})
    item_df = item_df[[etfname]]
    item_df = item_df[~item_df.index.duplicated(keep='first')]

    return item_df


def merge_file(etflist):
    benchmark_df = pd.DataFrame()
    for number in range(0, len(etflist)):
        each_etf_df = load_and_arrange_data(etflist[number])
        benchmark_df = pd.merge(benchmark_df, each_etf_df, left_index=True, right_index=True, how='outer')

    benchmark_final = benchmark_df.dropna()
    return benchmark_final

backtest_etf = ['VT', 'VUSTX', 'IEF', 'GSG', 'GLD']
benchmark_data = merge_file(backtest_etf)
