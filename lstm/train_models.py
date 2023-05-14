from lstm.lstm import Lstm
import os
import sys
sys.path.append(os.path.abspath('..'))
# print(os.getcwd())
from etl.api_etl.yahoofinance import *

from etl.api_etl.alphavantage import *
from data.preprocess.preprocess import *
import json

tickers = ['SPY', 'QQQ', '^DJI', # these are 3 main sections: sp500 etf, nasdaq top 100 eft and Dow Jones index
           'AAPL', 'GOOG', 'AMZN', 'MSFT', 'NVDA']

with open("../api-keys.json", "r") as f:
    api_keys = json.load(f)
    print(f"Found keys for {', '.join(api_keys.keys())}")

fromdate = "2018-05-01"
todate = "2023-05-04"

for ticker in tickers: 
    # ---------------------------uncomment the following block to download and preprocess the data------------------------------
    # yahoo = Yahoo([ticker], api_keys, fromdate, todate)
    # yahoo.fetch_data()
    # yahoo.add_technical_indicators()
    # yahoo.add_vix()
    # yahoo.add_bond()
    # yahoo.export_as_csv()

    # alpha = Alphavantage(api_keys)
    # alpha.fetch_earning_data(ticker)

    merger = Preprocess('../data/', ticker)
    merger.clean_benzinga()
    merger.clean_stock()
    merger.clean_macro()
    merger.clean_earning()
    merger.merge_table()
    merger.export_to_csv()
    #----------------------------------------------------------------------------------------------------------------------------
    lstm = Lstm(ticker)
    lstm.get_data()
    # lstm.train_lstm()
    # print(f"LSTM trained for {ticker}")
