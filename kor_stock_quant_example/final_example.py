##### PER, PBR, PSR, PCR 기준 가치지표 투자 구현
### 실행하기 전, read_price_data 함수에서 첫 줄인 path에 marcap 자료가 들어간 폴더 경로를 입력해야 합니다.

from dateutil.relativedelta import *
from datetime import datetime
import math
import pandas as pd
import os
from glob import glob
from pykrx import stock

### 재무제표 정리 및 가치지표 계산 함수
def make_finance_df():
    filelist = glob("*사업보고서*.txt")
    yr_list = sorted(list(set([j[:4] for j in filelist])))
    fsdata_fin = pd.DataFrame(columns=['종목코드'])
    corpname = pd.DataFrame(columns=['종목코드', '회사명'])

    for yr in yr_list:
        fs_df = load_fsfile(filelist, yr)
        corpname = pd.concat([corpname, fs_df[['회사명', '종목코드']]])
        fsdart_df = match_dart_code(fs_df)
        fsdart_df_adj = adjust_file(fsdart_df)
        fsdart_df_adj_pivot = pivot_df(fsdart_df_adj, yr)
        fsdata_fin = pd.merge(fsdata_fin, fsdart_df_adj_pivot, on=['종목코드'], how='outer')

    corpname.drop_duplicates(subset=['종목코드'], keep='last', inplace=True)
    corpname.reset_index(drop=True, inplace=True)
    fsdata_fin = pd.merge(fsdata_fin, corpname, on='종목코드', how='left')
    collist = fsdata_fin.columns.tolist()
    fsdata_fin = fsdata_fin[collist[-1:] + collist[:-1]]

    return fsdata_fin


def load_fsfile(filelist, yr):
    con_df = pd.DataFrame()
    sol_df = pd.DataFrame()
    load_conlist = [j for j in filelist if yr in j[:4] and '연결' in j and '자본변동' not in j]
    load_sollist = [j for j in filelist if yr in j[:4] and '연결' not in j and '자본변동' not in j]

    for each_f in load_conlist:
        temp_df = pd.read_csv(f'{each_f}', sep="\t", encoding='cp949')
        con_df = pd.concat([con_df, temp_df])

    for each_f in load_sollist:
        temp_df = pd.read_csv(f'{each_f}', sep="\t", encoding='cp949')
        sol_df = pd.concat([sol_df, temp_df])

    con_corp = list(set(con_df['종목코드']))
    sol_corp = list(set(sol_df['종목코드']))
    only_sol_corp = [j for j in sol_corp if j not in con_corp]
    sol_df = sol_df[sol_df['종목코드'].isin(only_sol_corp)]

    fs_df = pd.concat([con_df, sol_df])
    fs_df.reset_index(drop=True, inplace=True)
    fs_df = fs_df[fs_df['항목명'].isna() == False]
    fs_df['항목명'] = fs_df['항목명'].apply(lambda x: x.strip())
    fs_df['종목코드'] = fs_df['종목코드'].apply(lambda x: x.replace('[', '').replace(']', ''))

    return fs_df


def match_dart_code(fs_df):
    fs_df['key_var'] = ''
    fs_df.loc[fs_df['항목코드'] == 'ifrs_ProfitLoss', 'key_var'] = '당기순이익'
    fs_df.loc[fs_df['항목코드'] == 'ifrs-full_ProfitLoss', 'key_var'] = '당기순이익'
    fs_df.loc[fs_df['항목코드'] == 'ifrs_Revenue', 'key_var'] = '매출액'
    fs_df.loc[fs_df['항목코드'] == 'ifrs-full_Revenue', 'key_var'] = '매출액'
    fs_df.loc[fs_df['항목코드'] == 'ifrs_Equity', 'key_var'] = '자본총계'
    fs_df.loc[fs_df['항목코드'] == 'ifrs-full_Equity', 'key_var'] = '자본총계'
    fs_df.loc[fs_df['항목코드'] == 'ifrs_CashFlowsFromUsedInOperatingActivities', 'key_var'] = '영업활동현금흐름'
    fs_df.loc[fs_df['항목코드'] == 'ifrs-full_CashFlowsFromUsedInOperatingActivities', 'key_var'] = '영업활동현금흐름'

    fs_df.loc[(fs_df['항목명'] == '당기순이익') & (fs_df['재무제표종류'].str.contains('손익계산서')), 'key_var'] = '당기순이익'
    fs_df.loc[fs_df['항목명'] == '매출액', 'key_var'] = '매출액'
    fs_df.loc[fs_df['항목명'] == '자본총계', 'key_var'] = '자본총계'
    fs_df.loc[fs_df['항목명'] == '영업활동현금흐름', 'key_var'] = '영업활동현금흐름'

    return fs_df

