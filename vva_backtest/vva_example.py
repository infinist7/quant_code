# VVA 전략 구현

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


def find_rebalancing_period(data, start_date, end_date, byperiod):
    period_df = pd.DataFrame(data[start_date:end_date].index)
    select_date = period_df.loc[period_df.groupby(pd.Grouper(key='Date', freq=f'{byperiod}M')).Date.idxmax()]
    backtest_end_date = end_date + relativedelta(months=-1) + relativedelta(day=+40)
    rebalancing_day = [intime for intime in select_date['Date'] if intime <= backtest_end_date]

    return rebalancing_day


def get_backtest_result(rebalancing_period, benchmark_data, offensive_asset, defensive_asset, invest_share=1):
    initial_money = 1000
    total_backtest_result = pd.DataFrame()
    for index in range(len(rebalancing_period) - 1):
        vaa_momentum = calculate_vaa_momentum(benchmark_data[:rebalancing_period[index]])
        final_asset = check_condition(vaa_momentum, offensive_asset, defensive_asset)
        sub_benchmark_data = pd.DataFrame(
            benchmark_data.loc[rebalancing_period[index]:rebalancing_period[index + 1], final_asset])

        if index > 0 and save_asset != final_asset:
            initial_money = initial_money*0.9977
        else:
            pass
        save_asset = final_asset

        backtest_result = do_backtest(initial_money, sub_benchmark_data, invest_share)
        initial_money = backtest_result['total_asset'][-1]
        total_backtest_result = pd.concat([total_backtest_result[:-1], backtest_result])

    return total_backtest_result


def calculate_vaa_momentum(benchmark_data):
    vaa_momentum = {}
    monthlist = [1,3,6,12]
    current_day = benchmark_data.index[-1]
    for name in benchmark_data.columns:
        rate = 0
        for pr in monthlist:
            base_day = current_day - relativedelta(months=pr)
            sub_data = pd.DataFrame(benchmark_data.loc[base_day:current_day, name])
            rate += (sub_data.iloc[-1][name] / sub_data.iloc[0][name] - 1)*(12/pr)*100

        vaa_momentum[name] = rate

    return vaa_momentum


def check_condition(vaa_momentum, offensive_asset, defensive_asset):
    offensive_asset_m = {}
    defensive_asset_m = {}
    for name, momentum in vaa_momentum.items():
        if name in offensive_asset:
            offensive_asset_m[name] = momentum
        elif name in defensive_asset:
            defensive_asset_m[name] = momentum

    offensive_asset_m = dict(sorted(offensive_asset_m.items(), key=lambda item: item[1], reverse=True))
    defensive_asset_m = dict(sorted(defensive_asset_m.items(), key=lambda item: item[1], reverse=True))

    satisfied_asset_number = sum(x > 0 for x in offensive_asset_m.values())

    if len(offensive_asset) == satisfied_asset_number:
        final_asset = list(offensive_asset_m.keys())[0]
    else:
        final_asset = list(defensive_asset_m.keys())[0]

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


choice_asset = ['spy','vea','eem','agg','shy','ief','lqd']
offensive_asset = ['spy','vea','eem','agg']
defensive_asset = ['ief','shy','lqd']

benchmark_data = merge_file(choice_asset)

start_date = benchmark_data.index[0] + relativedelta(months=12)
end_date = benchmark_data.index[-1]

rebalancing_period = find_rebalancing_period(benchmark_data, start_date, end_date, 1)
total_backtest_result = get_backtest_result(rebalancing_period, benchmark_data, offensive_asset, defensive_asset)

cagr = calculate_cagr(total_backtest_result)
mdd = calculate_mdd(total_backtest_result)
