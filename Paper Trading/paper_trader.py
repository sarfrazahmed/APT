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
config.read('E:\Stuffs\APT\APT\Paper Trading\config.ini')
os.chdir('E:\Stuffs\APT')

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
user_id_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[2]/input')
password_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[3]/input')
log_in_button = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[4]/button')
user_id_box.send_keys(username)
password_box.send_keys(password)
log_in_button.click()
time.sleep(10)

# Logging in using Pin
pin_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[2]/div/input')
continue_box = driver.find_element_by_xpath('//*[@id="container"]/div/div/div/form/div[3]/button')
pin_box.send_keys(pin)
continue_box.click()
time.sleep(10)

# Redirecting to Kiteconnect
kite = KiteConnect(api_key=api_key)
url = kite.login_url()
page = driver.get(url)
current_url = driver.current_url
request_token = re.search(('=(.*)&action'), current_url).group(1)
KRT=kite.generate_session(request_token, api_secret)
kite.set_access_token(KRT['access_token'])
print("Connection Successful")

tokens = [897537]

# Initialise
kws = KiteTicker(api_key, KRT['access_token'])

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    print(ticks)

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens
    ws.subscribe(tokens)

    # Set TITAN to tick in `full` mode.
    ws.set_mode(ws.MODE_LTP , tokens)

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