import pandas as pd
import numpy as np
import glob
import os

class Preprocess():
    def __init__(self, path:str, tick:str):
        self.benzinga = None
        self.macro = None
        self.youtube = None
        self.tick = tick
        self.stock = None
        self.earning = None
        self.combination = None
        try:
            self.benzinga = pd.read_csv(os.path.join(path, 'benzinga_with_ratings.csv'))
        except FileNotFoundError:
            print('Benzinga file not found')
        try:
            self.macro = pd.read_csv(os.path.join(path, 'macro.csv'))
        except FileNotFoundError:
            print('Macro file not found')
        try:
            self.youtube = pd.read_csv(os.path.join(path, 'youtube_with_ratings.csv'))
        except FileNotFoundError:
            print('YouTube file not found')
        try:
            stock_file = glob.glob(os.path.join(path, f'{tick}_stock.csv'))[0]
            self.stock = pd.read_csv(stock_file)
        except IndexError:
            print(f'Stock file for {self.tick} not found')
        try:
            earning_file = glob.glob(os.path.join(path, f'{tick}_earnings.csv'))[0]
            self.earning = pd.read_csv(earning_file)
        except IndexError:
            print(f'Earning file for {self.tick} not found')
        

    def clean_benzinga(self):
        self.benzinga = self.benzinga[['created', 'benz_rate']]
        self.benzinga.dropna(subset=['benz_rate'], inplace=True)
        self.benzinga['benz_rate'] = self.benzinga['benz_rate'].astype(int)
        self.benzinga = self.benzinga.groupby('created')['benz_rate'].mean().reset_index()
        self.benzinga['benz_rate'] = self.benzinga['benz_rate'].round(4)
        self.benzinga = self.benzinga.rename(columns={'created': 'date'})
        self.benzinga['date'] = pd.to_datetime(self.benzinga['date']).dt.date
        print('Snapshot of benzinga data:')
        print(self.benzinga.head())
        print(f"Size:{self.benzinga.shape}")
    
    def clean_stock(self):
        exclude_cols = ['open', 'high', 'low','tic']
        self.stock = self.stock.drop(columns=exclude_cols)
        self.stock['date'] = pd.to_datetime(self.stock['date']).dt.date

        zero_rows = set(np.where(self.stock.iloc[:10, 4:20] == 0)[0].tolist())
        inf_rows = set(np.where(np.isinf(self.stock.iloc[:, 4:20]))[0].tolist())
        neg_inf_rows = set(np.where(np.isinf(self.stock.iloc[:, 4:20]) & (self.stock.iloc[:, 4:20] < 0))[0].tolist())
        nan_rows = set(np.where(np.isnan(self.stock.iloc[:, 4:20]))[0].tolist())
        invalid_rows = zero_rows.union(inf_rows).union(neg_inf_rows).union(nan_rows)
        print(invalid_rows)
        print()
        self.stock = self.stock.drop(list(invalid_rows)).reset_index(drop=True)

        print('Snapshot of stock data:')
        print(self.stock.head())
        print(f"Size:{self.stock.shape}")

    def clean_earning(self):
        if self.earning is not None:
            self.earning['reportedDate'] = pd.to_datetime(self.earning['reportedDate']).dt.date
            self.earning = self.earning[['reportedDate', 'reportedEPS', 'estimatedEPS', 'surprisePercentage']]
            self.earning = self.earning.rename(columns={'reportedDate': 'date', 'surprisePercentage' : 'surprisePct'})
            self.earning = self.earning.sort_values(by='date').reset_index(drop=True)
            print('Snapshot of earning data:')
            print(self.earning.head())
            print(f"Size:{self.earning.shape}")


    def clean_macro(self):
        new_dates_1 = pd.date_range(start='2023-04-01', end='2023-04-30')
        new_data_1 = {'date': new_dates_1, 'NFP' : 155673.0, 'InterestRate': 4.83, 'UnemploymentRate' : 3.4, 'PPI' : 257.381, 'CPI': 302.918}
        new_df_1 = pd.DataFrame(new_data_1)
        # # nfp, Unemployment Rate used a mock value, 
        # new_dates_2 = pd.date_range(start='2023-05-01', end='2023-05-04')
        # new_data_2 = {'date': new_dates_2, 'NFP' : 155873.0, 'InterestRate': 5.08, 'UnemploymentRate' : '3.4', 'PPI' : 257}
        # new_df_2 = pd.DataFrame(new_data_2)

        # # Concatenate the two DataFrames
        # new_df_12 = pd.concat([new_df_1, new_df_2], ignore_index=True)
        self.macro = pd.concat([self.macro, new_df_1], ignore_index=True)

        self.macro = self.macro[['date','NFP','InterestRate','UnemploymentRate','PPI','CPI']]
        self.macro['date'] = pd.to_datetime(self.macro['date']).dt.date
        print('Snapshot of macro data:')
        print(self.macro.head())
        print(f"Size:{self.macro.shape}")

    def merge_table(self):
        self.combination = pd.merge(self.stock, self.macro, on='date', how='left')
        self.combination = pd.merge(self.combination, self.benzinga, on='date', how='outer')
        self.combination = self.combination.sort_values(by='date').reset_index(drop=True)
        # Fill NA values using backward fill method for dates when market is closed
        columns_to_fill = [col for col in self.stock.columns if col not in ['date', 'benz_rate']]
        self.combination[columns_to_fill] = self.combination[columns_to_fill].fillna(method='bfill')
        # # Fill NA values using forward fill method for dates when no news created when market is open
        self.combination['benz_rate'] = self.combination['benz_rate'].fillna(method='ffill')
        self.combination['benz_rate'] = self.combination.groupby(['close', 'volume', 'day'])['benz_rate'].transform('mean')
        self.combination['benz_rate'] = self.combination['benz_rate'].round(3)
        if self.earning is not None:
            self.combination = pd.merge(self.combination, self.earning, on='date', how='outer')
        self.combination = self.combination.sort_values(by='date').reset_index(drop=True)    
        self.combination = self.combination.fillna(method='ffill')
        self.combination = self.combination[self.combination['date'].isin(self.stock['date'])].sort_values(by='date').reset_index(drop=True)

    def export_to_csv(self):
        self.combination.to_csv(f"../data/{self.tick}_cleaned_data.csv", index=False)


    # # this uncompleted function is used to merge tables based on user input
    # def merge_tables(self, table_list: list):
    #     for table in table_list:
    #         if hasattr(self, table):
    #             class_variable = getattr(self, table)
    #             if isinstance(class_variable, pd.DataFrame):
    #                 merged_dataframe = pd.concat([class_variable, class_variable], ignore_index=True)
    #                 setattr(self, table, merged_dataframe)