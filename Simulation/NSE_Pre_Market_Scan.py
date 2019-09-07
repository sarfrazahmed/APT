## Importing Libraries
###########################################################################################
import os
from selenium import webdriver
import time
from kiteconnect import KiteConnect
import pandas as pd
import html5lib


## Initial Inputs
###########################################################################################
homepage = 'https://www.nseindia.com/live_market/dynaContent/live_watch/pre_open_market/pre_open_market.htm'
output_folder = 'F:/DevAPT/APT/Paper_Trading' # For Windows
# output_folder = '/home/ubuntu/APT/APT/Paper_Trading' # For Ubuntu
exception_stocks = ['IDEA','BOSCHLTD','CASTROLIND','IDBI','MRF','NBCC','DISHTV',
                    'GMRINFRA','RELINFRA']
info_data_path = 'nifty50_stocks_token.csv'

## Main Body
###########################################################################################
os.chdir(output_folder)
# Open Webbrowser for ubuntu
# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
# chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument('--disable-dev-shm-usage')
# driver = webdriver.Chrome(chrome_options=chrome_options)
# page = driver.get(homepage)

# Get Stocks Info
info_data = pd.read_csv(info_data_path)

# Selenium for windows
chromeOptions = webdriver.ChromeOptions()
driver = webdriver.Chrome(executable_path='F:/DevAPT/APT/chromedriver.exe')
page = driver.get(homepage)
time.sleep(5)


# Choose All FO stocks From Option
x = driver.find_element_by_xpath('//*[@id="selId"]/option[2]')
x.click()

# Get Pre-market data as DataFrame
table = driver.find_element_by_xpath('//*[@id="preOpenNiftyTab"]')
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
selected_scrips_info = selected_scrips_info[0:5]
selected_scrips_info = selected_scrips_info[['Company','Token','Lot_Size']]
selected_scrips_info['Access_Token'] = '0000'
selected_scrips_info['Extra'] = 0

# Write Updated Stock List For Today as CSV
selected_scrips_info.to_csv('stock_list_updated.csv',index=False)