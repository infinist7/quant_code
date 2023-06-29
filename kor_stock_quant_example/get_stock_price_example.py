import pandas as pd
import FinanceDataReader as fdr
from pykrx import stock
import time
from datetime import datetime
from dateutil.relativedelta import *


def get_stockprice_frompykrx(last_date, base_date, market):
    last_date_str = last_date.strftime("%Y%m%d")
    base_date_str = base_date.strftime("%Y%m%d")
    market = market.upper()
    stock_df = pd.DataFrame()

    while last_date >= base_date:
        print(base_date)
        info_df = stock.get_market_ohlcv(base_date_str, market=market)

        if info_df['시가'].sum() != 0:
            info_df['date'] = base_date
            stock_df = pd.concat([info_df, stock_df])
            base_date = base_date+relativedelta(days=1)
            base_date_str = base_date.strftime("%Y%m%d")
            time.sleep(3)
        else:
            base_date = base_date+relativedelta(days=1)
            base_date_str = base_date.strftime("%Y%m%d")

    return stock_df


def get_stockname_frompykrx(stock_df_pykrx):
    name_dict = {}
    for ticker in stock_df_pykrx.index:
        stock_name = stock.get_market_ticker_name(ticker)
        print(stock_name)
        time.sleep(2)
        name_dict[ticker] = [stock_name]

    name_df = pd.DataFrame.from_dict(name_dict, orient='index', columns=['name'])
    return name_df



def get_price_fromfdr(last_date, base_date, stock_full_fdr):
    last_date_str = last_date.strftime("%Y-%m-%d")
    base_date_str = base_date.strftime("%Y-%m-%d")
    stock_df = pd.DataFrame()

    for symbol, name in zip(stock_full_fdr['Symbol'], stock_full_fdr['Name']):
        info_df = fdr.DataReader(symbol, base_date_str, last_date_str)
        if len(info_df) > 0 :
            info_df['Symbol'] = symbol
            info_df['Name'] = name
            print(symbol, name)
            stock_df = pd.concat([stock_df, info_df])
            time.sleep(2)
        else:
            print('no information')
            break

    return stock_df


today = datetime.today()
base_date = datetime(2023, 6, 10)

#1. pykrx
stock_kospi_pykrx = get_stockprice_frompykrx(today, base_date, 'KOSPI')
stock_kosdaq_pykrx = get_stockprice_frompykrx(today, base_date, 'KOSDAQ')
stock_df_pykrx = pd.concat([stock_kospi_pykrx, stock_kosdaq_pykrx])

name_df = get_stockname_frompykrx(stock_df_pykrx[:10])

stock_df_pykrx = pd.merge(stock_df_pykrx, name_df, left_index=True, right_index=True, how='left')
stock_df_pykrx= stock_df_pykrx.reset_index().rename(columns={'index':'Symbol'})
stock_df_pykrx.set_index(['date'], inplace=True)
stock_df_pykrx.sort_values(by=['name', 'date'], inplace=True)


#2. fdr
stock_list_kospi_fdr = fdr.StockListing('KOSPI')
stock_list_kosdaq_fdr = fdr.StockListing('KOSDAQ')
stock_list_full_fdr = pd.concat([stock_list_kospi_fdr, stock_list_kosdaq_fdr])
stock_list_full_fdr.reset_index(inplace=True, drop=True)

stock_df_fdr = get_price_fromfdr(today, base_date, stock_list_full_fdr[:10])