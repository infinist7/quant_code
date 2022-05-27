# 패키지 설치 코드
# pip install pandas-datareader
# pip install finance-datareader
# 이미 설치되어 있는 상황에서 에러가 발생하는 경우 버전업이 필요

# pip install pandas-datareader --upgrade
# pip install finance-datareader --upgrade

from pandas_datareader import data as pdr
from FinanceDataReader import DataReader as fdr

#1. 자료 읽어오기
# pandas_datareader를 사용하여 시계열 가격 자료 읽어오기(as pbr)
world_stock = pdr.get_data_yahoo('VT','1/1/1990')
longterm_bond = pdr.get_data_yahoo('VUSTX', '1/1/1990')
midterm_bond = pdr.get_data_yahoo('IEF', '1/1/1990')
commodity = pdr.get_data_yahoo('GSG', '1/1/1990')
gold = pdr.get_data_yahoo('GLD','1/1/1990')

# FinanceDataReader를 사용하여 시계열 가격 자료 읽어오기(as fdr)
# world_stock = fdr('VT', '1990-01-01')
# longterm_bond = fdr('VUSTX','1990-01-01')
# midterm_bond = fdr('IEF', '1990-01-01')
# commodity = fdr('GSG', '1990-01-01')
# gold = fdr('GLD', '1990-01-01')

