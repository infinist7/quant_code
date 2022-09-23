from pandas_datareader import data as pdr
from FinanceDataReader import DataReader as fdr
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import *
import math
import matplotlib.pyplot as plt
import numpy as np


##함수 부분
def merge_file(etflist):
    benchmark_df = pd.DataFrame()
    for number in range(0, len(etflist)):
        each_etf_df = load_and_arrange_data(etflist[number])
        benchmark_df = pd.merge(benchmark_df, each_etf_df, left_index=True, right_index=True, how='outer')

    benchmark_final = benchmark_df.dropna()
    return benchmark_final


def load_and_arrange_data(etfname, periods='1/1/1990'):
    load_key = etfname.upper()
    item_df = pdr.get_data_yahoo(load_key, periods)
    if 'Adj Close' in item_df.columns:
        item_df = item_df.rename(columns={'Adj Close': etfname})
    elif 'Adj Close' not in item_df.columns:
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


def calculate_rate(total_backtest_result):
    year_period = total_backtest_result.index[-1].year - total_backtest_result.index[0].year
    month_period = (total_backtest_result.index[-1].month - total_backtest_result.index[0].month) / 12
    final_period = year_period + month_period

    CAGR = ((total_backtest_result.iloc[-1]['total_asset'] / total_backtest_result.iloc[0]['total_asset']) ** (
            1 / final_period) - 1) * 100

    return CAGR



##실행부분
backtest_etf = ['VT', 'VUSTX', 'IEF', 'GSG', 'GLD']
benchmark_data = merge_file(backtest_etf)

start_date = benchmark_data.index[0]
end_date = benchmark_data.index[-1]
rebalancing_period = find_rebalancing_period(benchmark_data, start_date, end_date, 3)

asset_share = {'VT': 0.3, 'VUSTX': 0.3, 'IEF': 0.25, 'GSG': 0.075, 'GLD': 0.075}
total_backtest_result = get_backtest_result(rebalancing_period, benchmark_data, asset_share)

cagr = calculate_rate(total_backtest_result)



