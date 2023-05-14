from __future__ import annotations
from etl.api_etl.etl import ETL
import exchange_calendars as tc
import datetime
from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytz
import yfinance as yf
from stockstats import StockDataFrame as Sdf

class Yahoo(ETL):
    """Provides methods for retrieving daily stock data from
    Yahoo Finance API
    Attributes
    ----------
        start_date : str
            start date of the data (modified from neofinrl_config.py)
        end_date : str
            end date of the data (modified from neofinrl_config.py)
        ticker_list : list
            a list of stock tickers (modified from neofinrl_config.py)

    Methods
    -------
    fetch_data()
        Fetches data from yahoo API
    """

    def __init__(self, ticker_list: list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticker_list = ticker_list
        self.df = pd.DataFrame()

    # def __init__(self, start_date: str, end_date: str, ticker_list: list):
    #     self.start_day = start_date
    #     self.end_day = end_date
    #     self.ticker_list = ticker_list
    #     self.df = pd.DataFrame()
    
    def fetch_data(self, proxy=None) -> pd.DataFrame:
        """Fetches data from Yahoo API
        Parameters
        ----------

        Returns
        -------
        `pd.DataFrame`
            7 columns: A date, open, high, low, close, volume and tick symbol
            for the specified stock ticker
        """
        # Download and save the data in a pandas DataFrame:
        data_df = pd.DataFrame()
        num_failures = 0
        for tic in self.ticker_list:
            temp_df = yf.download(
                tic, start=self.start_day, end=self.end_day, proxy=proxy
            )
            temp_df["tic"] = tic
            if len(temp_df) > 0:
                # data_df = data_df.append(temp_df)
                data_df = pd.concat([data_df, temp_df], axis=0)
            else:
                num_failures += 1
        if num_failures == len(self.ticker_list):
            raise ValueError("no data is fetched.")
        # reset the index, we want to use numbers as index instead of dates
        data_df = data_df.reset_index()
        try:
            # convert the column names to standardized names
            data_df.columns = [
                "date",
                "open",
                "high",
                "low",
                "close",
                "adjcp",
                "volume",
                "tic",
            ]
            # use adjusted close price instead of close price
            data_df["close"] = data_df["adjcp"]
            # drop the adjusted close price column
            data_df = data_df.drop(labels="adjcp", axis=1)
        except NotImplementedError:
            print("the features are not supported currently")
        # create day of the week column (monday = 0)
        data_df["day"] = data_df["date"].dt.dayofweek
        # convert date to standard string format, easy to filter
        data_df["date"] = data_df.date.apply(lambda x: x.strftime("%Y-%m-%d"))
        # drop missing data
        data_df = data_df.dropna()
        data_df = data_df.reset_index(drop=True)
        print("Shape of DataFrame: ", data_df.shape)
        
        data_df = data_df.sort_values(by=["date", "tic"]).reset_index(drop=True)
        self.df = data_df
        return data_df

    def add_vix(self):
        vix_ticker = "^VIX"
        vix_data = yf.download(vix_ticker, start=self.start_day, end=self.end_day)
        vix_data = vix_data.reset_index()
        vix_data = vix_data[["Date", "Close"]]
        vix_data.columns = ["date", "vix"]
        vix_data["date"] = vix_data.date.apply(lambda x: x.strftime("%Y-%m-%d"))

        # Merge the original data frame with the VIX data frame
        merged_df = pd.merge(self.df, vix_data, on="date", how="left")
        merged_df["vix"] = merged_df["vix"].fillna(method='ffill')
        self.df = merged_df
        return merged_df

    def add_technical_indicators(self):
        stock_df = Sdf.retype(self.df)
        # Add MACD
        stock_df['macd'] = stock_df.get('macd')
        # Add KDJ
        stock_df['kdjk'] = stock_df.get('kdjk')
        stock_df['kdjd'] = stock_df.get('kdjd')
        stock_df['kdjj'] = stock_df.get('kdjj')
        # Add RSI
        stock_df['rsi'] = stock_df.get('rsi_14')
        # Add moving averages
        stock_df['ma50'] = stock_df.get('close_50_sma')
        stock_df['ma200'] = stock_df.get('close_200_sma')
        self.df = stock_df

        return stock_df

    def add_bond(self):
        etfs = ["TLT", "IEF", "SHY"]
        etf_data = None

        for etf in etfs:
            temp_data = yf.download(etf, start=self.start_day, end=self.end_day)["Close"]
            temp_data = temp_data.reset_index().rename(columns={"Date": "date", "Close": etf})

            if etf_data is None:
                etf_data = temp_data
            else:
                etf_data = pd.merge(etf_data, temp_data, on="date", how="left")

        self.df["date"] = pd.to_datetime(self.df["date"])
        merged_df = pd.merge(self.df, etf_data, on="date", how="left")
        merged_df = merged_df.fillna(method='ffill')
        self.df = merged_df
        return merged_df

    def export_as_csv(self):
        # # select only the useful columns
        # useful_columns = [
        #     "date", "open", "high", "low", "close", "volume", "tic",
        #     "day", "macd", "kdjk", "kdjd", "kdjj", "rsi", "ma50", "ma200"
        # ]
        # data_df = data_df[useful_columns]

        # round the value to 3 decimal places
        exclude_columns = ['date', 'tic']
        self.df.loc[:, ~self.df.columns.isin(exclude_columns)] = self.df.loc[:, ~self.df.columns.isin(exclude_columns)].round(3)
        if len(self.ticker_list) > 1:
            self.df.to_csv('stock_price.csv', index=False)
        else:
            self.df.to_csv(f'../data/{self.ticker_list[0]}_stock.csv', index=False)
            print(f"{self.ticker_list[0]}_stock.csv created!")


'''
class YahooFinance:
    """Provides methods for retrieving daily stock data from
    Yahoo Finance API
    """

    def __init__(self):
        pass

    """
    Param
    ----------
        start_date : str
            start date of the data
        end_date : str
            end date of the data
        ticker_list : list
            a list of stock tickers
    Example
    -------
    input:
    ticker_list = config_tickers.DOW_30_TICKER
    start_date = '2009-01-01'
    end_date = '2021-10-31'
    time_interval == "1D"

    output:
        date	    tic	    open	    high	    low	        close	    volume
    0	2009-01-02	AAPL	3.067143	3.251429	3.041429	2.767330	746015200.0
    1	2009-01-02	AMGN	58.590000	59.080002	57.750000	44.523766	6547900.0
    2	2009-01-02	AXP	    18.570000	19.520000	18.400000	15.477426	10955700.0
    3	2009-01-02	BA	    42.799999	45.560001	42.779999	33.941093	7010200.0
    ...
    """

    def convert_interval(self, time_interval: str) -> str:
        # Convert FinRL 'standardised' time periods to Yahoo format: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        if time_interval in [
            "1Min",
            "2Min",
            "5Min",
            "15Min",
            "30Min",
            "60Min",
            "90Min",
        ]:
            time_interval = time_interval.replace("Min", "m")
        elif time_interval in ["1H", "1D", "5D"]:
            time_interval = time_interval.lower()
        elif time_interval == "1W":
            time_interval = "1wk"
        elif time_interval in ["1M", "3M"]:
            time_interval = time_interval.replace("M", "mo")
        else:
            raise ValueError("wrong time_interval")

        return time_interval

    def download_data(
        self,
        ticker_list: list[str],
        start_date: str,
        end_date: str,
        time_interval: str,
        proxy: str | dict = None,
    ) -> pd.DataFrame:
        time_interval = self.convert_interval(time_interval)

        self.start = start_date
        self.end = end_date
        self.time_interval = time_interval

        # Download and save the data in a pandas DataFrame
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        delta = timedelta(days=1)
        data_df = pd.DataFrame()
        for tic in ticker_list:
            while (
                start_date <= end_date
            ):  # downloading daily to workaround yfinance only allowing  max 7 calendar (not trading) days of 1 min data per single download
                temp_df = yf.download(
                    tic,
                    start=start_date,
                    end=start_date + delta,
                    interval=self.time_interval,
                    proxy=proxy,
                )
                temp_df["tic"] = tic
                data_df = pd.concat([data_df, temp_df])
                start_date += delta

        data_df = data_df.reset_index().drop(columns=["Adj Close"])
        # convert the column names to match processor_alpaca.py as far as poss
        data_df.columns = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "tic",
        ]

        return data_df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        tic_list = np.unique(df.tic.values)
        NY = "America/New_York"

        trading_days = self.get_trading_days(start=self.start, end=self.end)
        # produce full timestamp index
        if self.time_interval == "1d":
            times = trading_days
        elif self.time_interval == "1m":
            times = []
            for day in trading_days:
                #                NY = "America/New_York"
                current_time = pd.Timestamp(day + " 09:30:00").tz_localize(NY)
                for i in range(390):  # 390 minutes in trading day
                    times.append(current_time)
                    current_time += pd.Timedelta(minutes=1)
        else:
            raise ValueError(
                "Data clean at given time interval is not supported for YahooFinance data."
            )

        # create a new dataframe with full timestamp series
        new_df = pd.DataFrame()
        for tic in tic_list:
            tmp_df = pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"], index=times
            )
            tic_df = df[
                df.tic == tic
            ]  # extract just the rows from downloaded data relating to this tic
            for i in range(tic_df.shape[0]):  # fill empty DataFrame using original data
                tmp_df.loc[tic_df.iloc[i]["timestamp"].tz_localize(NY)] = tic_df.iloc[
                    i
                ][["open", "high", "low", "close", "volume"]]
            # print("(9) tmp_df\n", tmp_df.to_string()) # print ALL dataframe to check for missing rows from download

            # if close on start date is NaN, fill data with first valid close
            # and set volume to 0.
            if str(tmp_df.iloc[0]["close"]) == "nan":
                print("NaN data on start date, fill using first valid data.")
                for i in range(tmp_df.shape[0]):
                    if str(tmp_df.iloc[i]["close"]) != "nan":
                        first_valid_close = tmp_df.iloc[i]["close"]
                        tmp_df.iloc[0] = [
                            first_valid_close,
                            first_valid_close,
                            first_valid_close,
                            first_valid_close,
                            0.0,
                        ]
                        break

            # if the close price of the first row is still NaN (All the prices are NaN in this case)
            if str(tmp_df.iloc[0]["close"]) == "nan":
                print(
                    "Missing data for ticker: ",
                    tic,
                    " . The prices are all NaN. Fill with 0.",
                )
                tmp_df.iloc[0] = [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ]

            # fill NaN data with previous close and set volume to 0.
            for i in range(tmp_df.shape[0]):
                if str(tmp_df.iloc[i]["close"]) == "nan":
                    previous_close = tmp_df.iloc[i - 1]["close"]
                    if str(previous_close) == "nan":
                        raise ValueError
                    tmp_df.iloc[i] = [
                        previous_close,
                        previous_close,
                        previous_close,
                        previous_close,
                        0.0,
                    ]
                    # print(tmp_df.iloc[i], " Filled NaN data with previous close and set volume to 0. ticker: ", tic)

            # merge single ticker data to new DataFrame
            tmp_df = tmp_df.astype(float)
            tmp_df["tic"] = tic
            new_df = pd.concat([new_df, tmp_df])

        #            print(("Data clean for ") + tic + (" is finished."))

        # reset index and rename columns
        new_df = new_df.reset_index()
        new_df = new_df.rename(columns={"index": "timestamp"})

        #        print("Data clean all finished!")

        return new_df

    def add_technical_indicator(
        self, data: pd.DataFrame, tech_indicator_list: list[str]
    ):
        """
        calculate technical indicators
        use stockstats package to add technical inidactors
        :param data: (df) pandas dataframe
        :return: (df) pandas dataframe
        """
        df = data.copy()
        df = df.sort_values(by=["tic", "timestamp"])
        stock = Sdf.retype(df.copy())
        unique_ticker = stock.tic.unique()

        for indicator in tech_indicator_list:
            indicator_df = pd.DataFrame()
            for i in range(len(unique_ticker)):
                try:
                    temp_indicator = stock[stock.tic == unique_ticker[i]][indicator]
                    temp_indicator = pd.DataFrame(temp_indicator)
                    temp_indicator["tic"] = unique_ticker[i]
                    temp_indicator["timestamp"] = df[df.tic == unique_ticker[i]][
                        "timestamp"
                    ].to_list()
                    indicator_df = pd.concat(
                        [indicator_df, temp_indicator], ignore_index=True
                    )
                except Exception as e:
                    print(e)
            df = df.merge(
                indicator_df[["tic", "timestamp", indicator]],
                on=["tic", "timestamp"],
                how="left",
            )
        df = df.sort_values(by=["timestamp", "tic"])
        return df

    def calculate_turbulence(
        self, data: pd.DataFrame, time_period: int = 252
    ) -> pd.DataFrame:
        # can add other market assets
        df = data.copy()
        df_price_pivot = df.pivot(index="timestamp", columns="tic", values="close")
        # use returns to calculate turbulence
        df_price_pivot = df_price_pivot.pct_change()

        unique_date = df.timestamp.unique()
        # start after a fixed timestamp period
        start = time_period
        turbulence_index = [0] * start
        # turbulence_index = [0]
        count = 0
        for i in range(start, len(unique_date)):
            current_price = df_price_pivot[df_price_pivot.index == unique_date[i]]
            # use one year rolling window to calcualte covariance
            hist_price = df_price_pivot[
                (df_price_pivot.index < unique_date[i])
                & (df_price_pivot.index >= unique_date[i - time_period])
            ]
            # Drop tickers which has number missing values more than the "oldest" ticker
            filtered_hist_price = hist_price.iloc[
                hist_price.isna().sum().min() :
            ].dropna(axis=1)

            cov_temp = filtered_hist_price.cov()
            current_temp = current_price[[x for x in filtered_hist_price]] - np.mean(
                filtered_hist_price, axis=0
            )
            temp = current_temp.values.dot(np.linalg.pinv(cov_temp)).dot(
                current_temp.values.T
            )
            if temp > 0:
                count += 1
                if count > 2:
                    turbulence_temp = temp[0][0]
                else:
                    # avoid large outlier because of the calculation just begins
                    turbulence_temp = 0
            else:
                turbulence_temp = 0
            turbulence_index.append(turbulence_temp)

        turbulence_index = pd.DataFrame(
            {"timestamp": df_price_pivot.index, "turbulence": turbulence_index}
        )
        return turbulence_index

    def add_turbulence(
        self, data: pd.DataFrame, time_period: int = 252
    ) -> pd.DataFrame:
        """
        add turbulence index from a precalcualted dataframe
        :param data: (df) pandas dataframe
        :return: (df) pandas dataframe
        """
        df = data.copy()
        turbulence_index = self.calculate_turbulence(df, time_period=time_period)
        df = df.merge(turbulence_index, on="timestamp")
        df = df.sort_values(["timestamp", "tic"]).reset_index(drop=True)
        return df

    def df_to_array(
        self, df: pd.DataFrame, tech_indicator_list: list[str], if_vix: bool
    ) -> list[np.ndarray]:
        df = df.copy()
        unique_ticker = df.tic.unique()
        if_first_time = True
        for tic in unique_ticker:
            if if_first_time:
                price_array = df[df.tic == tic][["close"]].values
                tech_array = df[df.tic == tic][tech_indicator_list].values
                if if_vix:
                    turbulence_array = df[df.tic == tic]["VIXY"].values
                else:
                    turbulence_array = df[df.tic == tic]["turbulence"].values
                if_first_time = False
            else:
                price_array = np.hstack(
                    [price_array, df[df.tic == tic][["close"]].values]
                )
                tech_array = np.hstack(
                    [tech_array, df[df.tic == tic][tech_indicator_list].values]
                )
        #        print("Successfully transformed into array")
        return price_array, tech_array, turbulence_array

    def get_trading_days(self, start: str, end: str) -> list[str]:
        nyse = tc.get_calendar("NYSE")
        df = nyse.sessions_in_range(
            pd.Timestamp(start, tz=pytz.UTC), pd.Timestamp(end, tz=pytz.UTC)
        )
        trading_days = []
        for day in df:
            trading_days.append(str(day)[:10])

        return trading_days

    # ****** NB: YAHOO FINANCE DATA MAY BE IN REAL-TIME OR DELAYED BY 15 MINUTES OR MORE, DEPENDING ON THE EXCHANGE ******
    def fetch_latest_data(
        self,
        ticker_list: list[str],
        time_interval: str,
        tech_indicator_list: list[str],
        limit: int = 100,
    ) -> pd.DataFrame:
        time_interval = self.convert_interval(time_interval)

        end_datetime = datetime.datetime.now()
        start_datetime = end_datetime - datetime.timedelta(
            minutes=limit + 1
        )  # get the last rows up to limit

        data_df = pd.DataFrame()
        for tic in ticker_list:
            barset = yf.download(
                tic, start_datetime, end_datetime, interval=time_interval
            )  # use start and end datetime to simulate the limit parameter
            barset["tic"] = tic
            data_df = pd.concat([data_df, barset])

        data_df = data_df.reset_index().drop(
            columns=["Adj Close"]
        )  # Alpaca data does not have 'Adj Close'

        data_df.columns = [  # convert to Alpaca column names lowercase
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "tic",
        ]

        start_time = data_df.timestamp.min()
        end_time = data_df.timestamp.max()
        times = []
        current_time = start_time
        end = end_time + pd.Timedelta(minutes=1)
        while current_time != end:
            times.append(current_time)
            current_time += pd.Timedelta(minutes=1)

        df = data_df.copy()
        new_df = pd.DataFrame()
        for tic in ticker_list:
            tmp_df = pd.DataFrame(
                columns=["open", "high", "low", "close", "volume"], index=times
            )
            tic_df = df[df.tic == tic]
            for i in range(tic_df.shape[0]):
                tmp_df.loc[tic_df.iloc[i]["timestamp"]] = tic_df.iloc[i][
                    ["open", "high", "low", "close", "volume"]
                ]

                if str(tmp_df.iloc[0]["close"]) == "nan":
                    for i in range(tmp_df.shape[0]):
                        if str(tmp_df.iloc[i]["close"]) != "nan":
                            first_valid_close = tmp_df.iloc[i]["close"]
                            tmp_df.iloc[0] = [
                                first_valid_close,
                                first_valid_close,
                                first_valid_close,
                                first_valid_close,
                                0.0,
                            ]
                            break
                if str(tmp_df.iloc[0]["close"]) == "nan":
                    print(
                        "Missing data for ticker: ",
                        tic,
                        " . The prices are all NaN. Fill with 0.",
                    )
                    tmp_df.iloc[0] = [
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    ]

            for i in range(tmp_df.shape[0]):
                if str(tmp_df.iloc[i]["close"]) == "nan":
                    previous_close = tmp_df.iloc[i - 1]["close"]
                    if str(previous_close) == "nan":
                        previous_close = 0.0
                    tmp_df.iloc[i] = [
                        previous_close,
                        previous_close,
                        previous_close,
                        previous_close,
                        0.0,
                    ]
            tmp_df = tmp_df.astype(float)
            tmp_df["tic"] = tic
            new_df = pd.concat([new_df, tmp_df])

        new_df = new_df.reset_index()
        new_df = new_df.rename(columns={"index": "timestamp"})

        df = self.add_technical_indicator(new_df, tech_indicator_list)
        df["VIXY"] = 0

        price_array, tech_array, turbulence_array = self.df_to_array(
            df, tech_indicator_list, if_vix=True
        )
        latest_price = price_array[-1]
        latest_tech = tech_array[-1]
        start_datetime = end_datetime - datetime.timedelta(minutes=1)
        turb_df = yf.download("VIXY", start_datetime, limit=1)
        latest_turb = turb_df["Close"].values
        return latest_price, latest_tech, latest_turb
'''