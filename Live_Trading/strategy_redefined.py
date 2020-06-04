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
    s3_fibonacci = pivotpoint - (data['High'][0] - data['Low'][0])

    r1_simple = (pivotpoint * 2) - data['Low'][0]
    r1_fibonacci = pivotpoint + (0.382 * (data['High'][0] - data['Low'][0]))
    r2_simple = pivotpoint + (data['High'][0] - data['Low'][0])
    r2_fibonacci = pivotpoint + (0.618 * (data['High'][0] - data['Low'][0]))
    r3_simple = pivotpoint + (2 * (data['High'][0] - data['Low'][0]))
    r3_fibonacci = pivotpoint + (data['High'][0] - data['Low'][0])

    pivots = list([s3_simple,s2_simple,s2_fibonacci,s1_simple,s1_fibonacci,pivotpoint,
                   r1_simple,r1_fibonacci,r2_simple,r2_fibonacci,r3_simple])
    return pivots

##Function to get previous Weekday
###############################################################
def prev_weekday(adate):
    holiday_list = ['2020-10-02', '2020-11-16', '2020-11-30', '2020-12-25']
    adate -= timedelta(days=1)
    if adate.strftime('%Y-%m-%d') in holiday_list:
        adate -= timedelta(days=1)
    while adate.weekday() > 4:
        adate -= timedelta(days=1)
    return adate



