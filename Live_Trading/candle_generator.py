# Import dependencies
import logging
from kiteconnect import KiteTicker
from kiteconnect import KiteConnect
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import datetime
from datetime import date, timedelta
import configparser
import time
import re
import sys

def start(name, date, access_token, interval):
    # print("Starting Trading Engine...", flush=True)
    config = configparser.ConfigParser()
    # path = os.getcwd()
    path = '/home/ubuntu/APT/APT/Live_Trading'
    config_path = path + '/config.ini'
    config.read(config_path)
    api_key = config['API']['API_KEY']

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    os.chdir(path)
    print("Connection Successful")

    scrip_dict = {
        'ADANIPORTS': '3861249',
        'ASIANPAINT': '60417',
        'AXISBANK': '1510401',
        'BAJAJ-AUTO': '4267265',
        'BAJFINANCE': '81153',
        'BAJAJFINSV': '4268801',
        'BPCL': '134657',
        'BHARTIARTL': '2714625',
        'INFRATEL': '7458561',
        'BRITANNIA': '140033',
        'CIPLA': '177665',
        'COALINDIA': '5215745',
        'DRREDDY': '225537',
        'EICHERMOT': '232961',
        'GAIL': '1207553',
        'GRASIM': '315393',
        'HCLTECH': '1850625',
        'HDFCBANK': '341249',
        'HEROMOTOCO': '345089',
        'HINDALCO': '348929',
        'HINDUNILVR': '356865',
        'HDFC': '340481',
        'ICICIBANK': '1270529',
        'ITC': '424961',
        'IBULHSGFIN': '7712001',
        'IOC': '415745',
        'INDUSINDBK': '1346049',
        'INFY': '408065',
        'JSWSTEEL': '3001089',
        'KOTAKBANK': '492033',
        'LT': '2939649',
        'M&M': '519937',
        'MARUTI': '2815745',
        'NTPC': '2977281',
        'ONGC': '633601',
        'POWERGRID': '3834113',
        'SBIN': '779521',
        'SUNPHARMA': '857857',
        'TCS': '2953217',
        'TATAMOTORS': '884737',
        'TATASTEEL': '895745',
        'TECHM': '3465729',
        'TITAN': '897537',
        'UPL': '2889473',
        'ULTRACEMCO': '2952193',
        'VEDL': '784129',
        'WIPRO': '969473',
        'YESBANK': '3050241',
        'ZEEL': '975873',
        'RELIANCE': '738561'
    }

    def prev_weekday(adate):
        adate -= timedelta(days=1)
        while adate.weekday() > 4:
            adate -= timedelta(days=1)
        return adate
    prev_date = prev_weekday(datetime.datetime.strptime(date, "%Y-%m-%d").date())
    data = kite.historical_data(instrument_token=int(scrip_dict[name]), from_date=date, to_date=date, interval=interval)
    data = pd.DataFrame(data)

    prev_day_data = kite.historical_data(instrument_token=int(scrip_dict[name]), from_date=prev_date, to_date=prev_date, interval='day')
    prev_day_data = pd.DataFrame(prev_day_data)
    prev_day_data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    prev_day_data.to_csv("previous_day_data_" + name + '.csv')


    for i in range(len(data)):
        single_candle = data.iloc[[i]]
        single_candle.to_csv('ohlc_data_' + name +'.csv',index= False)
        print(single_candle, flush= True)
        time.sleep(60)

if __name__ == '__main__':
    name = sys.argv[1]
    date = '2019-10-15'
    access_token = sys.argv[2]
    # name = 'LT'
    # date = '2019-08-08'
    interval = '5minute'
    start(name, date, access_token, interval)
