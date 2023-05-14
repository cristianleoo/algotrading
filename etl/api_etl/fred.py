from fredapi import Fred
from api_etl.etl import ETL

class Fredapi(ETL):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indices = ["PAYEMS", "FEDFUNDS", "UNRATE", "PPIACO", "CPIAUCSL",
                        "PCE", "INDPRO", "UMCSENT", "RSAFS", "HOUST", "CSUSHPINSA"],

    def fetch_macro_data(self):
        fred = Fred(api_key=self.api_keys["Fred"])
        dfs = []

        # Mapping of series IDs to their actual names
        names = {
            "PAYEMS": "NFP", # Non-Farm Payrolls
            "CPIAUCSL": "CPI", # Consumer Price Index
            "FEDFUNDS": "InterestRate", # Effective Federal Funds Rate
            "UNRATE": "UnemploymentRate",
            "PPIACO": "PPI", # Producer Price Index
            "PCE": "PCE", # Personal Consumption Expenditures
            "INDPRO": "IPI", # Industrial Production Index
            "UMCSENT": "ConsumerSentiment",
            "RSAFS": "RetailSales",
            "HOUST": "HousingStarts",
            "CSUSHPINSA": "HPI", # S&P/Case-Shiller U.S. National Home Price Index
        }

        for index in self.indices[0]: # Note: self.indices is a tuple with a single list
            series = fred.get_series(index, self.start_day, self.end_day)
            series = series.resample("D").ffill().reset_index()
            series.columns = ["date", index]
            dfs.append(series)

        # Merge all dataframes on 'date'
        macro_df = dfs[0]
        for df in dfs[1:]:
            macro_df = macro_df.merge(df, on='date', how='outer')

        # Rename the columns
        macro_df.rename(columns=names, inplace=True)

        macro_df = macro_df.round(4)
        macro_df.to_csv('../data/macro.csv', index=False)
        print('macro.csv created')
        return macro_df
