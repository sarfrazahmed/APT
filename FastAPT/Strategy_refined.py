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


## Pivot Point Calculation
###############################################################
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

    pivots = list([s3_simple,s2_simple,s2_fibonacci,s1_simple,s1_fibonacci,pivotpoint,
                   r1_simple,r1_fibonacci,r2_simple,r2_fibonacci,r3_simple])
    return pivots

##Function to get previous Weekday
###############################################################
def prev_weekday(adate):
    holiday_list = ['2019-10-02', '2019-10-08', '2019-10-28', '2019-11-12', '2019-12-25']
    adate -= timedelta(days=1)
    if adate.strftime('%Y-%m-%d') in holiday_list:
        adate -= timedelta(days=1)
    while adate.weekday() > 4:
        adate -= timedelta(days=1)
    return adate



##Main Script Flow
def start(name, token, access_token, lot_size):
    # Establicsh connection with Kiteconnect
    config = configparser.ConfigParser()
    config.read(config_path)
    api_key = config['API']['API_KEY']
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    # Bot API Link
    bot_link = "https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text="

    # Extract Last day's daily level ohlc data
    today = date.today()
    date_from = prev_weekday(today)
    interval = '5minute'
    prev_day_interval = 'day'
    previous_day_data = kite.historical_data(instrument_token=token[0], from_date=date_from, to_date=date_from,
                                             interval=prev_day_interval)
    previous_day_data = pd.DataFrame(previous_day_data)
    previous_day_data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    # previous_day_data.to_csv("previous_day_data_" + name + '.csv')

    # Sleep till 9:15
    time_now = datetime.now()
    script_start_string = 'Master Script Started at ' + str(time_now)
    requests.get(bot_link + script_start_string)
    print(script_start_string, flush=True)

    # Decision Engine Starts

    # Set Initial Pointers Value
    order_status = 'Exit'
    order_signal = ''
    order_price = 0.0
    target = 0.0
    stop_loss = 0.0

    if datetime.now()>= datetime.now().replace(hour=9, minute=20, second=5):
        master_data = kite.historical_data(instrument_token=token[0], from_date=today, to_date=today,
                                           interval=interval)
        master_data = pd.DataFrame(master_data)
        master_data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        entry_high_target = round(max(master_data.High),1)
        entry_low_target = round(min(master_data.Low),1)

    else:

        entry_high_target = previous_day_data.High[0]
        entry_low_target = previous_day_data.Low[0]


    prev_day_close = previous_day_data.Close[0]
    long_count = 0
    short_count = 0
    trade_count = 0
    semi_target_flag = 0
    profit = 0
    min_gap = 0.000001
    candle_error = 0.00075
    target_buffer_multiplier = 0.0
    min_target = 5000
    semi_target_multiplier = 0.004
    quantity = 1 if lot_size < 100 else round(lot_size / 100)
    last_saved_time = datetime.now().replace(hour=9, minute=15, second=0)
    skip_date = datetime.strptime('2019-08-06', '%Y-%m-%d').date()
    pivots = pivotpoints(previous_day_data)

    # Initialising variables for Order Management
    current_order_parameters = ['order_id',
                                'order_type',
                                'transaction_type',
                                'parent_order_id',
                                'price',
                                'trigger_price',
                                'status']
    current_order = pd.DataFrame(columns=['order_id',
                                          'order_type',
                                          'transaction_type',
                                          'parent_order_id',
                                          'price',
                                          'trigger_price',
                                          'status'])
    kite_orders = pd.DataFrame(kite.orders())

    Trade_Dataset = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Year', 'DatePart',
                                          'Order_Status', 'Order_Signal', 'Order_Price', 'Target', 'Stop_Loss',
                                          'Hour', 'Minute'])
    count = 0
    counter = 0
    temp_count = 0
    message = 'Entering into the Strategy'
    requests.get(bot_link + message)


    while True:

        if datetime.now() >= datetime.now().replace(hour=9, minute=20, second=5):

            # Get Live OHLC data from Kite from 9:20:05
            try:
                master_data = kite.historical_data(instrument_token=token[0], from_date=today, to_date=today,
                                             interval=interval)
                master_data = pd.DataFrame(master_data)
                master_data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            except:
                time.sleep(1)
                continue

            # Datetime manipulation in data
            master_data['Date'] = [datetime.strptime(datetime.strftime(i, '%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                            for i in master_data['Date']]

            if master_data['Date'][len(master_data) - 1] != last_saved_time:

                # Get the last full candle into strategy
                data = master_data.iloc[[- 2]]
                data = data.reset_index(drop=True)
                last_saved_time = master_data['Date'][len(master_data) - 1]

                # Selecting Tradable Day and Reset Day High and Day Low
                if data.Date[0].hour == 9 and data.Date[0].minute == 15:
                    message = name + ': Entered into 9.15 Criteria\nOpen: ' + str(data.Open[0]) + '\nHigh: ' + str(
                        data.High[0]) + '\nLow: ' + str(data.Low[0]) + '\nClose: ' + str(data.Close[0])
                    requests.get(bot_link + message)
                    day_flag = 'selected' if abs(data.Open[0] - prev_day_close) > (
                                prev_day_close * min_gap) else 'not selected'
                    skip_date = data.DatePart[0] if day_flag == 'not selected' else skip_date
                    entry_high_target = data.High[0]
                    entry_low_target = data.Low[0]

                    # Check if Marubozu Candle
                    if day_flag == 'selected':
                        trade_count = 1 if ((data.Open[0] - data.Low[0]) <= data.Open[0] * candle_error or
                                            (data.High[0] - data.Close[0]) <= data.Open[0] * candle_error or
                                            (data.High[0] - data.Open[0]) <= data.Open[0] * candle_error or
                                            (data.Close[0] - data.Low[0]) <= data.Open[
                                                0] * candle_error) else trade_count
                        if trade_count == 1:
                            message = 'Stock Name: ' + name + '\nMarubuzu Candle Identified'
                            requests.get(bot_link + message)
                            if ((data.Open[0] - data.Low[0]) <= data.Open[0] * candle_error or
                                    (data.High[0] - data.Close[0]) <= data.Open[0] * candle_error):
                                order_status = 'Sub - Entry'
                                order_signal = 'BUY'
                                semi_target_flag = 0
                                order_price = round(data.Close[0], 1)
                                stop_loss = entry_low_target - round((target_buffer_multiplier * order_price), 1)
                                profit = profit - order_price

                                # Calculating Target
                                deltas = [indicator - order_price for indicator in pivots]
                                pos_deltas = [delta for delta in deltas if delta > (order_price * 0.004)]
                                min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                                target = round(min_pos_delta + order_price + (order_price * target_buffer_multiplier),1)

                                # Calculating Semi Target
                                semi_target = round(order_price + order_price * semi_target_multiplier, 1)

                                # Print Pointers
                                # data.Order_Status[0] = order_status
                                # data.Order_Signal[0] = order_signal
                                # data.Order_Price[0] = order_price
                                # data.Target[0] = target
                                # data.Stop_Loss[0] = stop_loss

                                # live_order_data = pd.DataFrame({'order_id': [trade_count],
                                #                                 'transaction_type': [order_signal],
                                #                                 'price': [order_price],
                                #                                 'stoploss': [stop_loss],
                                #                                 'target': [target],
                                #                                 'semi_target': [semi_target],
                                #                                 'status': [np.nan],
                                #                                 'semi-target_status': [0],
                                #                                 'target_status': [0],
                                #                                 'stoploss_status': [0],
                                #                                 'day_high': [entry_high_target],
                                #                                 'day_low': [entry_low_target]})
                                # live_order_data.to_csv(live_order_file_name, index=False)

                                # Place the order
                                order_id = kite.place_order(tradingsymbol=name,
                                                            variety='bo',
                                                            exchange=kite.EXCHANGE_NSE,
                                                            transaction_type=order_signal,
                                                            quantity=quantity,
                                                            price=order_price,
                                                            order_type=kite.ORDER_TYPE_LIMIT,
                                                            product=kite.PRODUCT_MIS,
                                                            stoploss=stop_loss,
                                                            squareoff=target)

                                current_order = current_order.append({'order_id': order_id,
                                                                      'order_type': 'LIMIT',
                                                                      'transaction_type': order_signal,
                                                                      'parent_order_id': 'NA',
                                                                      'price': order_price,
                                                                      'trigger_price': 0,
                                                                      'status': 'OPEN'}, ignore_index=True)

                                message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                                    order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                requests.get(bot_link + message)

                            else:
                                order_status = 'Sub - Entry'
                                order_signal = 'SELL'
                                semi_target_flag = 0
                                order_price = round(data.Close[0], 1)
                                stop_loss = entry_high_target + round((target_buffer_multiplier * order_price), 1)
                                profit = profit + order_price

                                # Calculating Target
                                deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                                max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                                target = round(order_price + max_neg_delta - (order_price * target_buffer_multiplier),1)

                                # Calculating Semi Target
                                semi_target = round(order_price - order_price * semi_target_multiplier, 1)

                                # Print Pointers
                                # data.Order_Status[0] = order_status
                                # data.Order_Signal[0] = order_signal
                                # data.Order_Price[0] = order_price
                                # data.Target[0] = target
                                # data.Stop_Loss[0] = stop_loss
                                #
                                # live_order_data = pd.DataFrame({'order_id': [trade_count],
                                #                                 'transaction_type': [order_signal],
                                #                                 'price': [order_price],
                                #                                 'stoploss': [stop_loss],
                                #                                 'target': [target],
                                #                                 'semi_target': [semi_target],
                                #                                 'status': [np.nan],
                                #                                 'semi-target_status': [0],
                                #                                 'target_status': [0],
                                #                                 'stoploss_status': [0],
                                #                                 'day_high': [entry_high_target],
                                #                                 'day_low': [entry_low_target]})
                                # live_order_data.to_csv(live_order_file_name, index=False)

                                # Place the order
                                order_id = kite.place_order(tradingsymbol=name,
                                                            variety='bo',
                                                            exchange=kite.EXCHANGE_NSE,
                                                            transaction_type=order_signal,
                                                            quantity=quantity,
                                                            price=order_price,
                                                            order_type=kite.ORDER_TYPE_LIMIT,
                                                            product=kite.PRODUCT_MIS,
                                                            stoploss=stop_loss,
                                                            squareoff=target)

                                current_order = current_order.append({'order_id': order_id,
                                                                      'order_type': 'LIMIT',
                                                                      'transaction_type': order_signal,
                                                                      'parent_order_id': 'NA',
                                                                      'price': order_price,
                                                                      'trigger_price': 0,
                                                                      'status': 'OPEN'}, ignore_index=True)
                                message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                                    order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                requests.get(bot_link + message)

                elif data.Date[0].hour == 15 and data.Date[0].minute == 20:

                    # Check If Open Order Exists at 3:20
                    if order_status == 'Entry':

                        # Check if the open order is a long entry
                        if order_signal == 'BUY':
                            order_status = 'Exit'
                            order_signal = 'SELL'
                            order_price = round(data.Close[0], 1)
                            long_count = 1
                            short_count = 0
                            semi_target_flag = 0
                            profit = profit + order_price

                            # Print Pointers
                            # data.Order_Status[0] = order_status
                            # data.Order_Signal[0] = order_signal
                            # data.Order_Price[0] = order_price

                            # live_order_data = pd.read_csv(live_order_file_name)
                            # live_order_data['stoploss_status'][len(live_order_data) - 1] = 1
                            # live_order_data.to_csv(live_order_file_name, index=False)

                            #Manually Exit From Trade

                            # No Action is taken as Kite handles it
                            message = 'Stock Name: ' + name + '\n Long Exit ---' + '\nOrder Price: ' + str(
                                order_price) + '\nRemarks: Exit At 3:25 PM'
                            requests.get(bot_link + message)

                        # Check If the open order is a short entry
                        elif order_signal == 'SELL':
                            order_status = 'Exit'
                            order_signal = 'BUY'
                            order_price = round(data.Close[0], 1)
                            long_count = 0
                            short_count = 1
                            semi_target_flag = 0
                            profit = profit - order_price

                            # Print Pointers
                            # data.Order_Status[0] = order_status
                            # data.Order_Signal[0] = order_signal
                            # data.Order_Price[0] = order_price
                            #
                            # live_order_data = pd.read_csv(live_order_file_name)
                            # live_order_data['stoploss_status'][len(live_order_data) - 1] = 1

                            # No Action is taken as Kite handles it
                            message = 'Stock Name: ' + name + '\n Short Exit ---' + '\nOrder Price: ' + str(
                                order_price) + '\nRemarks: Exit At 3:25 PM'
                            requests.get(bot_link + message)
                            print('Stock Name: ' + name + '\n Short Exit ---')
                            print('Order Price: ' + str(order_price))
                            print('Remarks: Exit At 3:25 PM')

                # Reset Pointers at 3:30 PM
                elif data.Date[0].hour == 15 and data.Date[0].minute == 25:
                    # prev_day_close = data.Close[0]
                    long_count = 0
                    short_count = 0
                    trade_count = 0
                    skip_date = data.DatePart[0]
                    message = 'Stock Name: ' + name + '\nRemarks: Enough For Today'
                    requests.get(bot_link + message)

                # Iterate over all the data points for the dates that have been selected by Gap Up/Down Condition
                elif order_status == 'Exit' and trade_count == 0:

                    # Long Entry Action
                    if data.Close[0] > entry_high_target:
                        order_status = 'Sub - Entry'
                        order_signal = 'BUY'
                        trade_count = trade_count + 1
                        semi_target_flag = 0
                        order_price = round(data.Close[0], 1)
                        stop_loss = entry_low_target - round((target_buffer_multiplier * order_price), 1)
                        profit = profit - order_price

                        # Calculating Target
                        deltas = [indicator - order_price for indicator in pivots]
                        pos_deltas = [delta for delta in deltas if delta > (order_price * 0.004)]
                        min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                        target = round(min_pos_delta + order_price + (order_price * target_buffer_multiplier),
                                       1)

                        # Calculating Semi Target
                        semi_target = round(order_price + order_price * semi_target_multiplier, 1)

                        # Place the order
                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=order_signal,
                                                    quantity=quantity,
                                                    price=order_price,
                                                    order_type=kite.ORDER_TYPE_LIMIT,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=stop_loss,
                                                    squareoff=target)

                        current_order = current_order.append({'order_id': order_id,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': order_signal,
                                                              'parent_order_id': 'NA',
                                                              'price': order_price,
                                                              'trigger_price': 0,
                                                              'status': 'OPEN'}, ignore_index=True)

                        message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                            order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                        requests.get(bot_link + message)


                    # Short Entry Action
                    elif data.Close[0] < entry_low_target:
                        order_status = 'Sub - Entry'
                        order_signal = 'SELL'
                        semi_target_flag = 0
                        trade_count = trade_count + 1
                        order_price = round(data.Close[0], 1)
                        stop_loss = entry_high_target + round((target_buffer_multiplier * order_price), 1)
                        profit = profit + order_price

                        # Calculating Target
                        deltas = [round(indicator, 1) - order_price for indicator in pivots]
                        neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                        max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                        target = round(order_price + max_neg_delta - (order_price * target_buffer_multiplier),
                                       1)

                        # Calculating Semi Target
                        semi_target = round(order_price - order_price * semi_target_multiplier, 1)

                        # Place an Order
                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=order_signal,
                                                    quantity=quantity,
                                                    price=order_price,
                                                    order_type=kite.ORDER_TYPE_LIMIT,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=stop_loss,
                                                    squareoff=target)

                        current_order = current_order.append({'order_id': order_id,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': order_signal,
                                                              'parent_order_id': 'NA',
                                                              'price': order_price,
                                                              'trigger_price': 0,
                                                              'status': 'OPEN'}, ignore_index=True)

                        message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                            order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                        requests.get(bot_link + message)


                entry_high_target = round(max(entry_high_target, data.High[0]), 1)
                entry_low_target = round(min(entry_low_target, data.Low[0]), 1)

            elif order_status == 'Exit' and trade_count >= 1:

                # Get the last full candle into strategy
                data = master_data.loc[len(master_data) - 1, :]
                data = data.reset_index(drop=True)

                # Long Entry
                if (data.Close[0] > entry_high_target) and (long_count == 0):
                    order_status = 'Sub - Entry'
                    order_signal = 'BUY'
                    semi_target_flag = 0
                    trade_count = trade_count + 1
                    order_price = entry_high_target
                    stop_loss = entry_low_target - round((target_buffer_multiplier * order_price), 1)
                    profit = profit - order_price

                    # Calculating Target
                    deltas = [indicator - order_price for indicator in pivots]
                    pos_deltas = [delta for delta in deltas if delta > (order_price * 0.004)]
                    min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                    target = round(min_pos_delta + order_price + (order_price * target_buffer_multiplier), 1)

                    # Calculating Semi Target
                    semi_target = round(order_price + order_price * semi_target_multiplier, 1)

                    # Print Pointers
                    # data.Order_Status[0] = order_status
                    # data.Order_Signal[0] = order_signal
                    # data.Order_Price[0] = order_price
                    # data.Target[0] = target
                    # data.Stop_Loss[0] = stop_loss
                    #
                    # # Update Live Order Data
                    # if path.exists(live_order_file_name):
                    #     live_order_data = pd.read_csv(live_order_file_name)
                    #     live_order_data_subset = pd.DataFrame({'order_id': [trade_count],
                    #                                            'transaction_type': [order_signal],
                    #                                            'price': [order_price],
                    #                                            'stoploss': [stop_loss],
                    #                                            'target': [target],
                    #                                            'semi_target': [semi_target],
                    #                                            'status': [np.nan],
                    #                                            'semi-target_status': [0],
                    #                                            'target_status': [0],
                    #                                            'stoploss_status': [0],
                    #                                            'day_high': [entry_high_target],
                    #                                            'day_low': [entry_low_target]})
                    #     live_order_data = live_order_data.append(live_order_data_subset)
                    #     live_order_data.reset_index(drop=True)
                    # else:
                    #     live_order_data = pd.DataFrame({'order_id': [trade_count],
                    #                                     'transaction_type': [order_signal],
                    #                                     'price': [order_price],
                    #                                     'stoploss': [stop_loss],
                    #                                     'target': [target],
                    #                                     'semi_target': [semi_target],
                    #                                     'status': [np.nan],
                    #                                     'semi-target_status': [0],
                    #                                     'target_status': [0],
                    #                                     'stoploss_status': [0],
                    #                                     'day_high': [entry_high_target],
                    #                                     'day_low': [entry_low_target]})
                    #
                    # live_order_data.to_csv(live_order_file_name, index=False)

                    # Place the order
                    order_id = kite.place_order(tradingsymbol=name,
                                                variety='bo',
                                                exchange=kite.EXCHANGE_NSE,
                                                transaction_type=order_signal,
                                                quantity=quantity,
                                                price=order_price,
                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                product=kite.PRODUCT_MIS,
                                                stoploss=stop_loss,
                                                squareoff=target)

                    current_order = current_order.append({'order_id': order_id,
                                                          'order_type': 'LIMIT',
                                                          'transaction_type': order_signal,
                                                          'parent_order_id': 'NA',
                                                          'price': order_price,
                                                          'trigger_price': 0,
                                                          'status': 'OPEN'}, ignore_index=True)

                    message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                        order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                    requests.get(bot_link + message)

                # Short Entry
                elif (data.Close[0] < entry_low_target) and (short_count == 0):
                    order_status = 'Sub - Entry'
                    order_signal = 'SELL'
                    semi_target_flag = 0
                    trade_count = trade_count + 1
                    order_price = entry_low_target
                    stop_loss = entry_high_target + round((target_buffer_multiplier * order_price), 1)
                    profit = profit + order_price

                    # Calculating Target
                    deltas = [indicator - order_price for indicator in pivots]
                    neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                    max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                    target = round(order_price + max_neg_delta - (order_price * target_buffer_multiplier), 1)

                    # Calculating Semi Target
                    semi_target = round(order_price - order_price * semi_target_multiplier, 1)

                    # Place the order
                    order_id = kite.place_order(tradingsymbol=name,
                                                variety='bo',
                                                exchange=kite.EXCHANGE_NSE,
                                                transaction_type=order_signal,
                                                quantity=quantity,
                                                price=order_price,
                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                product=kite.PRODUCT_MIS,
                                                stoploss=stop_loss,
                                                squareoff=target)

                    current_order = current_order.append({'order_id': order_id,
                                                          'order_type': 'LIMIT',
                                                          'transaction_type': order_signal,
                                                          'parent_order_id': 'NA',
                                                          'price': order_price,
                                                          'trigger_price': 0,
                                                          'status': 'OPEN'}, ignore_index=True)

                    message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                        order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                    requests.get(bot_link + message)

            elif order_status == 'Sub - Entry':

                kite_orders = pd.DataFrame(kite.orders())
                if kite_orders['status'][kite_orders['order_id'] == current_order.at[0, 'order_id']].values[0] == 'REJECTED':
                    message = name + ': Insufficient Fund'
                    requests.get(bot_link + message)
                    break

                elif kite_orders['status'][kite_orders['order_id'] == current_order.at[0, 'order_id']].values[0] == 'COMPLETE':

                    # change current order status
                    current_order = current_order.reset_index(drop=True)
                    current_order.at[0, 'status'] = 'COMPLETE'

                    # append stoploss and target orders
                    current_order = current_order.append(kite_orders.loc[kite_orders['parent_order_id'] == current_order.at[0, 'order_id'], current_order_parameters])
                    current_order = current_order.reset_index(drop=True)
                    order_status = 'Entry'

                    # send message to telegram
                    message = (str(current_order.at[0, 'transaction_type']) + " order executed for "
                               + name + " at " + str(current_order.at[0, 'price']))
                    requests.get(bot_link + message)

                elif kite_orders['status'][kite_orders['order_id'] == current_order.at[0, 'order_id']].values[0] == 'OPEN':

                    if semi_target_flag == 0:

                        # Cancel Existing Order and take reverse order if order is open in SL

                        # Cancel Long Entry & Place reverse order
                        if order_signal == 'BUY' and data.Close[0] <= stop_loss:
                            # cancel last placed order
                            kite.cancel_order(variety='bo',
                                              order_id=current_order.at[0, 'order_id'].values[0])

                            # clear previous orders
                            current_order = current_order[0:0]

                            ## Take Reverse Entry
                            # set pointers
                            long_count = 1
                            short_count = 0
                            order_status = 'Sub - Entry'
                            order_signal = 'SELL'
                            semi_target_flag = 0
                            trade_count = trade_count + 1
                            order_price = stop_loss
                            stop_loss = entry_high_target + round((target_buffer_multiplier * order_price), 1)
                            profit = profit + order_price

                            # Calculating Target
                            deltas = [indicator - order_price for indicator in pivots]
                            neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                            max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                            target = round(order_price + max_neg_delta - (order_price * target_buffer_multiplier), 1)

                            # Calculating Semi Target
                            semi_target = round(order_price - order_price * semi_target_multiplier, 1)

                            # Place the order
                            order_id = kite.place_order(tradingsymbol=name,
                                                        variety='bo',
                                                        exchange=kite.EXCHANGE_NSE,
                                                        transaction_type=order_signal,
                                                        quantity=quantity,
                                                        price=order_price,
                                                        order_type=kite.ORDER_TYPE_LIMIT,
                                                        product=kite.PRODUCT_MIS,
                                                        stoploss=stop_loss,
                                                        squareoff=target)

                            current_order = current_order.append({'order_id': order_id,
                                                                  'order_type': 'LIMIT',
                                                                  'transaction_type': order_signal,
                                                                  'parent_order_id': 'NA',
                                                                  'price': order_price,
                                                                  'trigger_price': 0,
                                                                  'status': 'OPEN'}, ignore_index=True)

                            message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                                order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                            requests.get(bot_link + message)

                        # Cancel Short Entry & Place reverse order
                        elif order_signal == 'SELL' and data.Close[0] >= stop_loss:
                            # cancel last placed order
                            kite.cancel_order(variety='bo',
                                              order_id=current_order.at[0, 'order_id'].values[0])

                            # clear previous orders
                            current_order = current_order[0:0]

                            ## Take Reverse Entry
                            # set pointers
                            long_count = 0
                            short_count = 1
                            order_status = 'Sub - Entry'
                            order_signal = 'BUY'
                            semi_target_flag = 0
                            trade_count = trade_count + 1
                            order_price = entry_high_target
                            stop_loss = entry_low_target - round((target_buffer_multiplier * order_price), 1)
                            profit = profit - order_price

                            # Calculating Target
                            deltas = [indicator - order_price for indicator in pivots]
                            pos_deltas = [delta for delta in deltas if delta > (order_price * 0.004)]
                            min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                            target = round(min_pos_delta + order_price + (order_price * target_buffer_multiplier), 1)

                            # Calculating Semi Target
                            semi_target = round(order_price + order_price * semi_target_multiplier, 1)

                            # Place the order
                            order_id = kite.place_order(tradingsymbol=name,
                                                        variety='bo',
                                                                 exchange=kite.EXCHANGE_NSE,
                                                        transaction_type=order_signal,
                                                        quantity=quantity,
                                                        price=order_price,
                                                        order_type=kite.ORDER_TYPE_LIMIT,
                                                        product=kite.PRODUCT_MIS,
                                                        stoploss=stop_loss,
                                                        squareoff=target)

                            current_order = current_order.append({'order_id': order_id,
                                                                  'order_type': 'LIMIT',
                                                                  'transaction_type': order_signal,
                                                                  'parent_order_id': 'NA',
                                                                  'price': order_price,
                                                                  'trigger_price': 0,
                                                                  'status': 'OPEN'}, ignore_index=True)

                            message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                                order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                            requests.get(bot_link + message)

                        # Modify SL in case of Semi Target is hit

                        # Modify SL in Long Entry
                        elif order_signal == 'BUY' and data.Close[0] >= (semi_target + (order_price * 0.0005)):
                            # modify stoploss
                            stop_loss = semi_target
                            # set pointers
                            semi_target_flag = 1

                        # Modify SL in Short Entry
                        elif order_signal == 'SELL' and data.Close[0] <= (semi_target - (order_price * 0.0005)):
                            # modify stoploss
                            stop_loss = semi_target
                            # set pointers
                            semi_target_flag = 1

                    elif semi_target_flag == 1:

                        # Cancel existing order if target is hit while Open

                        # Cancel Long Entry
                        if order_signal == 'BUY' and data.Close[0] >= target:
                            # cancel last placed order
                            kite.cancel_order(variety='bo',
                                              order_id=current_order.at[0, 'order_id'].values[0])

                            # clear previous orders
                            current_order = current_order[0:0]

                            # set pointers
                            order_status = 'Exit'
                            long_count = 1
                            short_count = 0
                            semi_target_flag = 0

                        # Cancel Short Entry
                        elif order_signal == 'SELL' and data.Close[0] <= target:
                            # cancel last placed order
                            kite.cancel_order(variety='bo',
                                              order_id=current_order.at[0, 'order_id'].values[0])

                            # clear previous orders
                            current_order = current_order[0:0]

                            # set pointers
                            order_status = 'Exit'
                            long_count = 0
                            short_count = 1
                            semi_target_flag = 0

                        # Cancel the existing order and place reverse order in case of SL(semi target) is hit

                        # Cancel Long Entry and place reverse entry
                        elif order_signal == 'BUY' and data.Close[0] <= stop_loss:
                            # cancel last placed order
                            kite.cancel_order(variety='bo',
                                              order_id=current_order.at[0, 'order_id'].values[0])

                            # clear previous orders
                            current_order = current_order[0:0]

                            # set pointers
                            long_count = 1
                            short_count = 0
                            order_status = 'Sub - Entry'
                            order_signal = 'SELL'
                            semi_target_flag = 0
                            trade_count = trade_count + 1
                            order_price = stop_loss
                            stop_loss = entry_high_target + round((target_buffer_multiplier * order_price), 1)
                            profit = profit + order_price

                            # Calculating Target
                            deltas = [indicator - order_price for indicator in pivots]
                            neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                            max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                            target = round(order_price + max_neg_delta - (order_price * target_buffer_multiplier), 1)

                            # Calculating Semi Target
                            semi_target = round(order_price - order_price * semi_target_multiplier, 1)

                            # Place the order
                            order_id = kite.place_order(tradingsymbol=name,
                                                        variety='bo',
                                                        exchange=kite.EXCHANGE_NSE,
                                                        transaction_type=order_signal,
                                                        quantity=quantity,
                                                        price=order_price,
                                                        order_type=kite.ORDER_TYPE_LIMIT,
                                                        product=kite.PRODUCT_MIS,
                                                        stoploss=stop_loss,
                                                        squareoff=target)

                            current_order = current_order.append({'order_id': order_id,
                                                                  'order_type': 'LIMIT',
                                                                  'transaction_type': order_signal,
                                                                  'parent_order_id': 'NA',
                                                                  'price': order_price,
                                                                  'trigger_price': 0,
                                                                  'status': 'OPEN'}, ignore_index=True)

                            message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                                order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                            requests.get(bot_link + message)

                        # Cancel Short Entry and place reverse entry
                        elif order_signal == 'SELL' and data.Close[0] >= stop_loss:
                            # cancel last placed order
                            kite.cancel_order(variety='bo',
                                              order_id=current_order.at[0, 'order_id'].values[0])

                            # clear previous orders
                            current_order = current_order[0:0]

                            # set pointers
                            long_count = 0
                            short_count = 1
                            order_status = 'Sub - Entry'
                            order_signal = 'BUY'
                            semi_target_flag = 0
                            trade_count = trade_count + 1
                            order_price = stop_loss
                            stop_loss = entry_low_target - round((target_buffer_multiplier * order_price), 1)
                            profit = profit - order_price

                            # Calculating Target
                            deltas = [indicator - order_price for indicator in pivots]
                            pos_deltas = [delta for delta in deltas if delta > (order_price * 0.004)]
                            min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                            target = round(min_pos_delta + order_price + (order_price * target_buffer_multiplier), 1)

                            # Calculating Semi Target
                            semi_target = round(order_price + order_price * semi_target_multiplier, 1)

                            # Place the order
                            order_id = kite.place_order(tradingsymbol=name,
                                                        variety='bo',
                                                        exchange=kite.EXCHANGE_NSE,
                                                        transaction_type=order_signal,
                                                        quantity=quantity,
                                                        price=order_price,
                                                        order_type=kite.ORDER_TYPE_LIMIT,
                                                        product=kite.PRODUCT_MIS,
                                                        stoploss=stop_loss,
                                                        squareoff=target)

                            current_order = current_order.append({'order_id': order_id,
                                                                  'order_type': 'LIMIT',
                                                                  'transaction_type': order_signal,
                                                                  'parent_order_id': 'NA',
                                                                  'price': order_price,
                                                                  'trigger_price': 0,
                                                                  'status': 'OPEN'}, ignore_index=True)
                            message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                                order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                            requests.get(bot_link + message)

            elif order_status == 'Entry':

                kite_orders = pd.DataFrame(kite.orders())
                # check if stoploss is hit
                if kite_orders['status'][kite_orders['order_id'] == current_order['order_id'][(current_order['trigger_price'] != 0) &
                                                                                              (current_order['transaction_type'] != current_order.at[0, 'transaction_type'])].values[0]].values[0] == 'COMPLETE':

                    # Place reverse entry

                    # In case of Long Entry
                    if order_signal == 'BUY':

                        #Set pointers
                        long_count = 1
                        short_count = 0
                        order_status = 'Sub - Entry'
                        order_signal = 'SELL'
                        semi_target_flag = 0
                        trade_count = trade_count + 1
                        order_price = stop_loss
                        stop_loss = entry_high_target + round((target_buffer_multiplier * order_price), 1)
                        profit = profit + order_price

                        # Calculating Target
                        deltas = [indicator - order_price for indicator in pivots]
                        neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                        max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                        target = round(order_price + max_neg_delta - (order_price * target_buffer_multiplier), 1)

                        # Calculating Semi Target
                        semi_target = round(order_price - order_price * semi_target_multiplier, 1)

                        # Place the order
                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=order_signal,
                                                    quantity=quantity,
                                                    price=order_price,
                                                    order_type=kite.ORDER_TYPE_LIMIT,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=stop_loss,
                                                    squareoff=target)

                        current_order = current_order.append({'order_id': order_id,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': order_signal,
                                                              'parent_order_id': 'NA',
                                                              'price': order_price,
                                                              'trigger_price': 0,
                                                              'status': 'OPEN'}, ignore_index=True)

                        message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                            order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                        requests.get(bot_link + message)

                    # In case of Short Entry
                    elif order_signal == 'SELL':

                        # Set Pointers
                        long_count = 0
                        short_count = 1
                        order_status = 'Sub - Entry'
                        order_signal = 'BUY'
                        semi_target_flag = 0
                        trade_count = trade_count + 1
                        order_price = stop_loss
                        stop_loss = entry_low_target - round((target_buffer_multiplier * order_price), 1)
                        profit = profit - order_price

                        # Calculating Target
                        deltas = [indicator - order_price for indicator in pivots]
                        pos_deltas = [delta for delta in deltas if delta > (order_price * 0.004)]
                        min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                        target = round(min_pos_delta + order_price + (order_price * target_buffer_multiplier), 1)

                        # Calculating Semi Target
                        semi_target = round(order_price + order_price * semi_target_multiplier, 1)

                        # Place the order
                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=order_signal,
                                                    quantity=quantity,
                                                    price=order_price,
                                                    order_type=kite.ORDER_TYPE_LIMIT,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=stop_loss,
                                                    squareoff=target)

                        current_order = current_order.append({'order_id': order_id,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': order_signal,
                                                              'parent_order_id': 'NA',
                                                              'price': order_price,
                                                              'trigger_price': 0,
                                                              'status': 'OPEN'}, ignore_index=True)
                        message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                            order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                        requests.get(bot_link + message)


                # check if target is hit
                if kite_orders['status'][kite_orders['order_id'] == current_order['order_id'][(current_order['trigger_price'] == 0) &
                                                                                              (current_order['transaction_type'] != current_order.at[0, 'transaction_type'])].values[0]].values[0] == 'COMPLETE':
                    order_status = 'Exit'

                    if order_signal == 'BUY':
                        long_count = 1
                        short_count = 0

                    elif order_signal == 'SELL':
                        long_count = 0
                        short_count = 1


                # check if Semi target is hit
                data = master_data.loc[len(master_data) - 1, :]
                data = data.reset_index(drop=True)

                if order_signal == 'BUY' and data.Close[0] >= (semi_target + (order_price * 0.0005)) and \
                    semi_target_flag == 0:

                    # modify stoploss
                    order_id = kite.modify_order(variety='bo',
                                                 parent_order_id=current_order.at[0, 'order_id'],
                                                 order_id=current_order['order_id'][current_order['trigger_price'] != 0].values[0],
                                                 order_type=kite.ORDER_TYPE_SL,
                                                 trigger_price=semi_target)

                    semi_target_flag = 1

if __name__ == '__main__':

    # Get the input parameters and start the parallel processing
    # path = '/home/ubuntu/APT/APT/Live_Trading'
    path = 'F:\DevAPT\APT\Live_Trading'
    config_path = path + '/config.ini'
    os.chdir(path)
    # name = sys.argv[1]
    # token = [int(sys.argv[2])]
    # access_token = sys.argv[3]
    # lot_size = [int(sys.argv[4])]
    name = 'IBULHSGFIN'
    token = [7712001]
    access_token = 'AW9FrgcgU5SpgxBwxNkC7FjGbdlTwaVL'
    lot_size = 1200
    stock_name_string = 'Stock Name: ' + name
    requests.get(
        "https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + \
        stock_name_string)
    print(stock_name_string, flush=True)
    start(name, token, access_token, lot_size)





