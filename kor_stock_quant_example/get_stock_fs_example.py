import OpenDartReader as odr
import FinanceDataReader as fdr
import pandas as pd

def get_stocklist():
    df_krstock_kospi = fdr.StockListing('KOSPI')
    df_krstock_kosdaq = fdr.StockListing('KOSDAQ')
    df_krstock = pd.concat([df_krstock_kospi, df_krstock_kosdaq])
    df_krstock.reset_index(inplace=True, drop=True)
    df_krstock.rename(columns = {'Code':'Symbol'}, inplace=True)
    return df_krstock


def get_finance_info(match_krstock, yr, report_code):
    stock_finance = pd.DataFrame()
    except_list = {'Name': []}
    for fname in match_krstock['Name']:
        try:
            corp_finance = dart_fn.finstate_all(fname, yr, report_code)
            corp_finance['Name'] = fname
            stock_finance = pd.concat([stock_finance, corp_finance])
        except:
            except_list['Name'].append(fname)

    stock_finance.reset_index(inplace=True, drop=True)
    return stock_finance, except_list


api_key = '발급받은 인증키를 여기 입력해주세요'
dart_fn = odr(api_key)

df_krstock = get_stocklist()
dart_list = dart_fn.corp_codes
dart_list.rename(columns = {'stock_code':'Symbol'}, inplace=True)
match_krstock = pd.merge(df_krstock, dart_list, on='Symbol', how='left')
match_krstock = match_krstock[match_krstock['corp_code'].isna()==False]

finance_df, except_list = get_finance_info(match_krstock[:5], '2023', '11013')

