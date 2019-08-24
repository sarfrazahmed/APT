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

def start(name, date, interval):
    print("Connecting to Kite...")
    config = configparser.ConfigParser()
    config_path = 'D:/APT/APT/Paper_Trading/config.ini'
    config.read(config_path)
    path = 'D:/DevAPT/APT/Simulation'
    os.chdir(path)

    api_key = config['API']['API_KEY']
    api_secret = config['API']['API_SECRET']
    username = config['USER']['USERNAME']
    password = config['USER']['PASSWORD']
    pin = config['USER']['PIN']
    homepage = 'https://kite.zerodha.com/'

    ## Selenium for ubuntu
    # chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # driver = webdriver.Chrome(chrome_options=chrome_options)
    # page = driver.get(homepage)

    driver = webdriver.Chrome(executable_path='D:/DevAPT/APT/chromedriver.exe')
    page = driver.get(homepage)

    print("Authenticating...")
    # Logging in using Username and Password
    user_id_box = driver.find_element_by_xpath(
        '//*[@id="container"]/div/div/div/form/div[2]/input')
    password_box = driver.find_element_by_xpath(
        '//*[@id="container"]/div/div/div/form/div[3]/input')
    log_in_button = driver.find_element_by_xpath(
        '//*[@id="container"]/div/div/div/form/div[4]/button')
    user_id_box.send_keys(username)
    password_box.send_keys(password)
    log_in_button.click()
    time.sleep(3)

    # Logging in using Pin
    pin_box = driver.find_element_by_xpath(
        '//*[@id="container"]/div/div/div/form/div[2]/div/input')
    continue_box = driver.find_element_by_xpath(
        '//*[@id="container"]/div/div/div/form/div[3]/button')
    pin_box.send_keys(pin)
    continue_box.click()
    time.sleep(3)

    # Redirecting to Kiteconnect
    kite = KiteConnect(api_key=api_key)
    url = kite.login_url()
    page = driver.get(url)
    current_url = driver.current_url
    request_token = re.search(('request_token=(.*)'), current_url).group(1)[:32]
    KRT = kite.generate_session(request_token, api_secret)
    kite.set_access_token(KRT['access_token'])
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
        single_candle.to_csv('ohlc_data_' + name +'.csv')
        time.sleep(60)

if __name__ == '__main__':
    name = sys.argv[1]
    date = sys.argv[2]
    # name = 'LT'
    # date = '2019-08-21'
    interval = '5minute'
    start(name, date, interval)