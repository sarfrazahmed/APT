####################################################################################
##Title:       Scrip Scanner
##Author:      Anubhab Ghosh
##Purpose:     This script will authenticate the Kite session and will select
##             the gap-up/down scrips for the day using KiteConnect API (Not NSE)
##User Input:  Change the "Initial Inputs" part to run the code as required
##Version:     1.0
#####################################################################################


## Import Libraries
###############################################################
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import copy
import os
import configparser
import re
from selenium import webdriver
import time
from kiteconnect import KiteConnect
import requests

##Function to get previous Weekday
###############################################################
def prev_weekday(adate):
    holiday_list = ['2020-10-02', '2020-11-16', '2020-11-30', '2020-12-25']
    adate -= timedelta(days=1)
    if adate.strftime('%Y-%m-%d') in holiday_list:
        adate -= timedelta(days=1)
    while adate.weekday() > 4:
        adate -= timedelta(days=1)
    return adate

## Initial Inputs
###############################################################
# For Ubuntu
# working_dir = './APT/Live_Trading'

# For ubuntu
working_dir = '/home/ubuntu/APT/APT/Live_Trading'

# For Windows
# working_dir = 'F:/DevAPT/APT/FastAPT'

input_file_level = 'day'
output_file_name = 'Selected Stocks.csv'
info_file_path = 'F_O_Stocks_Token.csv'
kitepage = 'https://kite.zerodha.com/'
# Bot API Link
bot_link = "https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text="
gap_up_limit = 1  # Gap Up/Down Min Limit Criteria
max_try_count = 5  # No of Tries for chrome automation
# Set Arguments for data fetch
today = date.today()
date_from = prev_weekday(today)
interval = 'day'

## Main Body
###############################################################

# Get all info
message = "Starting Trading Engine..." + '\nStart Time: ' + str(datetime.now())
requests.get(bot_link + message)

os.chdir(working_dir)
info_data = pd.read_csv(info_file_path)

# Establicsh connection with Kiteconnect
config_path = working_dir + '/config.ini'
config = configparser.ConfigParser()
config.read(config_path)
api_key = config['API']['API_KEY']
api_secret = config['API']['API_SECRET']
username = config['USER']['USERNAME']
password = config['USER']['PASSWORD']
pin = config['USER']['PIN']
print("Details read")

# Try x times to connect kite
message = "Authenticating For Generation of Access Token..."
requests.get(bot_link + message)
try_counter = 1

while try_counter <= max_try_count:

    try:

        message = 'Trying Logging in via Chrome: Try ' + str(try_counter)
        requests.get(bot_link + message)

        # Selenium for ubuntu
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome('/home/ubuntu/APT/APT/chromedriver.exe', options=chrome_options)
        page = driver.get(kitepage)
        time.sleep(5)

        # Selenium for windows
        # driver = webdriver.Chrome(executable_path='F:\\DevAPT\\APT\\chromedriver.exe')
        # page = driver.get(kitepage)
        # time.sleep(5)

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
        print(api_key)
        kite = KiteConnect(api_key=api_key)
        url = kite.login_url()
        print(url)
        page = driver.get(url)
        current_url = driver.current_url
        print(current_url)
        request_token = re.search('request_token=(.*)', current_url).group(1)[:32]
        print(request_token)
        KRT = kite.generate_session(request_token, api_secret)
        access_token = KRT['access_token']
        print('Access Token - ' + access_token)
        message = "Connection Successful"
        requests.get(bot_link + message)
        driver.close()
        break

    except:
        try_counter = try_counter + 1

# Go For Stock Selection if Access Token is received successfully
if try_counter < 6:

    # Create Session with Kite
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    # Calculate Gap UP/Down For Stocks in list
    stock_list = pd.read_csv(info_file_path)

    # Initializing Counter for Selected Stock Dataset
    selected_stock_initialize_flag = 0

    # Iterate over all the available scrips
    stock_list = info_data
    for i in stock_list.index.values:

        # Get Previous Weekday and today's day level candle data
        day_compare_data = kite.historical_data(instrument_token= stock_list['Token'][i], from_date= date_from,
                                                 to_date=today, interval=interval)
        day_compare_data = pd.DataFrame(day_compare_data)
        print(stock_list['Company'][i])
        day_compare_data.columns = ['Close', 'Date', 'High', 'Low', 'Open', 'Volume']

        # Convert date column into date format
        day_compare_data['Date'] = [str(i) for i in day_compare_data['Date']]
        day_compare_data['Date'] = [i[:i.find('+')] for i in day_compare_data['Date']]
        day_compare_data['Date'] = [datetime.strptime(i, '%Y-%m-%d %H:%M:%S') for i in day_compare_data['Date']]

        # Calculate Gap Up/Down Extent
        previous_day = day_compare_data[day_compare_data['Date'] == np.datetime64(date_from)]
        previous_day = previous_day.reset_index(drop=True)
        current_day = day_compare_data[day_compare_data['Date'] == np.datetime64(today)]
        current_day = current_day.reset_index(drop=True)
        gap = abs(previous_day['Close'][len(previous_day) - 1] - current_day['Open'][0])
        gap_up_down_pecentage = (gap / previous_day['Close'][len(previous_day) - 1]) * 100
        print('Gap Up-Down Percentage = ' + str(gap_up_down_pecentage))

        # Check if the gap-up is meeting the criteria
        if gap_up_down_pecentage >= gap_up_limit:

            #selected_stocks = stock_list.iloc[[i]]

            # Check if Selected Stock dataset is initialized
            if selected_stock_initialize_flag == 0:

                # Creating Selected Stock List Dataframe with first entry
                selected_stock_list = stock_list.iloc[[i]]

                # change flag to indicate to show that selected stock list is initialized
                selected_stock_initialize_flag = 1

            else:

                # Append the stock details in the selected stock list
                selected_stock_list = selected_stock_list.append(stock_list.iloc[[i]])

        # Wait For 1 sec before iterating
        time.sleep(1)
    # Check if Stocks are selected through previous steps
    if len(selected_stock_list) > 0:

        # Include access token in selected stock list
        selected_stock_list['Access_Token'] = access_token
        
        # Send Intuitive Message in Telegram
        message = str(len(selected_stock_list)) + ' Stocks Selected From Gap Up_Down Criteria'



    # If Stock List is not selected due to any glitch
    else:

        # Use backup scrips & add access token in them
        message = 'No Scrip is Selected from gap-up/ gap-down'
        requests.get(bot_link + message)

else:

    # Use backup scrips & add access token in them
    message = 'Could not fetch access token'
    requests.get(bot_link + message)


# Write the stock list as csv
selected_stock_list.to_csv('Selected_Stock_List.csv', index= False)