def adjust_file(fs_df):
    fs_df = fs_df.loc[fs_df['key_var'] != ""]
    fs_df = fs_df[fs_df['당기'].isna()==False]
    fs_df = fs_df.drop_duplicates(subset=['종목코드', '회사명', '시장구분', '업종', 'key_var'], keep='last')
    fs_df.reset_index(inplace=True, drop=True)

    return fs_df


def pivot_df(fs_df, yr):
    fs_df['key_var'] = fs_df['key_var'] + '_' + str(yr)
    fs_df['당기'] = fs_df['당기'].apply(lambda x: int(x.replace(',', '')))
    fs_pivotdf = fs_df.pivot_table(index=['종목코드'], columns='key_var', values='당기')
    fs_pivotdf.reset_index(inplace=True)
    fs_pivotdf.sort_values(by='종목코드', inplace=True)

    return fs_pivotdf

def change_colname(fs_df, base_yr):
    collist_dict = {}
    collist = list(fs_df.columns)

    collist_dict['이번기'] = [j for j in collist if str(base_yr) in j]
    for pyr in [1, 2, 3]:
        collist_dict[f'{pyr}년전동기'] = [j for j in collist if str(base_yr - pyr) in j]

    adj_cols = ['회사명', '종목코드']
    for each_col in collist_dict.values():
        print(each_col)
        adj_cols = adj_cols + each_col

    fs_df_adj = fs_df[adj_cols]

    for curc in collist_dict['이번기']:
        fs_df_adj.rename(columns={curc: curc.replace(f'_{base_yr}', '')}, inplace=True)
    for pyr in [1, 2, 3]:
        for prec in collist_dict[f'{pyr}년전동기']:
            fs_df_adj.rename(columns={prec: f'{pyr}년전동기' + prec.replace(f'_{base_yr - pyr}', '')}, inplace=True)

    return fs_df_adj

def get_cap(base_day):
    date = str(base_day.year) + str(base_day.month).zfill(2) + str(base_day.day).zfill(2)
    limit_num = 1
    while limit_num < 10:
        print(date)
        market_info = stock.get_market_cap(date)
        if market_info['종가'].sum() != 0:
            break
        else:
            prev_date = base_day + relativedelta(days=-limit_num)
            date = str(prev_date.year) + str(prev_date.month).zfill(2) + str(prev_date.day).zfill(2)
            limit_num += 1

    market_info.reset_index(inplace=True)
    market_info.rename(columns = {'티커':'종목코드', '상장주식수': 'Stocks'}, inplace=True)

    return market_info


