## 시가총액을 marcap으로부터 뽑는 코드
import pandas as pd
import os
from datetime import datetime
from dateutil.relativedelta import *


def read_siga_frommarcap(base_day):
    date = base_day.strftime('%Y-%m-%d')
    stock_data1 = pd.read_csv(f'marcap-{base_day.year-1}.csv')
    stock_data2 = pd.read_csv(f'marcap-{base_day.year}.csv')
    stock_data = pd.concat([stock_data1, stock_data2])

    limit_num = 1
    while limit_num < 10:
        print(date)
        siga_data = stock_data[stock_data['Date']==date]
        if len(siga_data) != 0:
            break
        else:
            prev_date = base_day + relativedelta(days=-limit_num)
            date = prev_date.strftime('%Y-%m-%d')
            limit_num += 1

    siga_data.rename(columns = {'Code':'종목코드', 'Marcap':'시가총액'}, inplace=True)
    collist = list(siga_data.columns)
    collist.remove('종목코드')
    collist.remove('시가총액')
    collist = ['종목코드', '시가총액'] + collist
    siga_data  = siga_data[collist]
    siga_data.reset_index(inplace=True, drop=True)

    return siga_data

os.chdir(r'marcap 자료가 위치한 폴더를 입력해주세요')
base_day = datetime(2023, 10, 20)
siga_marcap = read_siga_frommarcap(base_day)
