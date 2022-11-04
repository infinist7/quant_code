from pandas_datareader import data as pdr
import pandas as pd
from dateutil.relativedelta import *


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


def calculate_momentum(benchmark_data, period):
    momentum_result = {}
    current_day = benchmark_data.index[-1]
    base_day = current_day - relativedelta(months=period)
    for name in benchmark_data.columns:
        rate = (benchmark_data.loc[current_day, name] / benchmark_data.loc[base_day, name]-1)*100
        momentum_result[f'{name}_{period}month'] = round(rate,2)

    return momentum_result



backtest_etf = ['VT', 'VUSTX', 'IEF', 'GSG', 'GLD']
benchmark_data = merge_file(backtest_etf)

momentum_r = calculate_momentum(benchmark_data, 1)


