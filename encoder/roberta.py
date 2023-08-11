import torch
from torch.utils.data import Dataset, DataLoader
from transformers import RobertaTokenizer, RobertaForSequenceClassification, AdamW
from transformers import Trainer, TrainingArguments
import pandas as pd
import numpy as np
from datetime import date
from sklearn.preprocessing import StandardScaler
import os

class RoBerta():
    def __init__(self, ticker, tokenizer, max_length):
        self.data = None
        self.ticker = ticker
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.days = 1

    # def __len__(self):
    #     return len(self.data)

    # def __getitem__(self, idx):
    #     example = self.data[idx]
    #     labels = self.labels[idx]

    #     encodings = []
    #     for column_data in example:
    #         if isinstance(column_data, str):
    #             encoding = self.tokenizer(column_data, padding='max_length', truncation=True, max_length=self.max_length, return_tensors='pt')
    #             encodings.append(encoding)

    #     input_ids = torch.cat([encoding['input_ids'] for encoding in encodings], dim=1)
    #     attention_mask = torch.cat([encoding['attention_mask'] for encoding in encodings], dim=1)

    #     label_tensor = torch.tensor(labels, dtype=torch.long)

    #     return {
    #         'input_ids': input_ids.squeeze(),
    #         'attention_mask': attention_mask.squeeze(),
    #         'labels': label_tensor
    #     }
    
    ############################################################

    def get_data(self):
        try:
            #os.chdir(os.getcwd())
            path = os.path.dirname(os.getcwd())
            self.data = pd.read_csv(f'{path}/data/{self.ticker}_cleaned_data.csv') 
            print(f'{self.ticker} data imported. Size: {self.data.shape}') 
        except FileNotFoundError:
            print(f'Error: File for {self.ticker} not found.')

        #self.data = pd.read_csv(f'../data/{self.ticker}_cleaned_data.csv')
        print(f'{self.ticker} size: {self.data.shape}')
        self.data_original = self.data.copy()

    ############################################################

    def preprocess(self):
        # Preprocess date column
        if self.data is None:
            self.get_data()

        self.data['Date'] = pd.to_datetime(self.data['date'])
        self.data.drop(['date'], axis=1, inplace=True)

        self.data['month_sin'] = np.sin(2*np.pi*self.data['Date'].dt.month/12)
        self.data['month_cos'] = np.cos(2*np.pi*self.data['Date'].dt.month/12)
        self.data['day_of_month_sin'] = np.sin(2*np.pi*self.data['Date'].dt.day/31)
        self.data['day_of_month_cos'] = np.cos(2*np.pi*self.data['Date'].dt.day/31)
        self.data['day_of_week_sin'] = np.sin(2*np.pi*self.data['day']/5)
        self.data['day_of_week_cos'] = np.cos(2*np.pi*self.data['day']/5)
        self.data = self.data.drop('day', axis=1)

        self.data['Year'] = self.data['Date'].dt.year
        self.data['Month'] = self.data['Date'].dt.month
        self.data['Day'] = self.data['Date'].dt.day

        self.data = pd.get_dummies(self.data, columns=['Month'])  # one-hot encode month column

        # set the 'date' column as the DataFrame's index
        self.data.set_index('Date', inplace=True)

        # lag the 'close_price' column by three months
        self.data['close_price_lagged'] = self.data['close'].shift(-self.days)

        # reset the index back to a column
        self.data.reset_index(inplace=True)

        # create new data as last three months of data
        self.new_data = self.data.iloc[-self.days:, :].copy().drop(['close_price_lagged'], axis=1)
        self.data_orig_final = self.data.copy()
        self.new_data_orig = self.new_data.copy()
        self.data = self.data[self.data['close_price_lagged'].isna()==False].copy()

        self.data = self.data.drop('Date', axis=1)
        self.new_data = self.new_data.drop('Date', axis=1)

        # scale data
        scaler = StandardScaler()
        self.data.iloc[:, 1:self.data.shape[1]-1] = scaler.fit_transform(self.data.iloc[:, 1:self.data.shape[1]-1])  # standardize year and day columns

        if self.days > 1:
            self.new_data.iloc[:, 1:self.new_data.shape[1]-1] = scaler.fit_transform(self.new_data.iloc[:, 1:self.new_data.shape[1]-1])

        self.X = self.data.drop('close_price_lagged', axis=1).values
        self.y = self.data['close_price_lagged'].values.reshape(-1, 1)
        self.new_data = self.new_data.values

        # reshape for LSTM
        #self.X = self.X.reshape(self.X.shape[0], 1, self.X.shape[1])  # reshape to 3D array
        return self.X, self.y, self.new_data