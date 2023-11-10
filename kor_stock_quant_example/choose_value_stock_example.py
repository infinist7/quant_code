import pandas as pd
import os
from glob import glob
from datetime import datetime
from pykrx import stock
from dateutil.relativedelta import *


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

    fs_df_adj_cap['가치순위평균'] = fs_df_adj_cap[['PER_rank', 'PBR_rank', 'PSR_rank', 'PCR_rank']].mean(axis=1, skipna=False)
    fs_df_adj_cap['최종가치순위'] = fs_df_adj_cap['가치순위평균'].rank()
    fs_df_adj_cap.sort_values(by='최종가치순위', inplace=True)
    fs_df_adj_cap.reset_index(inplace=True, drop=True)

    return fs_df_adj_cap


os.chdir(r'재무제표를 다운받은 폴더를 입력해주세요')
fs_df = make_finance_df()
base_day = datetime(2023, 11, 2)
market_info = get_cap(base_day)
fs_df_adj = change_colname(fs_df, base_day.year-1)
fs_df_adj_cap = pd.merge(fs_df_adj, market_info[['종목코드','시가총액']], on='종목코드', how='left')

fs_df_final = calculate_index(fs_df_adj_cap)