##Main Script Flow
def start(name, token, access_token, lot_size, scenario):

    # Establish connection with Kiteconnect
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
    previous_day_data = kite.historical_data(instrument_token=token[0], from_date=date_from, to_date=date_from,
                                             interval=interval)
    previous_day_data = pd.DataFrame(previous_day_data)
    previous_day_data.columns = ['Close', 'Date', 'High', 'Low', 'Open', 'Volume']
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

    entry_high_target = max(previous_day_data.High)
    entry_low_target = min(previous_day_data.Low)

    prev_day_close = previous_day_data.Close[len(previous_day_data) - 1]
    print('Previous Day High = ' + str(entry_high_target))
    print('Previous Day Low = ' + str(entry_low_target))
    print('Previous Day Close = ' + str(prev_day_close))
    print('Previous Day Open = ' + str(previous_day_data.Open[0]))

    long_count = 0
    short_count = 0
    trade_count = 0
    semi_target_flag = 0
    profit = 0
    min_gap = 0.00000
    candle_error = 0.000
    target_buffer_multiplier = 0.0
    # min_target = 5000
    semi_target_multiplier = 0.004
    quantity = 10
    last_saved_time = datetime.now().replace(hour=9, minute=15, second=0)
    skip_date = datetime.strptime('2019-08-06', '%Y-%m-%d').date()
    previous_day_data = pd.DataFrame({'Close': [prev_day_close],
                                      'Date': [date_from],
                                      'High': [entry_high_target],
                                      'Low': [entry_low_target],
                                      'Open': [previous_day_data.Open[0]]})
    print(previous_day_data)
    pivots = pivotpoints(previous_day_data)
    print(pivots)

    # Initialising variables for Order Management
    current_order = pd.DataFrame(columns=['order_id',
                                          'order_type',
                                          'transaction_type',
                                          'parent_order_id',
                                          'price',
                                          'trigger_price',
                                          'status'])

    count = 0
    counter = 0
    temp_count = 0
    bot_pointer = 0
    data_pointer = 0
    live_order_flag = 0
    message = 'Entering into the Strategy'
    requests.get(bot_link + message)


    while True:

        # Get Live OHLC data from Kite
        try:
            master_data = kite.historical_data(instrument_token=token[0], from_date=today, to_date=today,
                                               interval=interval)
            master_data = pd.DataFrame(master_data)
            master_data.columns = ['Close', 'Date', 'High', 'Low', 'Open', 'Volume']
        except:
            time.sleep(1)
            continue

        # Datetime manipulation in data
        master_data['Date'] = [datetime.strptime(datetime.strftime(i, '%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                                   for i in master_data['Date']]

        #Select Pointers according to data
        data_pointer = len(master_data)
        print('Data Pointer = ' + str(data_pointer))
        bot_pointer = bot_pointer + 1 if bot_pointer < data_pointer else bot_pointer
        
        if bot_pointer > data_pointer:
            bot_pointer = data_pointer

        # Run Strategy at least after 9:20
        if data_pointer >= 2:

            #Select Entry High - Low according to pointers
            if bot_pointer >= 2:
                entry_high_target = max(entry_high_target, master_data.High[bot_pointer-2]) if bot_pointer < data_pointer else entry_high_target
                entry_low_target = min(entry_low_target, master_data.Low[bot_pointer-2]) if bot_pointer < data_pointer else entry_low_target
                print('Bot Pointer = ' + str(bot_pointer))
                print('day High = ' + str(entry_high_target))
                print('day Low = ' + str(entry_low_target))
            
            # Select Data for analysis
            data = master_data.iloc[[bot_pointer-1]]
            data = data.reset_index(drop=True)

            # Selecting Tradable Day and Reset Day High and Day Low
            if data.Date[0].hour == 9 and data.Date[0].minute == 15:
                message = name + ': Entered into 9.15 Criteria\nOpen: ' + str(data.Open[0]) + '\nHigh: ' + str(
                    data.High[0]) + '\nLow: ' + str(data.Low[0]) + '\nClose: ' + str(data.Close[0])
                requests.get(bot_link + message)
                day_flag = 'selected' if ((data.High[0] - data.Open[0] == 0) or  (data.Open[0] - data.Low[0])== 0) \
                    else 'not selected'

                # Action on Day Selection
                if day_flag == 'selected':
                    entry_high_target = data.High[0]
                    entry_low_target = data.Low[0]

                #Action on Day Not Selection
                else:
                    break

            # Action on 3:15
            elif data.Date[0].hour == 15 and data.Date[0].minute == 15:

                # If Order Status is 'Exit'
                if order_status == 'Exit':

                    # Break the loop
                    break
                # If Order Status is 'Sub - Entry'
                elif order_status == 'Sub - Entry':

                    order_status = 'Exit'
                    # Cancel the existing order

                    # Calculate Profit
                    if order_signal == 'BUY':

                        # For Long Trade the last trade will be a sell
                        order_price = data.Close[0]
                        profit = profit + order_price

                    else:

                        # For Short Trade the last trade will be a buy
                        order_price = data.Close[0]
                        profit = profit - order_price

                        profit = profit - order_price

                # If Order Status is 'Entry'
                else:

                    order_status = 'Exit'
                    # Place a reverse order at current price (Can be a market/limit order)
                    # Cancel SL order

                    # Calculate Profit
                    if order_signal == 'BUY':

                        # For Long Trade the last trade will be a sell
                        order_price = data.Close[0]
                        profit = profit + order_price

                    else:

                        # For Short Trade the last trade will be a buy
                        order_price = data.Close[0]
                        profit = profit - order_price

            # Action After 3:15
            elif ((data.Date[0].hour == 15 and data.Date[0].minute > 15) or (data.Date[0].hour >= 16)):

                # Break the loop
                break


            # For Other Timestamps
            else:

                # If No Open Order
                if order_status == 'Exit':

                    # First Trade
                    if trade_count == 0:

                        # Long Entry Action
                        if data.High[0] >= entry_high_target:
                            order_status = 'Sub - Entry' if data_pointer == bot_pointer else 'Entry'
                            order_signal = 'BUY'
                            # semi_target_flag = 0
                            order_price = entry_high_target
                            stop_loss = entry_low_target - (0.000 * order_price)
                            profit = profit - order_price

                            # Calculating Target
                            if scenario == 1:
                                min_pos_delta = (order_price * 0.004)
                                target = min_pos_delta + order_price + (order_price * target_buffer_multiplier)

                            else:
                                deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                pos_deltas = [delta for delta in deltas if delta >= (order_price * 0.004)]
                                min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (order_price * 0.05)
                                target = min_pos_delta + order_price + (order_price * target_buffer_multiplier)

                            # Print Pointers
                            # ads_iteration.Order_Status[i] = order_status
                            # ads_iteration.Order_Signal[i] = order_signal
                            # ads_iteration.Order_Price[i] = order_price
                            # ads_iteration.Target[i] = target
                            # ads_iteration.Stop_Loss[i] = stop_loss

                            # Action on 1st Trade
                            if bot_pointer < data_pointer:
                                print('Long Entry ---')
                                print('Order Price: ' + str(order_price))
                                print('Target: ' + str(target))
                                print('Stop Loss: ' + str(stop_loss))

                            else:

                                # Place the order
                                order_id = kite.place_order(tradingsymbol=name,
                                                            variety='co',
                                                            exchange=kite.EXCHANGE_NSE,
                                                            transaction_type=order_signal,
                                                            quantity=quantity,
                                                            price=order_price,
                                                            order_type=kite.ORDER_TYPE_LIMIT,
                                                            product=kite.PRODUCT_MIS,
                                                            trigger_price=stop_loss)

                                current_order = current_order.append({'order_id': order_id,
                                                                      'order_type': 'LIMIT',
                                                                      'transaction_type': order_signal,
                                                                      'parent_order_id': 'NA',
                                                                      'price': order_price,
                                                                      'trigger_price': stop_loss,
                                                                      'status': 'OPEN'}, ignore_index=True)
                                live_order_flag = 1
                                message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                                    order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                requests.get(bot_link + message)

                        # Short Entry Action
                        elif data.Low[0] <= entry_low_target:
                            order_status = 'Sub - Entry' if data_pointer == bot_pointer else 'Entry'
                            order_signal = 'SELL'
                            semi_target_flag = 0
                            order_price = entry_low_target
                            stop_loss = entry_high_target + (0.000 * order_price)
                            profit = profit + order_price

                            # Calculating Target
                            if scenario == 1:
                                max_neg_delta = -(order_price * 0.004)
                                target = order_price + max_neg_delta - (order_price * target_buffer_multiplier)

                            else:

                                deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                                max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(order_price * 0.05)
                                target = order_price + max_neg_delta - (order_price * target_buffer_multiplier)

                            # Print Pointers
                            # ads_iteration.Order_Status[i] = order_status
                            # ads_iteration.Order_Signal[i] = order_signal
                            # ads_iteration.Order_Price[i] = order_price
                            # ads_iteration.Target[i] = target
                            # ads_iteration.Stop_Loss[i] = stop_loss

                            # Action on 1st Trade
                            if bot_pointer < data_pointer:
                                print('Short Entry ---')
                                print('Order Price: ' + str(order_price))
                                print('Target: ' + str(target))
                                print('Stop Loss: ' + str(stop_loss))

                            else:

                                # Place the order
                                order_id = kite.place_order(tradingsymbol=name,
                                                            variety='co',
                                                            exchange=kite.EXCHANGE_NSE,
                                                            transaction_type=order_signal,
                                                            quantity=quantity,
                                                            price=order_price,
                                                            order_type=kite.ORDER_TYPE_LIMIT,
                                                            product=kite.PRODUCT_MIS,
                                                            trigger_price=stop_loss)

                                current_order = current_order.append({'order_id': order_id,
                                                                      'order_type': 'LIMIT',
                                                                      'transaction_type': order_signal,
                                                                      'parent_order_id': 'NA',
                                                                      'price': order_price,
                                                                      'trigger_price': stop_loss,
                                                                      'status': 'OPEN'}, ignore_index=True)
                                live_order_flag = 1
                                message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                                    order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                requests.get(bot_link + message)


                    # Other Trade Entries
                    else:

                        # Long Entry Action
                        if (data.High[0] >= entry_high_target) and (long_count == 0):
                            order_status = 'Sub - Entry' if data_pointer == bot_pointer else 'Entry'
                            order_signal = 'BUY'
                            # semi_target_flag = 0
                            order_price = entry_high_target
                            stop_loss = entry_low_target - (0.000 * order_price)
                            profit = profit - order_price

                            # Calculating Target
                            deltas = [round(indicator, 1) - order_price for indicator in pivots]
                            pos_deltas = [delta for delta in deltas if delta >= (order_price * 0.004)]
                            min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (order_price * 0.05)
                            target = min_pos_delta + order_price + (order_price * target_buffer_multiplier)

                            # Print Pointers
                            # ads_iteration.Order_Status[i] = order_status
                            # ads_iteration.Order_Signal[i] = order_signal
                            # ads_iteration.Order_Price[i] = order_price
                            # ads_iteration.Target[i] = target
                            # ads_iteration.Stop_Loss[i] = stop_loss

                            # Action on 1st Trade
                            if bot_pointer < data_pointer:
                                print('Long Entry ---')
                                print('Order Price: ' + str(order_price))
                                print('Target: ' + str(target))
                                print('Stop Loss: ' + str(stop_loss))

                            else:

                                # Place the order
                                order_id = kite.place_order(tradingsymbol=name,
                                                            variety='co',
                                                            exchange=kite.EXCHANGE_NSE,
                                                            transaction_type=order_signal,
                                                            quantity=quantity,
                                                            price=order_price,
                                                            order_type=kite.ORDER_TYPE_LIMIT,
                                                            product=kite.PRODUCT_MIS,
                                                            trigger_price=stop_loss)

                                current_order = current_order.append({'order_id': order_id,
                                                                      'order_type': 'LIMIT',
                                                                      'transaction_type': order_signal,
                                                                      'parent_order_id': 'NA',
                                                                      'price': order_price,
                                                                      'trigger_price': stop_loss,
                                                                      'status': 'OPEN'}, ignore_index=True)
                                live_order_flag = 1
                                message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                                    order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                requests.get(bot_link + message)

                        # Short Entry Action
                        elif (data.Low[0] <= entry_low_target) and (short_count == 0):
                            order_status = 'Sub - Entry' if data_pointer == bot_pointer else 'Entry'
                            order_signal = 'SELL'
                            semi_target_flag = 0
                            order_price = entry_low_target
                            stop_loss = entry_high_target + (0.000 * order_price)
                            profit = profit + order_price

                            # Calculating Target
                            deltas = [round(indicator, 1) - order_price for indicator in pivots]
                            neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                            max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(order_price * 0.05)
                            target = order_price + max_neg_delta - (order_price * target_buffer_multiplier)

                            # Print Pointers
                            # ads_iteration.Order_Status[i] = order_status
                            # ads_iteration.Order_Signal[i] = order_signal
                            # ads_iteration.Order_Price[i] = order_price
                            # ads_iteration.Target[i] = target
                            # ads_iteration.Stop_Loss[i] = stop_loss

                            # Action on 1st Trade
                            if bot_pointer < data_pointer:
                                print('Short Entry ---')
                                print('Order Price: ' + str(order_price))
                                print('Target: ' + str(target))
                                print('Stop Loss: ' + str(stop_loss))

                            else:

                                # Place the order
                                order_id = kite.place_order(tradingsymbol=name,
                                                            variety='co',
                                                            exchange=kite.EXCHANGE_NSE,
                                                            transaction_type=order_signal,
                                                            quantity=quantity,
                                                            price=order_price,
                                                            order_type=kite.ORDER_TYPE_LIMIT,
                                                            product=kite.PRODUCT_MIS,
                                                            trigger_price=stop_loss)

                                current_order = current_order.append({'order_id': order_id,
                                                                      'order_type': 'LIMIT',
                                                                      'transaction_type': order_signal,
                                                                      'parent_order_id': 'NA',
                                                                      'price': order_price,
                                                                      'trigger_price': stop_loss,
                                                                      'status': 'OPEN'}, ignore_index=True)
                                live_order_flag = 1
                                message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                                    order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                requests.get(bot_link + message)

                # If Complete Order Exists
                elif order_status == 'Entry':

                    # Calculating for previous data of today
                    if bot_pointer < data_pointer:

                        # If Long Entry Exists
                        if order_signal == 'BUY':

                            # Exit From Stop Loss
                            if data.Low[0] <= stop_loss:
                                order_status = 'Exit'
                                order_signal = 'SELL'
                                order_price = stop_loss
                                trade_count = trade_count + 1
                                long_count = 1
                                short_count = 0
                                profit = profit + order_price

                                print('Long Exit ---')
                                print('Order Price: ' + str(order_price))
                                print('Remarks: Loss')

                                # Take Reverse Entry
                                order_status = 'Entry'
                                order_signal = 'SELL'
                                stop_loss = entry_high_target + (0.000 * order_price)
                                profit = profit + order_price

                                # Calculating Target
                                deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                                max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(order_price * 0.05)
                                target = order_price + max_neg_delta - (order_price * target_buffer_multiplier)

                                order_status = 'Entry'
                                print('Short Entry ---')
                                print('Order Price: ' + str(order_price))
                                print('Target: ' + str(target))
                                print('Stop Loss: ' + str(stop_loss))


                            # Exit From Target
                            elif data.High[0] >= target:
                                order_status = 'Exit'
                                order_signal = 'SELL'
                                order_price = target
                                trade_count = trade_count + 1
                                long_count = 1
                                short_count = 0
                                profit = profit + order_price

                                # Print Pointers
                                # ads_iteration.Order_Status[i] = order_status
                                # ads_iteration.Order_Signal[i] = order_signal
                                # ads_iteration.Order_Price[i] = order_price

                                print('Long Exit ---')
                                print('Order Price: ' + str(order_price))
                                print('Remarks: Profit')

                        # If Short Entry Exists
                        elif order_signal == 'SELL':

                            # Exit From Stop Loss
                            if data.High[0] >= stop_loss:
                                order_status = 'Exit'
                                order_signal = 'BUY'
                                order_price = stop_loss
                                trade_count = trade_count + 1
                                long_count = 0
                                short_count = 1
                                profit = profit - order_price

                                # Print Pointers
                                # ads_iteration.Order_Status[i] = order_status
                                # ads_iteration.Order_Signal[i] = order_signal
                                # ads_iteration.Order_Price[i] = order_price

                                print('Short Exit ---')
                                print('Order Price: ' + str(order_price))
                                print('Remarks: Loss')

                                # Take Reverse Entry
                                order_status = 'Entry'
                                order_signal = 'BUY'
                                stop_loss = entry_low_target - (0.000 * order_price)
                                profit = profit - order_price

                                # Calculating Target
                                deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                pos_deltas = [delta for delta in deltas if delta >= (order_price * 0.004)]
                                min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (order_price * 0.05)
                                target = min_pos_delta + order_price + (order_price * target_buffer_multiplier)

                                # Print Pointers
                                print('Long Entry ---')
                                print('Order Price: ' + str(order_price))
                                print('Target: ' + str(target))
                                print('Stop Loss: ' + str(stop_loss))

                            # Exit From Target
                            elif data.Low[0] <= target:
                                order_status = 'Exit'
                                order_signal = 'BUY'
                                order_price = target
                                trade_count = trade_count + 1
                                long_count = 0
                                short_count = 1
                                profit = profit - order_price

                                # Print Pointers
                                # ads_iteration.Order_Status[i] = order_status
                                # ads_iteration.Order_Signal[i] = order_signal
                                # ads_iteration.Order_Price[i] = order_price

                                print('Short Exit ---')
                                print('Order Price: ' + str(order_price))
                                print('Remarks: Profit')

                    # Calculating for LIVE data today
                    else:

                        # If Live Entry Exists
                        if live_order_flag == 1:

                            # Check If Stoploss Order is Hit
                            if current_order[current_order['parent_order_id'] == order_id]['status'].values[0] == 'COMPLETE':

                                # If Long Entry Exists
                                if order_signal == 'BUY':

                                    # Set Pointers
                                    order_status = 'Exit'
                                    order_signal = 'SELL'
                                    order_price = stop_loss
                                    trade_count = trade_count + 1
                                    long_count = 1
                                    short_count = 0
                                    profit = profit + order_price

                                    print('Long Exit ---')
                                    print('Order Price: ' + str(order_price))
                                    print('Remarks: Loss')

                                    # Take Reverse Entry
                                    order_status = 'Sub - Entry'
                                    order_signal = 'SELL'
                                    stop_loss = entry_high_target + (0.000 * order_price)
                                    profit = profit + order_price

                                    # Calculating Target
                                    deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                    neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                                    max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(order_price * 0.05)
                                    target = order_price + max_neg_delta - (order_price * target_buffer_multiplier)

                                    # Place the order
                                    order_id = kite.place_order(tradingsymbol=name,
                                                                variety='co',
                                                                exchange=kite.EXCHANGE_NSE,
                                                                transaction_type=order_signal,
                                                                quantity=quantity,
                                                                price=order_price,
                                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                                product=kite.PRODUCT_MIS,
                                                                trigger_price=stop_loss)

                                    current_order = current_order.append({'order_id': order_id,
                                                                          'order_type': 'LIMIT',
                                                                          'transaction_type': order_signal,
                                                                          'parent_order_id': 'NA',
                                                                          'price': order_price,
                                                                          'trigger_price': stop_loss,
                                                                          'status': 'OPEN'}, ignore_index=True)
                                    live_order_flag = 1
                                    message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                                        order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                    requests.get(bot_link + message)

                                # If Short entry Exists
                                else:

                                    # set Pointers
                                    order_status = 'Exit'
                                    order_signal = 'BUY'
                                    order_price = stop_loss
                                    trade_count = trade_count + 1
                                    long_count = 0
                                    short_count = 1
                                    profit = profit - order_price

                                    # Print Pointers
                                    # ads_iteration.Order_Status[i] = order_status
                                    # ads_iteration.Order_Signal[i] = order_signal
                                    # ads_iteration.Order_Price[i] = order_price

                                    print('Short Exit ---')
                                    print('Order Price: ' + str(order_price))
                                    print('Remarks: Loss')

                                    # Take Reverse Entry
                                    order_status = 'Sub - Entry'
                                    order_signal = 'BUY'
                                    stop_loss = entry_low_target - (0.000 * order_price)
                                    profit = profit - order_price

                                    # Calculating Target
                                    deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                    pos_deltas = [delta for delta in deltas if delta >= (order_price * 0.004)]
                                    min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (order_price * 0.05)
                                    target = min_pos_delta + order_price + (order_price * target_buffer_multiplier)

                                    # Place the order
                                    order_id = kite.place_order(tradingsymbol=name,
                                                                variety='co',
                                                                exchange=kite.EXCHANGE_NSE,
                                                                transaction_type=order_signal,
                                                                quantity=quantity,
                                                                price=order_price,
                                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                                product=kite.PRODUCT_MIS,
                                                                trigger_price=stop_loss)

                                    current_order = current_order.append({'order_id': order_id,
                                                                          'order_type': 'LIMIT',
                                                                          'transaction_type': order_signal,
                                                                          'parent_order_id': 'NA',
                                                                          'price': order_price,
                                                                          'trigger_price': stop_loss,
                                                                          'status': 'OPEN'}, ignore_index=True)
                                    live_order_flag = 1
                                    message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                                        order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                    requests.get(bot_link + message)

                            # check If Target is Hit
                            else:

                                # If Long Entry Exists
                                if (order_signal == 'BUY') and (data.High[0] >= target):

                                    # Set Pointers
                                    order_status = 'Exit'
                                    order_signal = 'SELL'
                                    order_price = target
                                    trade_count = trade_count + 1
                                    long_count = 1
                                    short_count = 0
                                    profit = profit + order_price

                                    # Print Pointers
                                    # ads_iteration.Order_Status[i] = order_status
                                    # ads_iteration.Order_Signal[i] = order_signal
                                    # ads_iteration.Order_Price[i] = order_price

                                    # Modify the stoploss of existing order
                                    kite.exit_order(variety='co',
                                                    order_id=order_id)

                                    print('Long Exit ---')
                                    print('Order Price: ' + str(order_price))
                                    print('Remarks: Profit')

                                # If short Entry Exists
                                elif (order_signal == 'SELL') and (data.Low[0] <= target):

                                    # Set Pointers
                                    order_status = 'Exit'
                                    order_signal = 'BUY'
                                    order_price = target
                                    trade_count = trade_count + 1
                                    long_count = 0
                                    short_count = 1
                                    profit = profit - order_price

                                    # Print Pointers
                                    # ads_iteration.Order_Status[i] = order_status
                                    # ads_iteration.Order_Signal[i] = order_signal
                                    # ads_iteration.Order_Price[i] = order_price

                                    # Modify the stoploss of existing order
                                    kite.exit_order(variety='co',
                                                    order_id=order_id)

                                    print('Short Exit ---')
                                    print('Order Price: ' + str(order_price))
                                    print('Remarks: Profit')

                                # On No Target & SL Hit
                                else:

                                    print(name + " - remains in Entry State")

                        # If Live Entry does not exist
                        else:

                            # If Long Entry Exists
                            if order_signal == 'BUY':

                                # Exit From Stop Loss
                                if data.Low[0] <= stop_loss:
                                    order_status = 'Exit'
                                    order_signal = 'SELL'
                                    order_price = stop_loss
                                    trade_count = trade_count + 1
                                    long_count = 1
                                    short_count = 0
                                    profit = profit + order_price

                                    print('Long Exit ---')
                                    print('Order Price: ' + str(order_price))
                                    print('Remarks: Loss')

                                    # Take Reverse Entry
                                    order_status = 'Sub - Entry'
                                    order_signal = 'SELL'
                                    stop_loss = entry_high_target + (0.000 * order_price)
                                    profit = profit + order_price

                                    # Calculating Target
                                    deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                    neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                                    max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(order_price * 0.05)
                                    target = order_price + max_neg_delta - (order_price * target_buffer_multiplier)

                                    # Place the order
                                    order_id = kite.place_order(tradingsymbol=name,
                                                                variety='co',
                                                                exchange=kite.EXCHANGE_NSE,
                                                                transaction_type=order_signal,
                                                                quantity=quantity,
                                                                price=order_price,
                                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                                product=kite.PRODUCT_MIS,
                                                                trigger_price=stop_loss)

                                    current_order = current_order.append({'order_id': order_id,
                                                                          'order_type': 'LIMIT',
                                                                          'transaction_type': order_signal,
                                                                          'parent_order_id': 'NA',
                                                                          'price': order_price,
                                                                          'trigger_price': stop_loss,
                                                                          'status': 'OPEN'}, ignore_index=True)
                                    live_order_flag = 1
                                    message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                                        order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                    requests.get(bot_link + message)

                                # Exit From Target
                                elif data.High[0] >= target:
                                    order_status = 'Exit'
                                    order_signal = 'SELL'
                                    order_price = target
                                    trade_count = trade_count + 1
                                    long_count = 1
                                    short_count = 0
                                    profit = profit + order_price

                                    # Print Pointers
                                    # ads_iteration.Order_Status[i] = order_status
                                    # ads_iteration.Order_Signal[i] = order_signal
                                    # ads_iteration.Order_Price[i] = order_price

                                    print('Long Exit ---')
                                    print('Order Price: ' + str(order_price))
                                    print('Remarks: Profit')

                            # If Short Entry Exists
                            elif order_signal == 'SELL':

                                # Exit From Stop Loss
                                if data.High[0] >= stop_loss:
                                    order_status = 'Exit'
                                    order_signal = 'BUY'
                                    order_price = stop_loss
                                    trade_count = trade_count + 1
                                    long_count = 0
                                    short_count = 1
                                    profit = profit - order_price

                                    # Print Pointers
                                    # ads_iteration.Order_Status[i] = order_status
                                    # ads_iteration.Order_Signal[i] = order_signal
                                    # ads_iteration.Order_Price[i] = order_price

                                    print('Short Exit ---')
                                    print('Order Price: ' + str(order_price))
                                    print('Remarks: Loss')

                                    # Take Reverse Entry
                                    order_status = 'Sub - Entry'
                                    order_signal = 'BUY'
                                    stop_loss = entry_low_target - (0.000 * order_price)
                                    profit = profit - order_price

                                    # Calculating Target
                                    deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                    pos_deltas = [delta for delta in deltas if delta >= (order_price * 0.004)]
                                    min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (order_price * 0.05)
                                    target = min_pos_delta + order_price + (order_price * target_buffer_multiplier)

                                    # Place the order
                                    order_id = kite.place_order(tradingsymbol=name,
                                                                variety='co',
                                                                exchange=kite.EXCHANGE_NSE,
                                                                transaction_type=order_signal,
                                                                quantity=quantity,
                                                                price=order_price,
                                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                                product=kite.PRODUCT_MIS,
                                                                trigger_price=stop_loss)

                                    current_order = current_order.append({'order_id': order_id,
                                                                          'order_type': 'LIMIT',
                                                                          'transaction_type': order_signal,
                                                                          'parent_order_id': 'NA',
                                                                          'price': order_price,
                                                                          'trigger_price': stop_loss,
                                                                          'status': 'OPEN'}, ignore_index=True)
                                    live_order_flag = 1
                                    message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                                        order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                    requests.get(bot_link + message)

                                # Exit From Target
                                elif data.Low[0] <= target:
                                    order_status = 'Exit'
                                    order_signal = 'BUY'
                                    order_price = target
                                    trade_count = trade_count + 1
                                    long_count = 0
                                    short_count = 1
                                    profit = profit - order_price

                                    # Print Pointers
                                    # ads_iteration.Order_Status[i] = order_status
                                    # ads_iteration.Order_Signal[i] = order_signal
                                    # ads_iteration.Order_Price[i] = order_price

                                    print('Short Exit ---')
                                    print('Order Price: ' + str(order_price))
                                    print('Remarks: Profit')

                # If Open Order Exists
                elif order_status == 'Sub - Entry':

                    # Check if Order is completed
                    if current_order[current_order['order_id'] == order_id]['status'].values[0] == 'COMPLETE':

                        # Set Order Status as 'Entry'
                        order_status = 'Entry'

                    # Check Other conditions if order is still open
                    else:

                        # If Long Entry Exists
                        if order_signal == 'BUY':

                            # Exit From Stop Loss
                            if data.Low[0] <= stop_loss:

                                # Cancel Existing Order
                                kite.cancel_order(variety='co',
                                                  order_id=order_id)

                                # Set Pointer
                                order_status = 'Exit'
                                order_signal = 'SELL'
                                order_price = stop_loss
                                trade_count = trade_count + 1
                                long_count = 1
                                short_count = 0
                                profit = profit + order_price

                                print('Long Exit ---')
                                print('Order Price: ' + str(order_price))
                                print('Remarks: Loss')

                                # Take Reverse Entry
                                order_status = 'Sub - Entry'
                                order_signal = 'SELL'
                                stop_loss = entry_high_target + (0.000 * order_price)
                                profit = profit + order_price

                                # Calculating Target
                                deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.004)]
                                max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(order_price * 0.05)
                                target = order_price + max_neg_delta - (order_price * target_buffer_multiplier)

                                # Place the order
                                order_id = kite.place_order(tradingsymbol=name,
                                                            variety='co',
                                                            exchange=kite.EXCHANGE_NSE,
                                                            transaction_type=order_signal,
                                                            quantity=quantity,
                                                            price=order_price,
                                                            order_type=kite.ORDER_TYPE_LIMIT,
                                                            product=kite.PRODUCT_MIS,
                                                            trigger_price=stop_loss)

                                current_order = current_order.append({'order_id': order_id,
                                                                      'order_type': 'LIMIT',
                                                                      'transaction_type': order_signal,
                                                                      'parent_order_id': 'NA',
                                                                      'price': order_price,
                                                                      'trigger_price': stop_loss,
                                                                      'status': 'OPEN'}, ignore_index=True)
                                live_order_flag = 1
                                message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(
                                    order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                requests.get(bot_link + message)

                            # Exit From Target
                            elif data.High[0] >= target:

                                # Cancel Existing Order
                                kite.cancel_order(variety='co',
                                                  order_id=order_id)

                                # Set Pointers
                                order_status = 'Exit'
                                order_signal = 'SELL'
                                order_price = target
                                trade_count = trade_count + 1
                                long_count = 1
                                short_count = 0
                                profit = profit + order_price

                                # Print Pointers
                                # ads_iteration.Order_Status[i] = order_status
                                # ads_iteration.Order_Signal[i] = order_signal
                                # ads_iteration.Order_Price[i] = order_price

                                print('Long Exit ---')
                                print('Order Price: ' + str(order_price))
                                print('Remarks: Profit')

                        # If Short Entry Exists
                        elif order_signal == 'SELL':

                            # Exit From Stop Loss
                            if data.High[0] >= stop_loss:

                                # Cancel Existing Order
                                kite.cancel_order(variety='co',
                                                  order_id=order_id)

                                # Set Pointers
                                order_status = 'Exit'
                                order_signal = 'BUY'
                                order_price = stop_loss
                                trade_count = trade_count + 1
                                long_count = 0
                                short_count = 1
                                profit = profit - order_price

                                # Print Pointers
                                # ads_iteration.Order_Status[i] = order_status
                                # ads_iteration.Order_Signal[i] = order_signal
                                # ads_iteration.Order_Price[i] = order_price

                                print('Short Exit ---')
                                print('Order Price: ' + str(order_price))
                                print('Remarks: Loss')

                                # Take Reverse Entry
                                order_status = 'Sub - Entry'
                                order_signal = 'BUY'
                                stop_loss = entry_low_target - (0.000 * order_price)
                                profit = profit - order_price

                                # Calculating Target
                                deltas = [round(indicator, 1) - order_price for indicator in pivots]
                                pos_deltas = [delta for delta in deltas if delta >= (order_price * 0.004)]
                                min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (order_price * 0.05)
                                target = min_pos_delta + order_price + (order_price * target_buffer_multiplier)

                                # Place the order
                                order_id = kite.place_order(tradingsymbol=name,
                                                            variety='co',
                                                            exchange=kite.EXCHANGE_NSE,
                                                            transaction_type=order_signal,
                                                            quantity=quantity,
                                                            price=order_price,
                                                            order_type=kite.ORDER_TYPE_LIMIT,
                                                            product=kite.PRODUCT_MIS,
                                                            trigger_price=stop_loss)

                                current_order = current_order.append({'order_id': order_id,
                                                                      'order_type': 'LIMIT',
                                                                      'transaction_type': order_signal,
                                                                      'parent_order_id': 'NA',
                                                                      'price': order_price,
                                                                      'trigger_price': stop_loss,
                                                                      'status': 'OPEN'}, ignore_index=True)
                                live_order_flag = 1
                                message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(
                                    order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                                requests.get(bot_link + message)

                            # Exit From Target
                            elif data.Low[0] <= target:

                                # Cancel Existing Order
                                kite.cancel_order(variety='co',
                                                  order_id=order_id)

                                # Set Pointers
                                order_status = 'Exit'
                                order_signal = 'BUY'
                                order_price = target
                                trade_count = trade_count + 1
                                long_count = 0
                                short_count = 1
                                profit = profit - order_price

                                # Print Pointers
                                # ads_iteration.Order_Status[i] = order_status
                                # ads_iteration.Order_Signal[i] = order_signal
                                # ads_iteration.Order_Price[i] = order_price
                                print('Order Price: ' + str(order_price))
                                print('Remarks: Profit')

                # Set Day High-Low Pointers
                entry_high_target = max(entry_high_target, data.High[0])
                entry_low_target = min(entry_low_target, data.Low[0])



## The Main Function
if __name__ == '__main__':

    # Get the input parameters and start the parallel processing
    path = '/home/ubuntu/APT/APT/Live_Trading'
    # path = 'F:\DevAPT\APT\Live_Trading'
    config_path = path + '/config.ini'
    os.chdir(path)
    # name = sys.argv[1]
    # token = [int(sys.argv[2])]
    # access_token = sys.argv[3]
    # lot_size = [int(sys.argv[4])]
    name = 'PVR'
    token = [3365633]
    access_token = 'S2qf7h6epEEJEDY9arTVwi3Yc8v0vT0J'
    lot_size = 400
    scenario = 2
    stock_name_string = 'Stock Name: ' + name
    requests.get(
        "https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + \
        stock_name_string)
    print(stock_name_string, flush=True)
    start(name, token, access_token, lot_size, scenario=scenario)
