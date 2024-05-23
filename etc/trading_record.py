from pykrx import stock
from datetime import datetime
import pandas as pd
import numpy as np

path = r'매매일지 엑셀파일이 있는 경로를 지정해주세요'
stock_list = ['005930', '035760'] ## 투자한 종목 티커

result_df = pd.read_excel(f'{path}', index_col=0, dtype={'티커':str})

date = datetime.today().strftime("%Y%m%d")
stock_df = stock.get_market_ohlcv(date, market='ALL')

stock_name = [stock.get_market_ticker_name(j) for j in stock_list]
invest_df = df.loc[stock_list]
invest_df['종목명'] = stock_name
invest_df['날짜'] = date
invest_df.reset_index(inplace=True)
invest_df['거래대금'] = round(invest_df['거래대금'] / 1000000, 0)
invest_df['등락률'] = invest_df['등락률'].apply(lambda x: np.floor(x*100)/100)

invest_df = invest_df[['티커','종목명','날짜','종가', '거래량','거래대금','등락률']]

result_df = pd.concat([result_df, invest_df])

result_df.to_excel(f'{path}', index=False)