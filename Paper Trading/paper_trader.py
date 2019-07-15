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

print("Starting Trading Engine...")
config = configparser.ConfigParser()
config_path = 'E:/Stuffs/APT/APT/Paper Trading/config.ini'
config.read(config_path)
path = 'E:/Stuffs/APT'
os.chdir(path)

api_key = config['API']['API_KEY']
api_secret = config['API']['API_SECRET']
username = config['USER']['USERNAME']
password = config['USER']['PASSWORD']
pin = config['USER']['PIN']
homepage = 'https://kite.zerodha.com/'

driver = webdriver.Chrome()
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

tokens = [897537]
# tick_data = pd.DataFrame(columns=['token', 'time', 'ltp'])
tick_data = []

# Initialise
kws = KiteTicker(api_key, KRT['access_token'])


def on_ticks(ws, ticks):
    # Callback to receive ticks.
    token = ticks[0]['instrument_token']
    ltp = ticks[0]['last_price']
    time = ticks[0]['timestamp']
    tick_data.append({'token': token, 'ltp': ltp, 'timestamp': time})
    print(ticks)

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens
    ws.subscribe(tokens)

    # Set TITAN to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, tokens)

# def on_close(ws, code, reason):
#     # On connection close stop the main loop
#     # Reconnection will not happen after executing `ws.stop()`
#     ws.stop()


# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
# kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()

# LTP
# tick = [{'tradable': True, 'mode': 'ltp', 'instrument_token': 897537, 'last_price': 1101.2}]

# FULL
# tick = [{'tradable': True, 'mode': 'full', 'instrument_token': 897537, 'last_price': 1085.6, 'last_quantity': 14, 'average_price': 1089.2, 'volume': 1030686, 'buy_quantity': 863713, 'sell_quantity': 269903, 'ohlc': {'open': 1110.0, 'high': 1110.05, 'low': 1079.0, 'close': 1101.2}, 'change': -1.4166363966582034, 'last_trade_time': datetime.datetime(2019, 7, 15, 11, 6, 11), 'oi': 0, 'oi_day_high': 0, 'oi_day_low': 0, 'timestamp': datetime.datetime(2019, 7, 15, 11, 6, 12), 'depth': {'buy': [{'quantity': 24, 'price': 1085.45, 'orders': 1}, {'quantity': 90, 'price': 1085.4, 'orders': 2}, {'quantity': 23, 'price': 1085.35, 'orders': 1}, {'quantity': 12, 'price': 1085.3, 'orders': 2}, {'quantity': 231, 'price': 1085.25, 'orders': 2}], 'sell': [{'quantity': 41, 'price': 1085.6, 'orders': 4}, {'quantity': 219, 'price': 1086.0, 'orders': 3}, {'quantity': 2, 'price': 1086.1, 'orders': 1}, {'quantity': 9, 'price': 1086.15, 'orders': 1}, {'quantity': 46, 'price': 1086.25, 'orders': 1}]}}]
# token = tick[0]['instrument_token']
# ltp = tick[0]['last_price']
# time = tick[0]['timestamp']

# tick_data = pd.DataFrame(columns=['token', 'time', 'ltp'])
# tick_data.loc[0] = [token, time, ltp]
# print(tick_data)

# QUOTE
# tick = [{'tradable': True, 'mode': 'quote', 'instrument_token': 897537, 'last_price': 1086.2, 'last_quantity': 1, 'average_price': 1089.13, 'volume': 1055785, 'buy_quantity': 864953, 'sell_quantity': 438516, 'ohlc': {'open': 1110.0, 'high': 1110.05, 'low': 1079.0, 'close': 1101.2}, 'change': -1.3621503814021068}]

# tick_data.insert()

tick_df = pd.DataFrame(tick_data)
tick_df['timestamp']  = pd.to_datetime(tick_df['timestamp'])
grouped = tick_df.groupby('token')
ltp = grouped['ltp'].resample('15Min', how='ohlc')
resampled_tick_data = tick_df.resample('15Min')
print(resampled_tick_data)
tick_df