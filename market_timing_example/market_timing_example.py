# import quantstats as qs

## 마켓타이밍 관련 코드

from pandas_datareader import data
import numpy as np

def calculate_mdd(pct_result):
    pct_result = pct_result.dropna()
    max_value = np.maximum.accumulate(pct_result)
    rate_value = (pct_result - max_value) / max_value

    return np.min(rate_value)


# 마켓타이밍 계산
kospi = data.get_data_yahoo('^KS11', '1997/01/01')
kospi.rename(columns={'Adj Close': 'kospi'}, inplace=True)
kospi = kospi[['kospi']]
kospi['kospi60'] = kospi['kospi'].rolling(window=60).mean()

kospi['kospi_lag'] = kospi[['kospi']].shift(1)
kospi['kospi60_lag'] = kospi[['kospi60']].shift(1)

kospi['pct'] = kospi['kospi'].pct_change()

kospi['adj_pct'] = kospi['pct']
kospi.loc[kospi['kospi_lag'] < kospi['kospi60_lag'], 'adj_pct'] = 0


# CAGR, MDD 계산
year_period = kospi.index[-1].year - kospi.index[0].year
month_period = (kospi.index[-1].month - kospi.index[0].month) / 12
final_period = year_period + month_period

kospi['cumpct'] = (1 + kospi['pct']).cumprod()
kospi['adj_cumpct'] = (1 + kospi['adj_pct']).cumprod()

cagr = ((kospi.iloc[-1]['cumpct']) ** (1 / final_period) - 1) * 100
adj_cagr = ((kospi.iloc[-1]['adj_cumpct']) ** (1 / final_period) - 1) * 100

mdd = calculate_mdd(kospi['cumpct']) * 100
adj_mdd = calculate_mdd(kospi['adj_cumpct']) * 100