# Import dependencies
import datetime
import logging
from kiteconnect import KiteTicker
from kiteconnect import KiteConnect
import pandas as pd
import os
from selenium import webdriver
import time
from datetime import date, timedelta, datetime
import configparser
import re
import sys
import requests

def start(name, token, access_token, timeframe):
    # print("Starting Trading Engine...", flush=True)
    config = configparser.ConfigParser()
    # path = os.getcwd()
    path = '/home/ubuntu/APT/APT/Paper_Trading'
    config_path = path + '/config.ini'
    config.read(config_path)
    api_key = config['API']['API_KEY']

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    # Get previous day candle
    def prev_weekday(adate):
        adate -= timedelta(days=1)
        while adate.weekday() > 4:
            adate -= timedelta(days=1)
        return adate
    date_from = prev_weekday(date.today())
    date_to = date_from
    interval = 'day'
    previous_day_data = kite.historical_data(instrument_token=token[0], from_date=date_from, to_date=date_to, interval=interval)
    previous_day_data = pd.DataFrame(previous_day_data)
    previous_day_data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    previous_day_data.to_csv("previous_day_data_"+ name +'.csv')

    # Sleep till 9:15
    time_now = datetime.now()
    sleep_time = 60 - time_now.second
    time.sleep(sleep_time)
    time_now = datetime.now()
    print('Script Started at ' + str(time_now),flush=True)

    # Initialise
    print("Initialising Kite Ticker")
    kws = KiteTicker(api_key, access_token)
    start.tick_df = pd.DataFrame(columns=['Token', 'Timestamp', 'LTP'], index=pd.to_datetime([]))
    start.last_saved_time = 10


    def on_ticks(ws, ticks):
        # Callback to receive ticks.
        # print(ticks)
        start.tick_df = start.tick_df.append({'Token': ticks[0]['instrument_token'], 'Timestamp': ticks[0]['timestamp'], 'LTP': ticks[0]['last_price']}, ignore_index=True)
        if (start.tick_df['Timestamp'][len(start.tick_df) - 1].minute % 5 == 0) and (start.tick_df['Timestamp'][len(start.tick_df) - 1].minute != start.last_saved_time):
            # save the last minute
            start.last_saved_time = start.tick_df['Timestamp'][len(start.tick_df) - 1].minute

            # drop last row
            start.tick_df.drop(start.tick_df.tail(1).index, inplace=True)
            print(len(start.tick_df))

            # set timestamp as index
            start.tick_df = start.tick_df.set_index(['Timestamp'])
            start.tick_df['Timestamp'] = pd.to_datetime(start.tick_df.index, unit='s')

            # convert to OHLC format
            data_ohlc = start.tick_df['LTP'].resample(timeframe).ohlc()
            print(data_ohlc)
            # save the dataframe to csv
            data_ohlc.to_csv('ohlc_data_' + name +'.csv')
            print("Printed at " + str(datetime.datetime.now()))

            # initialize the dataframe
            start.tick_df = pd.DataFrame(columns=['Token', 'Timestamp', 'LTP'], index=pd.to_datetime([]))
            print(len(data_ohlc))

    def on_connect(ws, response):
        # Callback on successful connect.
        # Subscribe to a list of instrument_tokens
        ws.subscribe(token)
        # Set TITAN to tick in `full` mode.
        ws.set_mode(ws.MODE_FULL, token)

    # Callback when current connection is closed.
    def on_close(ws, code, reason):
        logging.info("Connection closed: {code} - {reason}".format(code=code, reason=reason))


    # Callback when connection closed with error.
    def on_error(ws, code, reason):
        logging.info("Connection error: {code} - {reason}".format(code=code, reason=reason))


    # Callback when reconnect is on progress
    def on_reconnect(ws, attempts_count):
        logging.info("Reconnecting: {}".format(attempts_count))


    # Callback when all reconnect failed (exhausted max retries)
    def on_noreconnect(ws):
        logging.info("Reconnect failed.")


    # Assign the callbacks.
    kws.on_ticks = on_ticks
    kws.on_close = on_close
    kws.on_error = on_error
    kws.on_connect = on_connect
    kws.on_reconnect = on_reconnect
    kws.on_noreconnect = on_noreconnect
    print("Callbacks assigned")


    # Infinite loop on the main thread. Nothing after this will run.
    # You have to use the pre-defined callbacks to manage subscriptions.
    kws.connect()
    print("KWS disconnected")


if __name__ == '__main__':
    # path = os.getcwd()
    path = '/home/ubuntu/APT/APT/Paper_Trading'
    os.chdir(path)
    name = sys.argv[1]
    token = [int(sys.argv[2])]
    access_token = sys.argv[3]
    # name = 'IBULHSGFIN'
    # token = [7712001]
    # access_token = 'Aiz2qrsvSQEgaPIcayZiS1lqy5YyVZnL'
    print('Stock Name: ' + name, flush=True)
    start(name, token, access_token, timeframe='5min')
