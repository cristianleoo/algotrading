from lstm import lstm

tickers = ['MSFT', 'JNJ', 'INTC', 'BA', 'UNH', 
            'JPM', 'V', 'PG', 'HD', 'CVX', 
            'MRK', 'KO', 'CSCO', 'MCD','WMT', 
            'CRM', 'DIS', 'VZ', 'NKE', 'AAPL', 
            'IBM', 'GS', 'HON', 'AXP', 'AMGN']


for ticker in tickers:
    lstm = lstm(ticker)
    lstm.train_lstm()
    print(f"LSTM trained for {ticker}")