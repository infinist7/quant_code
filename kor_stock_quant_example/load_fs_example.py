import pandas as pd
import os
from glob import glob

def make_finance_df():
    filelist = glob("*사업보고서*.txt")
    yr_list = sorted(list(set([j[:4] for j in filelist])))
    fsdata_fin = pd.DataFrame(columns=['종목코드'])
    corpname = pd.DataFrame(columns=['종목코드', '회사명'])

    for yr in yr_list:
        fs_df = load_fsfile(filelist, yr)
        corpname = pd.concat([corpname, fs_df[['회사명', '종목코드']]])  # 마지막 년도 값이 덧붙여질 것임.
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


os.chdir(r'재무제표를 다운받은 폴더를 입력해주세요')
fs_df = make_finance_df()