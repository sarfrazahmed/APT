# Import dependencies
import pandas as pd
from kiteconnect import KiteConnect
import configparser
import os
import time
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

while True:
    previous_data = pd.read_csv('filename')
    all_orders = kite.orders()
    if len(data) != 0:
        current_order = len(data)
        if datetime.now().second % 10 == 0:
            # get all orders
            all_orders = kite.orders()
            # filter for current order
            order = all_orders['order_id']
            if previous_order != order:
                # punch new order if stoploss gets hit
                if order['status'] == 'COMPLETE':
                    if order['transaction_type'] == 'BUY':
                        transaction_type = 'SELL'
                        target = get_target(token)
                        stoploss = data.at[current_order, 'day_high']
                        order_id = kite.place_order(variety='BO', order_type='LIMIT', product='MIS', validity='DAY',
                                                transaction_type='transaction_type', price=data.at[current_order, 'price'],
                                                squareoff=data.at[current_order, 'target'], stoploss=data.at[current_order, 'stoploss'])
                # change order status
                if order['status'] == 'Executed':
                    data.at[current_order, 'status'] = 'COMPLETE'
                elif order['status'] == 'Cancelled':
                    data.at[current_order, 'status'] = 'CANCELLED'
                elif order['status'] == 'Placed':
                    data.at[current_order, 'status'] = 'OPEN'
                previous_order = order
                data.to_csv('filename')

            if datetime.now().minute % 5 == 0 and datetime.now().second >= 10:
                data = pd.read_csv('filename')

                # place new order
                if data.at[current_order, 'modified'] == 0:
                    order_id = kite.place_order(variety='BO', order_type='LIMIT', product='MIS', validity='DAY',
                                                transaction_type='transaction_type', price=data.at[current_order, 'price'],
                                                squareoff=data.at[current_order, 'target'], stoploss=data.at[current_order, 'stoploss'])
                    data.at[current_order, order_id] = order_id

                # cancel previous order and place new order if semi-target hits
                if data.at[current_order, 'Semi-Target_Status'] == 'Hit' and order.at[
                    current_order, 'Status'] == 'Placed':
                    kite.cancel_order(order_id='order_id')
                    order_id = kite.place_order(variety='BO', order_type='LIMIT', product='MIS', validity='DAY',
                                                transaction_type='transaction_type', price=data.at[current_order, 'price'],
                                                squareoff=data.at[current_order, 'target'], stoploss=data.at[current_order, 'stoploss'])
                    data.at[current_order, order_id] = order_id
    time.sleep(1)
