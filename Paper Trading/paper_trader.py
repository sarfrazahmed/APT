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

config = configparser.ConfigParser()
config.read('config.ini')


# Authentication
api_key = config['API']['API_KEY']
api_secret = config['API']['API_SECRET']
kite = KiteConnect(api_key=api_key)
url = kite.login_url()

# Open chrome tab with the URL
# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--no-sandbox')
driver = webdriver.Chrome(executable_path='E:/Stuffs/APT/chromedriver.exe')
driver.get(url)

# Get the 
username = driver.find_element_by_xpath("//*[@id='container']/div/div/div[2]/form/div[1]/input")
password = driver.find_element_by_xpath('//*[@id="container"]/div/div/div[2]/form/div[2]/input')

username.send_keys(config['USER']['USERNAME'])
password.send_keys(config['USER']['PASSWORD'])

submit = driver.find_element_by_xpath('//*[@id="container"]/div/div/div[2]/form/div[4]/button')



request_token='2AaGdDipi5sehld6gl1wD7CY2AZErAEK'
KRT=kite.generate_session(request_token,api_secret)
kite.set_access_token(KRT['access_token'])
print(KRT)

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