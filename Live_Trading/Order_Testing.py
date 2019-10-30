# Import dependencies
import pandas as pd
from kiteconnect import KiteConnect
import configparser
import os
import time
import sys
from datetime import datetime
import requests
import logging

def pivotpoints(data):
    pivotpoint = (data['High'][0] + data['Low'][0] + data['Close'][0]) / 3

    s1_simple = (pivotpoint * 2) - data['High'][0]
    s1_fibonacci = pivotpoint - (0.382 * (data['High'][0] - data['Low'][0]))
    s2_simple = pivotpoint - (data['High'][0] - data['Low'][0])
    s2_fibonacci = pivotpoint - (0.618 * (data['High'][0] - data['Low'][0]))
    s3_simple = pivotpoint - (2 * (data['High'][0] - data['Low'][0]))

    r1_simple = (pivotpoint * 2) - data['Low'][0]
    r1_fibonacci = pivotpoint + (0.382 * (data['High'][0] - data['Low'][0]))
    r2_simple = pivotpoint + (data['High'][0] - data['Low'][0])
    r2_fibonacci = pivotpoint + (0.618 * (data['High'][0] - data['Low'][0]))
    r3_simple = pivotpoint + (2 * (data['High'][0] - data['Low'][0]))

    pivots = list([s3_simple, s2_simple, s2_fibonacci, s1_simple, s1_fibonacci, pivotpoint,
                   r1_simple, r1_fibonacci, r2_simple, r2_fibonacci, r3_simple])
    return pivots


def get_target(pivots, order_price, transaction_type, lot_size):
    min_target = 5000
    target_buffer_multiplier = 0
    if transaction_type == 'BUY':
        deltas = [indicator - order_price for indicator in pivots]
        pos_deltas = [delta for delta in deltas if delta > (order_price * 0.005)]
        min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
        target = round(min_pos_delta + order_price + (order_price * target_buffer_multiplier), 1) - order_price
    else:
        deltas = [round(indicator, 1) - order_price for indicator in pivots]
        neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.005)]
        max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
        target = order_price - round(order_price + max_neg_delta - (order_price * target_buffer_multiplier), 1)
    return target


name = 'YESBANK'
access_token = 'si0y1PQYpV3hYgxgsI0RJppZmlq4X1XH'
lot_size = 3000

# Read previous day data file
data = pd.read_csv('C:/Users/Sarfraz/Desktop/previous_day_data_' + name + '.csv')
pivots = pivotpoints(data)

path = 'D:\DevAPT\APT\Live_Trading'
os.chdir(path)
config = configparser.ConfigParser()
config_path = path + '/config.ini'
config.read(config_path)
api_key = config['API']['API_KEY']

# Connect to kite
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

transaction_type = 'BUY'
quantity = 1
entry_price = 166.5
day_high = 171.4
day_low = 151.2
modified_price = 155

#place order
order_id = kite.place_order(tradingsymbol=name,
                            variety='bo',
                            exchange=kite.EXCHANGE_NSE,
                            transaction_type=transaction_type,
                            quantity=quantity,
                            price=entry_price,
                            order_type=kite.ORDER_TYPE_LIMIT ,
                            product=kite.PRODUCT_MIS,
                            stoploss=(day_high - entry_price) if transaction_type == 'SELL' else (entry_price - day_low),
                            squareoff=get_target(pivots, entry_price, transaction_type, lot_size))


# cancel last placed order
kite.cancel_order(variety='bo',
                  order_id=order_id)

parent_order_id = 191030000348338
order_id = 191030000404983
modified_price = 720
quantity = 10
#order modify
order_id = kite.modify_order(variety='bo',
                             parent_order_id=parent_order_id,
                             order_id=order_id,
                             order_type=kite.ORDER_TYPE_SL,
                             quantity=quantity,
                             price=modified_price,
                             trigger_price=modified_price
                             )

