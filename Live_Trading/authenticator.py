# Import dependencies
import configparser
import re
import os
from selenium import webdriver
import time
from datetime import datetime
print('Start Time: ' + str(datetime.now()))
from kiteconnect import KiteConnect
import pandas as pd

# Get all info
print("Starting Trading Engine...", flush=True)
config = configparser.ConfigParser()


## Initial Inputs
############################################################################
# For Windows
# path = 'F:/DevAPT/APT/Live_Trading'

# For Ubuntu
path = '/home/ubuntu/APT/APT/Live_Trading'

# For Windows
# path = 'D:/DevAPT/APT/Live_Trading'

exception_stocks = ['IDEA','BOSCHLTD','CASTROLIND','IDBI','MRF','NBCC','DISHTV',
                    'GMRINFRA','RELINFRA']
info_data_path = 'nifty50_stocks_token.csv'
nsepage = 'https://www.nseindia.com/live_market/dynaContent/live_watch/pre_open_market/pre_open_market.htm'
kitepage = 'https://kite.zerodha.com/'



## Main Body
################################################################
os.chdir(path)
info_data = pd.read_csv(info_data_path)
config_path = path + '/config.ini'
config.read(config_path)
api_key = config['API']['API_KEY']
api_secret = config['API']['API_SECRET']
username = config['USER']['USERNAME']
password = config['USER']['PASSWORD']
pin = config['USER']['PIN']


## Selenium for ubuntu
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(chrome_options=chrome_options)
page = driver.get(nsepage)
time.sleep(5)

# Selenium for windows
# driver = webdriver.Chrome(executable_path='F:\\DevAPT\\APT\\chromedriver.exe')
# page = driver.get(nsepage)
# time.sleep(5)

# Choose All FO stocks From Option
print('Getting All Gap Up/ Down Stocks From Pre Market...')
x = driver.find_element_by_xpath('//*[@id="selId"]/option[2]')
x.click()
time.sleep(3)

# Get Pre-market data as DataFrame
table = driver.find_element_by_xpath('//*[@id="preOpenNiftyTab"]')
print(table,flush= True)
tbl = table.get_attribute('outerHTML')
pre_open_stat = pd.read_html(tbl)[0]
pre_open_stat = pre_open_stat.drop([1,2,3,4,6,7,8,9,10,11],axis=1)
pre_open_stat.columns = pre_open_stat.iloc[1]
pre_open_stat = pre_open_stat[2:]
pre_open_stat['% Chng'] = [float(i) for i in pre_open_stat['% Chng']]


# Select Stocks From Pre-Open Scenario
pre_open_stat['Abs_Change'] = abs(pre_open_stat['% Chng'])
pre_open_stat = pre_open_stat[~pre_open_stat.Symbol.isin(exception_stocks)]

# Scenario 1
selected_scrips = pre_open_stat[pre_open_stat['Abs_Change'] >= 0.9]
selected_scrips = selected_scrips.sort_values(['Abs_Change'],ascending=False)
selected_scrips = selected_scrips[['Symbol', '% Chng', 'Abs_Change']]

# Include Token & Lot_Size
selected_scrips_info = pd.merge(selected_scrips,info_data,
                                left_on='Symbol',
                                right_on='Company',
                                how='left')
selected_scrips_info = selected_scrips_info.dropna()
selected_scrips_info = selected_scrips_info.reset_index()
selected_scrips_info = selected_scrips_info[0:3]
selected_scrips_info = selected_scrips_info[['Company','Token','Lot_Size']]
print('Completed')



# Login using username and password
print("Authenticating For Generation of Access Token...", flush=True)
page = driver.get(kitepage)
time.sleep(3)

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

# Log in using Pin
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
request_token = re.search('request_token=(.*)', current_url).group(1)[:32]
KRT = kite.generate_session(request_token, api_secret)
print("Connection Successful")
driver.close()

# Write access token
selected_scrips_info['Access_Token'] = KRT['access_token']
selected_scrips_info['Extra'] = 0
selected_scrips_info['Token'] = [int(i) for i in selected_scrips_info['Token']]
selected_scrips_info['Lot_Size'] = [int(i) for i in selected_scrips_info['Lot_Size']]
selected_scrips_info.to_csv('stock_list_updated.csv', index=False)
print("Connection successful", flush=True)
print("End Time: " + str(datetime.now()))