def calculate_index(fs_df_adj_cap):
    fs_df_adj_cap['PER'] = 1 / (fs_df_adj_cap['시가총액'] / fs_df_adj_cap['당기순이익'])
    fs_df_adj_cap['PBR'] = 1 / (fs_df_adj_cap['시가총액'] / fs_df_adj_cap['자본총계'])
    fs_df_adj_cap['PSR'] = 1 / (fs_df_adj_cap['시가총액'] / fs_df_adj_cap['매출액'])
    fs_df_adj_cap['PCR'] = 1 / (fs_df_adj_cap['시가총액'] / fs_df_adj_cap['영업활동현금흐름'])

    fs_df_adj_cap['PER_rank'] = fs_df_adj_cap['PER'].rank(ascending=False)
    fs_df_adj_cap['PBR_rank'] = fs_df_adj_cap['PBR'].rank(ascending=False)
    fs_df_adj_cap['PSR_rank'] = fs_df_adj_cap['PSR'].rank(ascending=False)
    fs_df_adj_cap['PCR_rank'] = fs_df_adj_cap['PCR'].rank(ascending=False)

    # 순위 평균으로 계산
    fs_df_adj_cap['가치순위평균'] = fs_df_adj_cap[['PER_rank', 'PBR_rank', 'PSR_rank', 'PCR_rank']].mean(axis=1, skipna=False)
    fs_df_adj_cap['최종가치순위'] = fs_df_adj_cap['가치순위평균'].rank()
    fs_df_adj_cap.sort_values(by='최종가치순위', inplace=True)
    fs_df_adj_cap.reset_index(inplace=True, drop=True)

    return fs_df_adj_cap


### 리밸런싱 구현 함수
def backtest_stock_basic(rebalancing_period, num_stock, fs_df):
    initial_money = 100000000
    backtest_result = pd.DataFrame()
    for beginning_day, end_day in zip(rebalancing_period['beginning'], rebalancing_period['end']):
        print(beginning_day, end_day)
        fs_df_adj_cap = make_value_df(fs_df, beginning_day)
        invest_stock_list = {'회사명':fs_df_adj_cap['회사명'][:num_stock].values, '종목코드':fs_df_adj_cap['종목코드'][:num_stock].values}
        invest_price_data = get_satisfied_item(beginning_day, end_day, invest_stock_list['종목코드'])
        print(invest_stock_list['종목코드'])

        invest_price_data = invest_price_data[['Name','Code','adj_price']]
        amount_df = get_buy_quantity(invest_price_data, initial_money)

        invest_price_data = invest_price_data.reset_index().merge(amount_df, how='left', on='Code').set_index('Date')
        invest_price_data['total_amount'] = invest_price_data['buynum'] * invest_price_data['adj_price']

        invest_result_df, invest_stock_sum = collapse_and_make_portfolio(invest_price_data)
        # invest_result_df = invest_result_df[invest_result_df['buynum'] == invest_result_df['buynum'].iloc[0]]

        if invest_stock_sum['buynum'].min() != invest_stock_sum['buynum'].max():
            print('Some stocks fell')

        cash = initial_money - invest_result_df['total_amount'].iloc[0]
        invest_result_df['total_amount'] = invest_result_df['total_amount'] + cash

        backtest_result= pd.concat([backtest_result, invest_result_df])
        initial_money = backtest_result['total_amount'].iloc[-1]

    backtest_result['daily_return'] = backtest_result['total_amount'].pct_change()

    return backtest_result


def make_value_df(fs_df, beginning_day):
    market_info = get_cap(beginning_day)
    fs_df_adj = change_colname(fs_df, beginning_day.year - 1)
    fs_df_adj_cap = pd.merge(fs_df_adj, market_info[['종목코드', '시가총액']], on='종목코드', how='left')
    fs_df_adj_cap = calculate_index(fs_df_adj_cap)

    return fs_df_adj_cap


def get_satisfied_item(beginning_day, end_day, invest_code_list):
    price_data = read_price_data(beginning_day)
    invest_price_data =price_data[price_data['Code'].isin(invest_code_list)]
    adjusted_day = find_index_period(invest_price_data, beginning_day)


    check_first_day_list = invest_price_data.loc[adjusted_day]['Code']

    invest_price_data.sort_index(inplace=True)
    invest_price_data = invest_price_data[invest_price_data['Code'].isin(check_first_day_list)][adjusted_day:end_day]
    invest_price_data.sort_values(by=['Code','Date'], inplace=True)

    return invest_price_data

