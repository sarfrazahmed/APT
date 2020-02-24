import threading
import time
import datetime
import logging
from kiteconnect import KiteTicker
from kiteconnect import KiteConnect
import pandas as pd
import os
from selenium import webdriver
import requests
import time
from datetime import date, timedelta, datetime
import configparser
import sys

#Initialize global variable
# global data_ohlc = pd.DataFrame()

#Function to get previous Weekday
def prev_weekday(adate):
    holiday_list = ['2019-10-02', '2019-10-08', '2019-10-28', '2019-11-12', '2019-12-25']
    adate -= timedelta(days=1)
    if adate.strftime('%Y-%m-%d') in holiday_list:
        adate -= timedelta(days=1)
    while adate.weekday() > 4:
        adate -= timedelta(days=1)
    return adate


#Candle Generator
def process_ohlc(api_key, access_token, token, timeframe):

    #Call the Global Exchangable Variable
    global data_ohlc
    # Initialise Kite Socket Connection
    print("Initialising Kite Ticker")
    kws = KiteTicker(api_key, access_token)
    process_ohlc.tick_df = pd.DataFrame(columns=['Token', 'Timestamp', 'LTP'], index=pd.to_datetime([]))
    process_ohlc.last_saved_time = 10

    def on_ticks(ws, ticks):

        # print(ticks)
        # print(ticks[0]['timestamp'] >= datetime.now().replace(hour= 9,minute= 15, second = 0,microsecond = 0))
        # print(ticks[0]['timestamp'] >= datetime.strptime('1970-01-01 00:00:00','%Y-%m-%d %H:%M:%S'))
        if ticks[0]['timestamp'] >= datetime.now().replace(hour= 3,minute= 45, second = 0,microsecond = 0):

            #Check if its a 5th minute
            if (ticks[0]['timestamp'].minute() % 5 == 0) and (ticks[0]['timestamp'].minute() != process_ohlc.last_saved_time):
                process_ohlc.tick_df = pd.DataFrame(columns=['Token', 'Timestamp', 'LTP'], index=pd.to_datetime([]))

            #Append Ticks into 1 table
            process_ohlc.tick_df = process_ohlc.tick_df.append({'Token': ticks[0]['instrument_token'],
                                                                'Timestamp': ticks[0]['timestamp'],
                                                                'LTP': ticks[0]['last_price']}, ignore_index=True)

            # set timestamp as index
            process_ohlc.tick_df = process_ohlc.tick_df.set_index(['Timestamp'])
            process_ohlc.tick_df['Timestamp'] = pd.to_datetime(process_ohlc.tick_df.index, unit='s')

            # convert to OHLC format
            data_ohlc_raw = process_ohlc.tick_df['LTP'].resample(timeframe).ohlc()
            data_ohlc_raw['Last_Time'] = process_ohlc.tick_df['Timestamp'][len(process_ohlc.tick_df) - 1]
            data_ohlc = data_ohlc_raw


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



# Generate Decisions
def decision_engine():

    global data_ohlc

    while True:
        # Print OHLC Updating OHLC data
        message = 'Latest Time:' + str(data_ohlc['Last_Time'][len(data_ohlc) - 1]) + '\n Open: ' + \
                  str(data_ohlc['open'][len(data_ohlc) - 1]) + '\n High: ' + str(
            data_ohlc['high'][len(data_ohlc) - 1]) + \
                  '\n Low: ' + str(data_ohlc['low'][len(data_ohlc) - 1]) + '\n Close: ' + \
                  str(data_ohlc['close'][len(data_ohlc) - 1])
        requests.get(
            "https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)
        print(message)
        time.sleep(2)




if __name__ == '__main__':

    # setting global variable
    global data_ohlc
    data_ohlc = pd.DataFrame()

    # Get the input parameters and start the parallel processing
    # path = '/home/ubuntu/APT/APT/Live_Trading'
    path = 'F:\DevAPT\APT\Live_Trading'
    config_path = path + '/config.ini'
    os.chdir(path)
    # name = sys.argv[1]
    # token = [int(sys.argv[2])]
    # access_token = sys.argv[3]
    name = 'IBULHSGFIN'
    token = [7712001]
    access_token = 't6C3VvBafs9mSmi8sztGBauhIouPNW1h'
    stock_name_string = 'Stock Name: ' + name
    requests.get(
        "https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + \
        stock_name_string)
    print(stock_name_string, flush=True)

    # Establicsh connection with Kiteconnect
    config = configparser.ConfigParser()
    config.read(config_path)
    api_key = config['API']['API_KEY']
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    # Extract Last day's daily level ohlc data
    date_from = prev_weekday(date.today())
    date_to = date_from + timedelta(days=1)
    interval = 'day'
    previous_day_data = kite.historical_data(instrument_token=token[0], from_date=date_from, to_date=date_to,
                                             interval=interval)
    previous_day_data = pd.DataFrame(previous_day_data)
    previous_day_data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    previous_day_data.to_csv("previous_day_data_" + name + '.csv')

    # Sleep till 9:15
    time_now = datetime.now()
    sleep_time = 60 - time_now.second
    time.sleep(sleep_time)
    time_now = datetime.now()
    print('Script Started at ' + str(time_now), flush=True)

    #Start Threading
    t1 = threading.Thread(target=process_ohlc, args=(api_key, access_token, token, '5min',))
    t2 = threading.Thread(target=decision_engine)

    t1.start()
    t2.start()

    # wait until threads finish their job
    t1.join()
    t2.join()


