import requests
import csv
from etl.api_etl.etl import ETL

class Alphavantage(ETL):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def fetch_earning_data(self, ticker:str):
        # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
        url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={self.api_keys["Alphavantage"]}'
        r = requests.get(url)
        data = r.json()

        # Check if the 'quarterlyEarnings' key exists in the response
        if 'quarterlyEarnings' in data:
            earnings = data['quarterlyEarnings']

            # Specify the output CSV file path
            output_file = f'../data/{ticker}_earnings.csv'

            # Open the output file in write mode
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write the header row
                writer.writerow(earnings[0].keys())

                # Write the data rows
                for earnings_data in earnings:
                    writer.writerow(earnings_data.values())

            print(f"Data has been successfully converted and saved to '{output_file}'.")
        else:
            print("No earnings data found in the response.")