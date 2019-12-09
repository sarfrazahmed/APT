# Import dependencies
import logging
from kiteconnect import KiteTicker
from kiteconnect import KiteConnect
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import datetime
import configparser
import time
import re

print("Connecting to Kite...")
config = configparser.ConfigParser()
config_path = 'F:/DevAPT/APT/Data_Fetch/config.ini'
config.read(config_path)
path = 'F:\DevAPT\APT'
os.chdir(path)

api_key = config['API']['API_KEY']
api_secret = config['API']['API_SECRET']
username = config['USER']['USERNAME']
password = config['USER']['PASSWORD']
pin = config['USER']['PIN']
homepage = 'https://kite.zerodha.com/'

## Selenium for ubuntu
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)
time.sleep(5)


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
time.sleep(5)

# Logging in using Pin
pin_box = driver.find_element_by_xpath(
    '//*[@id="container"]/div/div/div/form/div[2]/div/input')
continue_box = driver.find_element_by_xpath(
    '//*[@id="container"]/div/div/div/form/div[3]/button')
pin_box.send_keys(pin)
continue_box.click()
time.sleep(5)

# Redirecting to Kiteconnect
kite = KiteConnect(api_key=api_key)
url = kite.login_url()
page = driver.get(url)
current_url = driver.current_url
request_token = re.search(('request_token=(.*)'), current_url).group(1)[:32]
KRT = kite.generate_session(request_token, api_secret)
kite.set_access_token(KRT['access_token'])
print("Connection Successful")

# Create directory to save data

# Get working directory path
path = "F:/DevAPT/APT/Data/Monthly_Data_Hub"

# Input name of the directory to save the data
# dirName = ''

# Create target Directory if don't exist
# if not os.path.exists(dirName):
#     os.mkdir(dirName)
#     print("Directory " , dirName ,  " created ")
# else:
#     print("Directory " , dirName ,  " already exists")


# Give the list of scrips token
scrip_dict = {
              'ADANIPORTS':'3861249',
              'ASIANPAINT':'60417',
              'AXISBANK':'1510401',
              'BAJAJ-AUTO':'4267265',
              'BAJFINANCE':'81153',
              'BAJAJFINSV':'4268801',
              'BPCL':'134657',
              'BHARTIARTL':'2714625',
              'INFRATEL':'7458561',
              'BRITANNIA':'140033',
              'CIPLA':'177665',
              'COALINDIA':'5215745',
              'DRREDDY':'225537',
              'EICHERMOT':'232961',
              'GAIL':'1207553',
              'GRASIM':'315393',
              'HCLTECH':'1850625',
              'HDFCBANK':'341249',
              'HEROMOTOCO':'345089',
              'HINDALCO':'348929',
              'HINDUNILVR':'356865',
              'HDFC':'340481',
              'ICICIBANK':'1270529',
              'ITC':'424961',
              'IBULHSGFIN':'7712001',
              'IOC':'415745',
              'INDUSINDBK':'1346049',
              'INFY':'408065',
              'JSWSTEEL':'3001089',
              'KOTAKBANK':'492033',
              'LT':'2939649',
              'M&M':'519937',
              'MARUTI':'2815745',
              'NTPC':'2977281',
              'ONGC':'633601',
              'POWERGRID':'3834113',
              'SBIN':'779521',
              'SUNPHARMA':'857857',
              'TCS':'2953217',
              'TATAMOTORS':'884737',
              'TATASTEEL':'895745',
              'TECHM':'3465729',
              'TITAN':'897537',
              'UPL':'2889473',
              'ULTRACEMCO':'2952193',
              'VEDL':'784129',
              'WIPRO':'969473',
              'YESBANK':'3050241',
              'ZEEL':'975873',
              'RELIANCE':'738561'
              }
# date_from = '2019-06-01'
# date_to = '2019-06-30'
interval_list = ['5minute'
                 # 'minute',
                 # 'day',
                 # '3minute',
                 # '10minute',
                 # '15minute',
                 # '30minute',
                 # '60minute'
                 ]

# Fetch data
date_list = [
             # ['2019-08-01', '2019-08-31', 'August_2019'],
             # ['2019-07-01', '2019-07-30', 'July']
             # ['2018-10-01', '2018-10-31', 'October'],
             # ['2018-11-01', '2018-11-30', 'November'],
             # ['2018-12-01', '2018-12-31', 'December'],
             ['2019-01-01', '2019-01-31', 'January'],
             ['2019-02-01', '2019-02-28', 'February'],
             ['2019-03-01', '2019-03-31', 'March'],
             ['2019-04-01', '2019-04-30', 'April'],
             ['2019-05-01', '2019-05-31', 'May'],
             ['2019-06-01', '2019-06-30', 'June'],
             ['2019-07-01', '2019-07-31', 'July'],
             ['2019-08-01', '2019-08-31', 'August'],
             ['2019-09-01', '2019-09-30', 'September'],
             ['2019-10-01', '2019-10-31', 'October'],
             ['2019-11-01', '2019-11-30', 'November']
             ]
for item in date_list:
    in_path = path + "/" + item[2]
    if not os.path.exists(in_path):
        os.mkdir(in_path)
        print("Directory", in_path, "Created ")
    else:
        print("Directory", in_path, "already exists")
    for name, token in scrip_dict.items():
        flag = 0
        in_path = path + "/" + item[2] + "/" + name
        if not os.path.exists(in_path):
            os.mkdir(in_path)
            print("Directory" , in_path ,  "Created ")
        else:
            print("Directory" , in_path ,  "already exists")
        for interval in interval_list:
            if flag == 1:
                interval = 'minute'
            if not os.path.exists(in_path + "/" + interval+'data.csv'):
                try:
                    print("in try block")
                    data=kite.historical_data(instrument_token=token, from_date=item[0], to_date=item[1], interval=interval)
                    flag = 0
                except:
                    print("in except block")
                    flag = 1
                    continue
            else:
                print(name + " " + interval + " already exists")
                continue
            data=pd.DataFrame(data)
            print(name + "-" + interval)
            data.to_csv(in_path + "\\" + interval + '.csv')
            print("Data for "+name+" for interval "+interval+" is saved")
