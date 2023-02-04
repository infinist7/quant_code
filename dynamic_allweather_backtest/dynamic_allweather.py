# 동적 올웨더 구현 예제
# 주식 모멘텀이 채권 모멘텀보다 클 경우 주식 비중 증가, 채권 비중 축소
# 반대로 주식 모멘텀이 채권 모멘텀보다 낮을 경우 주식 비중 축소, 채권 비중 증가


import pandas as pd
from dateutil.relativedelta import *
import math
import numpy as np
import yfinance as yf


def merge_file(etflist):
    benchmark_df = pd.DataFrame()
    for number in range(0, len(etflist)):
        each_etf_df = load_and_arrange_data(etflist[number])
        benchmark_df = pd.merge(benchmark_df, each_etf_df, left_index=True, right_index=True, how='outer')

    benchmark_final = benchmark_df.dropna()
    return benchmark_final


def load_and_arrange_data(etfname):
    load_key = etfname.upper()
    item_df = yf.Ticker(load_key).history(period='max')

    if 'Adj Close' in item_df.columns:
        item_df = item_df.rename(columns={'Adj Close': etfname})
    elif 'Adj Close' not in item_df.columns:
        item_df = item_df.rename(columns={'Close': etfname})
    item_df = item_df[[etfname]]
    item_df = item_df[~item_df.index.duplicated(keep='first')]

    return item_df


def find_reb_period(data, start_date, end_date, byperiod):
    period_df = pd.DataFrame(data[start_date:end_date].index)
    select_date = period_df.loc[period_df.groupby(pd.Grouper(key='Date', freq=f'{byperiod}M')).Date.idxmax()]
    backtest_end_date = end_date + relativedelta(months=-1) + relativedelta(day=+40)
    rebalancing_day = [intime for intime in select_date['Date'] if intime <= backtest_end_date]

    return rebalancing_day


def get_backtest_result(reb_period, benchmark_data, ag_asset, def_asset, inv_share=1, mom_set=6):
    initial_money = 1000
    total_backtest_result = pd.DataFrame()

    for index in range(len(reb_period) - 1):
        find_ag_momentum = calculate_momentum(benchmark_data[:reb_period[index]], ag_asset, mom_set)
        find_def_momentum = calculate_momentum(benchmark_data[:reb_period[index]], def_asset, mom_set)
        find_ag_momentum = dict(sorted(find_ag_momentum.items(), key=lambda item: item[1], reverse=True))
        find_def_momentum = dict(sorted(find_def_momentum.items(), key=lambda item: item[1], reverse=True))
        asset_share = check_asset_share(find_ag_momentum, find_def_momentum)
        sub_data = pd.DataFrame(benchmark_data.loc[reb_period[index]:reb_period[index + 1]])
        backtest_result = do_backtest(initial_money, sub_data, asset_share, inv_share)
        initial_money = backtest_result['total_asset'][-1]
        total_backtest_result = pd.concat([total_backtest_result[:-1], backtest_result])

    return total_backtest_result


def calculate_momentum(benchmark_data, stocklist, period):
    momentum_result = {}
    current_day = benchmark_data.index[-1]
    base_day = current_day - relativedelta(months=period)
    sub_data = pd.DataFrame(
        benchmark_data.loc[base_day:current_day, stocklist])
    for name in sub_data.columns:
        rate = (sub_data.iloc[-1][name] / sub_data.iloc[0][name] - 1) * 100
        momentum_result[f'{name}'] = round(rate, 2)

    return momentum_result


def check_asset_share(find_ag_momentum, find_def_momentum):
    if list(find_ag_momentum.values())[0] > list(find_def_momentum.values())[0]:
        asset_share = {'VT': 0.5, 'VUSTX': 0.2,'IEF': 0.15, 'GSG': 0.075, 'GLD': 0.075}
    else:
        asset_share = {'VT': 0.1, 'VUSTX': 0.4,'IEF': 0.35, 'GSG': 0.075, 'GLD': 0.075}

    return asset_share


def do_backtest(initial_money, sub_data, asset_share, inv_share):
    inv_money = initial_money * inv_share
    backtest_result = pd.DataFrame(index=sub_data.index)
    backtest_result['invest_asset'] = 0

    for col in sub_data.columns:
        initial_buy = math.trunc(asset_share[col] * inv_money / sub_data[col][0])
        backtest_result['invest_asset'] = backtest_result['invest_asset'] + initial_buy * sub_data[col]
    backtest_result['cash_asset'] = initial_money - backtest_result['invest_asset'][0]
    backtest_result['total_asset'] = backtest_result['invest_asset'] + backtest_result['cash_asset']
    backtest_result['daily_return'] = backtest_result['total_asset'].pct_change() * 100

    return backtest_result


def calculate_cagr(total_backtest_result):
    year_period = total_backtest_result.index[-1].year - total_backtest_result.index[0].year
    month_period = (
        total_backtest_result.index[-1].month - total_backtest_result.index[0].month) / 12
    final_period = year_period + month_period

    CAGR = round(((total_backtest_result.iloc[-1]['total_asset'] / total_backtest_result.iloc[0]['total_asset']) ** (
        1 / final_period) - 1) * 100, 2)

    return CAGR


def calculate_mdd(total_backtest_result):
    max_value = np.maximum.accumulate(total_backtest_result['total_asset'])
    rate_value = (total_backtest_result['total_asset'] - max_value) / max_value
    mdd = round(rate_value.min() * 100, 2)

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


backtest_etf = ['VT', 'VUSTX', 'IEF', 'GSG', 'GLD']
benchmark_data = merge_file(backtest_etf)
ag_asset = ['VT']
def_asset = ['VUSTX', 'IEF']

start_date = benchmark_data.index[0] + relativedelta(months=12)
end_date = benchmark_data.index[-1]
reb_period = find_reb_period(benchmark_data, start_date, end_date, 6)

total_backtest_result = get_backtest_result(reb_period, benchmark_data, ag_asset, def_asset, 1, mom_set=6)

cagr = calculate_cagr(total_backtest_result)
mdd = calculate_mdd(total_backtest_result)
yr_rate = calculate_gr_byyear(total_backtest_result)
