# 듀얼모멘텀 구현 예제
# 주식 2개(미국(SPY), 전세계(VT))와 채권 2개(미국중기채(IEF), 미국단기채(VFISX)) 활용.
# 지정한 기간의 모멘텀(수익률) 기준으로 주식 2개의 모멘텀이 0보다 크면 그 중 모멘텀이 가장 높은 것을 선택하여 투자.
# 만약 두 자산 모두 모멘텀이 0보다 낮은 경우 채권 2개에 반반씩 배분하는 방식.


from pandas_datareader import data as pdr
import pandas as pd
from dateutil.relativedelta import *
import math
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt



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


def find_rebalancing_period(data, start_date, end_date, byperiod):
    period_df = pd.DataFrame(data[start_date:end_date].index)
    select_date = period_df.loc[period_df.groupby(pd.Grouper(key='Date', freq=f'{byperiod}M')).Date.idxmax()]
    backtest_end_date = end_date + relativedelta(months=-1) + relativedelta(day=+40)
    rebalancing_day = [intime for intime in select_date['Date'] if intime <= backtest_end_date]

    return rebalancing_day



def get_backtest_result(rebalancing_period, benchmark_data, aggressive_asset, defensive_asset, invest_share=1, mom_set=6):
    initial_money = 1000
    total_backtest_result = pd.DataFrame()

    for index in range(len(rebalancing_period) - 1):
        find_aggressive_momentum = calculate_momentum(benchmark_data[:rebalancing_period[index]], aggressive_asset, mom_set)
        find_aggressive_momentum = dict(
            sorted(find_aggressive_momentum.items(), key=lambda item: item[1], reverse=True))
        final_asset = check_condition(find_aggressive_momentum, defensive_asset)

        sub_benchmark_data = pd.DataFrame(
            benchmark_data.loc[rebalancing_period[index]:rebalancing_period[index + 1], final_asset])
        backtest_result = do_backtest(initial_money, sub_benchmark_data, invest_share)
        initial_money = backtest_result['total_asset'][-1]
        total_backtest_result = pd.concat([total_backtest_result[:-1], backtest_result])

    return total_backtest_result


def calculate_momentum(benchmark_data, stocklist, period):
    momentum_result = {}
    current_day = benchmark_data.index[-1]
    base_day = current_day - relativedelta(months=period)
    sub_data = pd.DataFrame(benchmark_data.loc[base_day:current_day, stocklist])
    for name in sub_data.columns:
        rate = (sub_data.iloc[-1][name] / sub_data.iloc[0][name] - 1) * 100
        momentum_result[f'{name}'] = round(rate, 2)

    return momentum_result


def check_condition(find_aggressive_momentum, defensive_asset):
    satisfied_asset_list = []
    for name, momentum in find_aggressive_momentum.items():
        if momentum > 0:
            satisfied_asset_list.append(name)

    if satisfied_asset_list:
        final_asset = satisfied_asset_list[0]

    else:
        final_asset = defensive_asset

    return final_asset


def do_backtest(initial_money, sub_benchmark_data, invest_share):
    invest_money = initial_money * invest_share
    backtest_result = pd.DataFrame(index=sub_benchmark_data.index)
    backtest_result['invest_asset'] = 0

    for col in sub_benchmark_data.columns:
        each_money = invest_money / len(sub_benchmark_data.columns)
        initial_buy = math.trunc(each_money / sub_benchmark_data[col][0])
        backtest_result['invest_asset'] = backtest_result['invest_asset'] + initial_buy * sub_benchmark_data[col]
    backtest_result['cash_asset'] = initial_money - backtest_result['invest_asset'][0]
    backtest_result['total_asset'] = backtest_result['invest_asset'] + backtest_result['cash_asset']
    backtest_result['daily_return'] = backtest_result['total_asset'].pct_change() * 100

    return backtest_result


def calculate_cagr(total_backtest_result):
    year_period = total_backtest_result.index[-1].year - total_backtest_result.index[0].year
    month_period = (total_backtest_result.index[-1].month - total_backtest_result.index[0].month) / 12
    final_period = year_period + month_period

    CAGR = round(((total_backtest_result.iloc[-1]['total_asset'] / total_backtest_result.iloc[0]['total_asset']) ** (
            1 / final_period) - 1) * 100,2)

    return CAGR


def calculate_mdd(total_backtest_result):
    max_value = np.maximum.accumulate(total_backtest_result['total_asset'])
    rate_value = (total_backtest_result['total_asset'] - max_value) / max_value
    mdd = round(rate_value.min() * 100, 2)

    return mdd


backtest_etf = ['SPY', 'EFA', 'IEF', 'VFISX']
aggressive_asset = ['SPY', 'EFA']
defensive_asset = ['IEF', 'VFISX']
benchmark_data = merge_file(backtest_etf)

start_date = benchmark_data.index[0] + relativedelta(months=12)
end_date = benchmark_data.index[-1]

result_dict = {'type': [], 'CAGR': [], 'MDD': []}

rebalancing_set = [1,3,6,12]
momentum_time_set = [1,3,6,12]

for reb_set in rebalancing_set:
    for mom_set in momentum_time_set:
        rebalancing_period = find_rebalancing_period(benchmark_data, start_date, end_date, reb_set)
        total_backtest_result = get_backtest_result(rebalancing_period, benchmark_data, aggressive_asset,
                                                    defensive_asset, 1, mom_set)

        cagr = calculate_cagr(total_backtest_result)
        mdd = calculate_mdd(total_backtest_result)
        result_dict['type'].append(f'R:{reb_set}/M:{mom_set}')
        result_dict['CAGR'].append(cagr)
        result_dict['MDD'].append(mdd)

result_df = pd.DataFrame.from_dict(result_dict)

result_df.plot.bar(x='type', y='CAGR', rot=0)
result_df.plot.bar(x='type', y='MDD', rot=0, color='red')