def read_price_data(rebalancing_day):
    path = r'marcap 자료가 있는 폴더를 입력해주세요' # marcap이 들어간 경로 입력
    price_data1 = pd.read_csv(f'{path}\\marcap-{rebalancing_day.year}.csv')
    price_data2 = pd.read_csv(f'{path}\\marcap-{rebalancing_day.year + 1}.csv')
    price_data = pd.concat([price_data1, price_data2])
    price_data = calculate_adj_price(price_data)
    price_data.index = pd.DatetimeIndex(price_data['Date'])
    price_data = price_data.drop(['Date'], axis=1)

    return price_data



def calculate_adj_price(price_data):
    price_data = price_data.sort_values(['Code','Date'], ascending=False)
    price_data['ChagesRatio'] = (1+(price_data['ChagesRatio']/100))
    price_data['cumratio'] = price_data.groupby(['Code'])['ChagesRatio'].cumprod()
    price_data['cumratio'] = price_data.groupby('Code')['cumratio'].shift()
    price_data.loc[price_data['cumratio'].isna()==True, 'cumratio'] = 1
    first_close = price_data[['Code', 'Close']].groupby(by='Code').first()
    first_close.rename(columns = {'Close':'first_price'}, inplace=True)
    price_data = price_data.merge(first_close, how='left', on='Code')
    price_data['adj_price'] = round(price_data['first_price']/price_data['cumratio'])

    price_data = price_data.sort_values(['Code', 'Date'])
    del(price_data['first_price'], price_data['cumratio'])

    return price_data

def find_index_period(invest_price_data, beginning_day):
    if beginning_day in invest_price_data.index:
        selected_day = beginning_day

    elif beginning_day not in invest_price_data.index:
        while beginning_day not in invest_price_data.index:
            beginning_day = beginning_day + relativedelta(days=+1)
        selected_day = beginning_day

    return selected_day


def get_buy_quantity(invest_price_data, initial_money):
    adjusted_day = invest_price_data.index[0]
    numcode = len(invest_price_data['Code'].unique())
    each_money = round(initial_money / numcode)

    amount_dict = {}
    if numcode > 1:
        for stockcode, stockprice in zip(invest_price_data['Code'][adjusted_day], invest_price_data['adj_price'][adjusted_day]):
            amount_dict[stockcode] = math.trunc(each_money / stockprice)
    elif numcode == 1:
        amount_dict[invest_price_data['Code'][adjusted_day]] = math.trunc(each_money / invest_price_data['adj_price'][adjusted_day])
    amount_df = pd.DataFrame.from_dict(amount_dict, orient='index')
    amount_df.rename(columns={0: 'buynum'}, inplace=True)
    amount_df.reset_index(inplace=True)
    amount_df.rename(columns={'index':'Code'}, inplace=True)

    return amount_df


def collapse_and_make_portfolio(invest_price_data):
    asset_calculate = invest_price_data[['buynum', 'total_amount']].groupby(invest_price_data.index).sum()
    asset_number = invest_price_data[['buynum', 'total_amount']].groupby(invest_price_data.index).count()

    return asset_calculate, asset_number


def get_rebalancing_period(backtest_list, start_month, period):
    rebalancing_day = {}
    rebalancing_day['beginning'] = []
    rebalancing_day['end'] = []

    beginning_day = datetime(backtest_list[0], start_month, 1)
    end_day = beginning_day + relativedelta(months=period) - relativedelta(days=1)

    while end_day < datetime(backtest_list[-1]+1, 1, 1):
        rebalancing_day['beginning'].append(beginning_day)
        rebalancing_day['end'].append(end_day)
        beginning_day = beginning_day + relativedelta(months=period)
        end_day = beginning_day + relativedelta(months=period) - relativedelta(days=1)

    return rebalancing_day


os.chdir(r'재무제표를 다운받은 폴더를 입력해주세요')
backtest_list = [2017, 2024]
rebalancing_period = get_rebalancing_period(backtest_list, 4, 12)
num_stock = 20

fs_df = make_finance_df()
backtest_result = backtest_stock_basic(rebalancing_period, num_stock, fs_df)

