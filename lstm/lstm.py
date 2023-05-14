# uncomment to install the required libraries
import os
import sys
sys.path.append(os.path.abspath('..'))
from impo import impo
impo.imp_inst.import_or_install('pandas')
impo.imp_inst.import_or_install('scikit-learn')
impo.imp_inst.import_or_install('numpy')
impo.imp_inst.import_or_install('tensorflow')
impo.imp_inst.import_or_install('keras')
impo.imp_inst.import_or_install('matplotlib')
impo.imp_inst.import_or_install('plotly')

import pandas as pd
from datetime import date
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.models import load_model
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.graph_objs as go


class Lstm(): 
    def __init__(self, ticker: str, range: int):
        self.ticker = ticker
        self.range = int(range)
        self.days = int(range*30)
        self.data = None
        self.data_original = None
        self.new_data = None
        self.dat_orig_final = None
        self.new_data_orig_final = None
        self.X = None
        self.y = None
        self.X_train = None
        self.y_train = None
        self.X_val = None
        self.y_val = None
        self.X_test = None
        self.y_test = None
        self.split_idx = None
        self.split_idx_val = None
        self.model = None
        self.x_pred  = None
        self.y_pred = None
        self.new_pred = None
        self.preds_train = None
        self.preds_test = None
        self.new_preds = None
        print('\nlstm intance initialized')
    
    ############################################################

    def get_data(self):
        try:
            #os.chdir(os.getcwd())
            self.data = pd.read_csv(f'data/{self.ticker}_cleaned_data.csv')
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
        self.new_data = self.data[self.data['close_price_lagged'].isna()==True].copy().drop(['close_price_lagged'], axis=1)
        self.data_orig_final = self.data.copy()
        self.new_data_orig = self.new_data.copy()
        self.data = self.data[self.data['close_price_lagged'].isna()==False].copy()

        self.data = self.data.drop('Date', axis=1)
        self.new_data = self.new_data.drop('Date', axis=1)

        # scale data
        scaler = StandardScaler()
        self.data.iloc[:, 1:self.data.shape[1]-1] = scaler.fit_transform(self.data.iloc[:, 1:self.data.shape[1]-1])  # standardize year and day columns
        self.new_data.iloc[:, 1:self.new_data.shape[1]-1] = scaler.fit_transform(self.new_data.iloc[:, 1:self.new_data.shape[1]-1])

        self.X = self.data.drop('close_price_lagged', axis=1).values
        self.y = self.data['close_price_lagged'].values.reshape(-1, 1)
        self.new_data = self.new_data.values

        # reshape for LSTM
        self.X = self.X.reshape(self.X.shape[0], 1, self.X.shape[1])  # reshape to 3D array

    ############################################################

    def train_lstm(self, idx=0.8, layers=6, lr=0.01, early_stopping=200, epochs=2000, save="On"):
        if self.X is None:
            self.preprocess()

        # Split the data into training and testing sets
        self.split_idx = int(len(self.X) * idx)
        self.X_train, self.X_test = self.X[:self.split_idx], self.X[self.split_idx:]
        self.y_train, self.y_test = self.y[:self.split_idx], self.y[self.split_idx:]

        # Split train into train and val test
        self.split_idx_val = int(len(self.X_train) * idx)
        self.X_train, self.X_val = self.X_train[:self.split_idx_val], self.X_train[self.split_idx_val:]
        self.y_train, self.y_val = self.y_train[:self.split_idx_val], self.y_train[self.split_idx_val:]

        # Define the LSTM model
        model = Sequential()
        model.add(LSTM(50, activation='relu', return_sequences=True, input_shape=(1, self.X.shape[2])))
        for n in range(layers-1):
            model.add(LSTM(20, activation='relu', return_sequences=True))
        model.add(LSTM(20, activation='relu', return_sequences=False))
        model.add(Dropout(0.1))
        model.add(Dense(20, activation='relu'))
        model.add(Dense(1))

        # Compile the model with an appropriate learning rate and metric
        opt = Adam(learning_rate=lr)
        model.compile(optimizer=opt, loss='mean_absolute_error', metrics=['mae'])

        # Define early stopping criteria
        early_stopping = EarlyStopping(monitor='val_mae', patience=early_stopping, mode='min', verbose=1)

        # Train the model with early stopping
        history = model.fit(self.X_train, self.y_train, 
                            epochs=epochs, 
                            verbose=1, 
                            validation_data=(self.X_val, self.y_val), 
                            callbacks=[early_stopping])

        # Use the best model for predictions
        train_pred = model.predict(self.X_train)
        val_pred = model.predict(self.X_val)
        test_pred = model.predict(self.X_test)

        # Calculate the MAE
        mae = np.mean(np.abs(test_pred - self.y_test))

        # Print the MAE
        print("MAE: ", mae)

        self.train_pred = [x[0] for x in train_pred]
        self.val_pred = [x[0] for x in val_pred]
        self.test_pred = [x[0] for x in test_pred]

        # Save the model
        if save=="On":
            model.save(f"lstm/models/best_model_{self.ticker}.h5")
            #ModelCheckpoint(f"best_model_{self.ticker}.h5", monitor='val_mae', mode='min', save_best_only=True)
            self.model = load_model(f"lstm/models/best_model_{self.ticker}.h5")
        else:
            self.model = model

    ############################################################

    def plot_train(self):
        if self.model is None:
            self.train_lstm()
        
        self.preds_train = pd.DataFrame({
            'Date': self.data_orig_final['Date'][:self.split_idx_val]+ pd.DateOffset(days=self.days),
            'Predictions': self.train_pred,
            'Observed': self.data_orig_final['close_price_lagged'][:self.split_idx_val]
        })

        self.preds_train.to_csv(f'train_pred_{self.ticker}.csv')

        fig, ax = plt.subplots(figsize=(12,8))
        plt.title('Train Predictions')
        ax.plot('Date', 'Predictions', data=self.preds_train, label='Predictions')
        ax.plot('Date', 'Observed', data=self.preds_train, label='Observed', linewidth=0.5) # set alpha to 0.5 for the Observed line
        plt.xticks(rotation=60)
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=3))
        ax.legend()
        plt.show()

    ############################################################

    def plot_val(self):
        if self.model is None:
            self.train_lstm()
        
        self.preds_val = pd.DataFrame({
            'Date': self.data_orig_final['Date'][self.split_idx_val:self.split_idx] + pd.DateOffset(days=self.days),
            'Predictions': self.val_pred,
            'Observed': self.data_orig_final['close_price_lagged'][self.split_idx_val:self.split_idx]
        })

        self.preds_val.to_csv(f'val_pred_{self.ticker}.csv')

        fig, ax = plt.subplots(figsize=(12,8))
        plt.title('Train Predictions')
        ax.plot('Date', 'Predictions', data=self.preds_val, label='Predictions')
        ax.plot('Date', 'Observed', data=self.preds_val, label='Observed', linewidth=0.5) # set alpha to 0.5 for the Observed line
        plt.xticks(rotation=60)
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=3))
        ax.legend()
        plt.show()

    ############################################################

    def plot_test(self):
        if self.model is None:
            self.train_lstm()

        self.preds_test = pd.DataFrame({
            'Date': self.data_orig_final['Date'][self.split_idx:self.data_orig_final.shape[0]-self.days] + pd.DateOffset(days=self.days),
            'Predictions': self.test_pred,
            'Observed': self.data_orig_final['close_price_lagged'][self.split_idx:self.data_orig_final.shape[0]-self.days]
            })

        self.preds_test.to_csv(f'test_pred_{self.ticker}.csv')

        fig, ax = plt.subplots(figsize=(12,8))
        plt.title('Test Predictions')
        ax.plot('Date', 'Predictions', data=self.preds_test, label='Predictions')
        ax.plot('Date', 'Observed', data=self.preds_test, label='Observed', linewidth=0.5) # set alpha to 0.5 for the Observed line
        plt.xticks(rotation=60)
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        ax.legend()
        plt.show()

    ############################################################

    def predict(self):
        if self.model is None:
            try:
                self.model = load_model(f"lstm/models/best_model_{self.ticker}.h5")
                self.get_data()
                self.preprocess()

            except Exception:
                self.train_lstm()

        #Reshape X to match LSTM input shape
        self.new_data = self.new_data.reshape((self.new_data.shape[0], 1, self.new_data.shape[1]))
        self.new_pred = self.model.predict(self.new_data)
        self.new_pred = [x[0] for x in self.new_pred]

    ############################################################

    def plot_preds(self):
        if self.new_pred is None:
            self.predict()

        self.new_preds = pd.DataFrame({
            'Date': self.new_data_orig['Date'],
            'Predictions': self.new_pred
        })

        self.new_preds.to_csv(f'new_preds_{self.ticker}.csv')

        fig, ax = plt.subplots(figsize=(12,8))
        plt.title(f'Next {self.range} Months Predictions')
        ax.plot('Date', 'Predictions', data=self.new_preds, label='Predictions')
        plt.xticks(rotation=60)
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        ax.legend()
        fig.savefig(f'static/img/{self.ticker}.png')
        plt.show()

    ############################################################

    def plot_all(self):
        if self.new_pred is None:
            self.predict()

        date_new = pd.concat([self.data_orig_final['Date'], self.new_data['close_price_lagged']], axis=0)
        len_zeros = int(len(date_new)-len(self.data_orig_final['close_price_lagged']))
        observed_new = pd.concat([self.data_orig_final['close_price_lagged'], pd.Series(np.zeros(len_zeros))], axis=0)
        predictions_new = pd.concat([self.preds_train['Predictions'], self.preds_test['Predictions'], self.new_preds['Predictions']])

        predictions_concat = pd.DataFrame({
            'Date': date_new,
            'Observed': observed_new,
            'Predictions': predictions_new
        })


        # Create a trace for the observed values
        trace_observed = go.Scatter(x=predictions_concat['Date'], y=predictions_concat['Observed'], name='Observed')

        # Create a trace for the predictions
        trace_predictions = go.Scatter(x=predictions_concat['Date'], y=predictions_concat['Predictions'], name='Predictions')

        # Create a layout for the graph
        layout = go.Layout(
            title=f'Next {self.range} Months Predictions',
            xaxis=dict(title='Date', tickangle=60),
            yaxis=dict(title='Values'),
        )

        # Create a figure and add the traces and layout
        fig = go.Figure(data=[trace_observed, trace_predictions], layout=layout)

        # Show the graph
        fig.show()