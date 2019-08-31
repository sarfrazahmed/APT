# Import dependencies
import pandas as pd
from kiteconnect import KiteConnect
import configparser
import os
from kiteconnect import KiteTicker
from datetime import datetime, timedelta

# Authenticate
config = configparser.ConfigParser()
path = os.getcwd()
print(path)
config_path = path + '\\config.ini'
config.read(config_path)
api_key = config['API']['API_KEY']

# Get access token
df = pd.read_csv('access_token.csv', index_col=0)
access_token = df.iloc[0][0]

# Connect to kite
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# # Connect to kite connect
# kws = KiteTicker(api_key, access_token)
#
# # Start webhook
# def on_order_update(ws, data):
#     print(data)
#     data = pd.DataFrame(data)
#     data.to_csv('order_info.csv')
#
# kws.connect()

# Check if order is generated from Strategy
# filename = 'D:/DevAPT/APT/Paper_Trading/access_token.csv'
# old_time = os.stat(filename).st_mtime
# while True:
#     if os.stat(filename).st_mtime != old_time:
#         print("File updated")
#         old_time = os.stat(filename).st_mtime
#         time.sleep(1)

previous_data = pd.read_csv('filename')
previous_orders = kite.orders()
while True:
    if datetime.now().second % 10 == 0:
        orders = kite.orders()
        if previous_orders != orders:
            orders.to_csv('filename')
        if datetime.now().minute % 5 == 0 and datetime.now().second >= 10:
            data = pd.read_csv('filename')
            if len(data) != len(previous_data):
                new_order = data - previous_data
                kite.place_order(new_order)
            elif data != previous_data:
                modified_order = new_order
                kite.modify_order(modified_order)