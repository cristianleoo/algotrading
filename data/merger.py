from preprocess.preprocess import *
import pandas as pd


if __name__ == "__main__":
    merger = Preprocess('./','SPY')
    
    merger.clean_benzinga()
    merger.clean_stock()
    merger.clean_macro()
    merger.clean_earning()
    merger.merge_table()
    merger.export_to_csv()