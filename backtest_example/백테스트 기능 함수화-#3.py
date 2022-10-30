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


##실행부분
backtest_etf = ['VT', 'VUSTX', 'IEF', 'GSG', 'GLD']
benchmark_data = merge_file(backtest_etf)

start_date = benchmark_data.index[0]
end_date = benchmark_data.index[-1]
rebalancing_period = find_rebalancing_period(benchmark_data, start_date, end_date, 3)
