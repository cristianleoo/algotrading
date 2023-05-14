from api_etl.etl import ETL
from benzinga_tool import financial_data,news_data
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import json
import datetime

# inherit from ETL class
class Benzinga(ETL):
    def __init__(self, ticker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticker = ticker

    # helper function to clean the text
    def clean_text(self, text):
        # Remove HTML tags using Beautiful Soup
        soup = BeautifulSoup(text, 'html.parser')
        clean_text = soup.get_text().replace('\n', ' ').replace('"', '').replace('\u2028', ' ').replace('\u2029', ' ').replace('\r', ' ')
        return ' '.join(clean_text.split())

    # clean the response data
    def process_stories(self, stories):
        df = pd.DataFrame(stories)[['created', 'title', 'body']]
        df['created'] = pd.to_datetime(df['created'], errors='coerce')
        df['title'] = df['title'].apply(lambda x: x.replace('"', ''))
        df['body'] = df['body'].apply(self.clean_text)
        df = df.dropna(subset=['created', 'title', 'body'])
        df['created'] = df['created'].dt.date
        return df

    # make requests to Benzinga API
    def benzinga_call(self, news, ticker, fromdate, todate):
        stories = news.news(display_output='full', company_tickers=ticker, pagesize=100, date_from=fromdate, date_to=todate)
        df = self.process_stories(stories)

        fromdate = (df.iloc[-1, 0] - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        one_month_be4_todate = (datetime.datetime.strptime(todate, '%Y-%m-%d') - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
        last_request_fromdate = None
        while fromdate < one_month_be4_todate:
            if last_request_fromdate is not None and fromdate <= last_request_fromdate:
                fromdate = (datetime.datetime.strptime(last_request_fromdate, '%Y-%m-%d') + datetime.timedelta(days=15)).strftime('%Y-%m-%d')
                continue

            stories = news.news(display_output='full', company_tickers=ticker, pagesize=100, date_from=fromdate, date_to=todate)
            stories_df = self.process_stories(stories)
            df = pd.concat([df, stories_df]).drop_duplicates(subset=['title']).reset_index(drop=True)
            last_request_fromdate = fromdate
            fromdate = (df.iloc[-1, 0] - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        return df

    # call Benzinga API to get one ticker data
    def get(self):
       news = news_data.News(self.api_keys['Benzinga'])
       df = self.benzinga_call(news, self.ticker, self.start_day, self.end_day)
       return df
    
    # batch call Benzinga API to get all tickers data from a list
    def pull_batch_benzinga(api_keys, tick_list, start_day, end_day):
        df_list = []
        for ticker in tick_list:
            news = Benzinga(api_keys = api_keys, ticker = ticker, start_day = start_day, end_day = end_day)
            df_list.append( news.get() )
        df = pd.concat(df_list, axis=0)
        df = df.sort_values(by='created')
        df = df.drop_duplicates(subset=['created', 'title'], keep='first')
        df.to_csv('../data/benzinga.csv', index=False)