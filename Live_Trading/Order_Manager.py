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
    if datetime.now().minute % 5 == 0 and datetime.now().second >= 3:
        local_orders = pd.read_csv('filename')
        if len(local_orders > 0):
            # Place first order
            local_current_order = len(local_orders) - 2
            order_id = kite.place_order(tradingsymbol=local_orders.at[local_current_order, 'tradingsymbol'],
                                        variety='bo',
                                        exchange=kite.EXCHANGE_NSE,
                                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                                        quantity=local_orders.at[local_current_order, 'quantity'],
                                        price=local_orders.at[local_current_order, 'price'],
                                        order_type=kite.ORDER_TYPE_LIMIT,
                                        product=kite.PRODUCT_MIS,
                                        stoploss=local_orders.at[local_current_order, 'stoploss'],
                                        squareoff=local_orders.at[local_current_order, 'target'])
            local_orders.at[local_current_order, 'order_id'] = order_id

            # Place second order
            local_current_order = len(local_orders) - 1
            order_id = kite.place_order(tradingsymbol=local_orders.at[local_current_order, 'tradingsymbol'],
                                        variety='bo',
                                        exchange=kite.EXCHANGE_NSE,
                                        transaction_type=kite.TRANSACTION_TYPE_BUY,
                                        quantity=local_orders.at[local_current_order, 'quantity'],
                                        price=local_orders.at[local_current_order, 'price'],
                                        order_type=kite.ORDER_TYPE_LIMIT,
                                        product=kite.PRODUCT_MIS,
                                        stoploss=local_orders.at[local_current_order, 'stoploss'],
                                        squareoff=local_orders.at[local_current_order, 'target'])
            local_orders.at[local_current_order, 'order_id'] = order_id
            order_id_list = list(local_orders['order_id'])
            kite_all_orders = pd.DataFrame(kite.orders())
            while True:
                if datetime.now().second % 10 == 0:
                    if kite_all_orders != pd.DataFrame(kite.orders()):
                        if kite_all_orders[kite_all_orders['order_id'] == order_id_list[0]]['status'] == 'COMPLETE':
                            kite.cancel_order(order_id_list[1])
                        elif kite_all_orders[kite_all_orders['order_id'] == order_id_list[1]]['status'] == 'COMPLETE':
                            kite.cancel_order(order_id_list[0])
                    else:
                        time.sleep(1)





# while True:
#     local_previous_order = pd.read_csv('filename')
#     kite_all_orders = pd.DataFrame(kite.orders())
#     if len(local_previous_order) != 0:
#         local_current_order = len(local_previous_order) - 1
#         if datetime.now().second % 10 == 0:
#             # get all orders
#             kite_all_orders = pd.DataFrame(kite.orders())
#             # filter for current order
#             kite_current_order = kite_all_orders[kite_all_orders['order_id'] == order_id]
#             if local_previous_order != order:
#                 # punch new order if stoploss gets hit
#                 if order['status'] == 'COMPLETE':
#                     if order['transaction_type'] == 'BUY':
#                         transaction_type = 'SELL'
#                         target = get_target(token)
#                         stoploss = data.at[local_current_order, 'day_high']
#                         order_id = kite.place_order(variety='BO', order_type='LIMIT', product='MIS', validity='DAY',
#                                                 transaction_type='transaction_type', price=data.at[local_current_order, 'price'],
#                                                 squareoff=data.at[local_current_order, 'target'], stoploss=data.at[local_current_order, 'stoploss'])
#                 # change order status
#                 if order['status'] == 'Executed':
#                     data.at[local_current_order, 'status'] = 'COMPLETE'
#                 elif order['status'] == 'Cancelled':
#                     data.at[local_current_order, 'status'] = 'CANCELLED'
#                 elif order['status'] == 'Placed':
#                     data.at[local_current_order, 'status'] = 'OPEN'
#                 local_previous_order = order
#                 data.to_csv('filename')
#
#             if datetime.now().minute % 5 == 0 and datetime.now().second >= 10:
#                 data = pd.read_csv('filename')
#
#                 # place new order
#                 if data.at[local_current_order, 'modified'] == 0:
#                     order_id = kite.place_order(variety='BO', order_type='LIMIT', product='MIS', validity='DAY',
#                                                 transaction_type='transaction_type', price=data.at[local_current_order, 'price'],
#                                                 squareoff=data.at[local_current_order, 'target'], stoploss=data.at[local_current_order, 'stoploss'])
#                     data.at[local_current_order, order_id] = order_id
#
#                 # cancel previous order and place new order if semi-target hits
#                 if data.at[local_current_order, 'Semi-Target_Status'] == 'Hit' and order.at[
#                     local_current_order, 'Status'] == 'Placed':
#                     kite.cancel_order(order_id='order_id')
#                     order_id = kite.place_order(variety='BO', order_type='LIMIT', product='MIS', validity='DAY',
#                                                 transaction_type='transaction_type', price=data.at[local_current_order, 'price'],
#                                                 squareoff=data.at[local_current_order, 'target'], stoploss=data.at[local_current_order, 'stoploss'])
#                     data.at[local_current_order, order_id] = order_id
#     time.sleep(1)
