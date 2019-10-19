## Import Libraries
###############################################################
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from os import path
import requests


## Define Strategy Function
def GapUpStrategy_Pivot(data, name, lot_size, pivots, order_status, order_signal, order_price, target, stop_loss,
                        entry_high_target, entry_low_target, long_count, short_count, trade_count,
                        semi_target_flag, profit, skip_date, prev_day_close, min_gap=0.000001,
                        semi_target_multiplier=0.005, target_buffer_multiplier=0.0, min_target=5000,
                        candle_error = 0.00075):
    live_order_file_name = 'live_order_' + name + '_' + str(datetime.now().date()) + '.csv'
    print('Live Oder From Strategy: '  + live_order_file_name)

    if path.exists(live_order_file_name):
        print('Live Trading data Exists for ' + name)
        live_order_data = pd.read_csv(live_order_file_name)

    # Selecting Tradable Day and Reset Day High and Day Low
    if data.Date[0].hour == 9 and data.Date[0].minute == 15:
        day_flag = 'selected' if abs(data.Open[0] - prev_day_close) > (prev_day_close * min_gap) else 'not selected'
        skip_date = data.DatePart[0] if day_flag == 'not selected' else skip_date
        entry_high_target = data.High[0]
        entry_low_target = data.Low[0]

        # Check if Marubuzu Candle
        if day_flag == 'selected':
            trade_count = 1 if ((data.Open[0] - data.Low[0]) <= data.Open[0] * candle_error or 
                    (data.High[0] - data.Close[0]) <= data.Open[0] * candle_error or
                    (data.High[0] - data.Open[0]) <= data.Open[0] * candle_error or
                    (data.Close[0] - data.Low[0]) <= data.Open[0] * candle_error) else trade_count
            if trade_count == 1:
                 message = 'Stock Name: ' + name + '\nMarubuzu Candle Identified'
                 requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

        # print('Date: ' + str(data.Date[0]))
        # print('Status: ' + day_flag)

    # Exit from Ongoing Order, if any at 3:25 PM
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
                data.Order_Status[0] = order_status
                data.Order_Signal[0] = order_signal
                data.Order_Price[0] = order_price
                live_order_data = pd.read_csv(live_order_file_name)
                live_order_data['stoploss_status'][len(live_order_data) - 1] = 1
                message = 'Stock Name: ' + name + '\n Long Exit ---' + '\nOrder Price: ' + str(order_price) + '\nRemarks: Exit At 3:25 PM'
                requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

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
                data.Order_Status[0] = order_status
                data.Order_Signal[0] = order_signal
                data.Order_Price[0] = order_price
                live_order_data = pd.read_csv(live_order_file_name)
                live_order_data['stoploss_status'][len(live_order_data) - 1] = 1
                message = 'Stock Name: ' + name + '\n Short Exit ---' + '\nOrder Price: ' + str(order_price) + '\nRemarks: Exit At 3:25 PM'
                requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)
                print('Stock Name: ' + name + '\n Short Exit ---')
                print('Order Price: ' + str(order_price))
                print('Remarks: Exit At 3:25 PM')

    # Reset Pointers at 3:30 PM
    elif data.Date[0].hour == 15 and data.Date[0].minute == 25:
        prev_day_close = data.Close[0]
        long_count = 0
        short_count = 0
        trade_count = 0
        skip_date = data.DatePart[0]
        message = 'Stock Name: ' + name + '\nRemarks: Enough For Today'
        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

    # Iterate over all the data points for the dates that have been selected by Gap Up/Down Condition
    elif data.DatePart[0] != skip_date:

        # If No Open Order
        if order_status == 'Exit':

            # First Trade
            if trade_count == 0:

                # Long Entry Action
                if data.Close[0] > entry_high_target:
                    order_status = 'Entry'
                    order_signal = 'BUY'
                    trade_count = trade_count + 1
                    semi_target_flag = 0
                    order_price = round(data.Close[0], 1)
                    stop_loss = entry_low_target - round((target_buffer_multiplier * order_price), 1)
                    profit = profit - order_price

                    # Calculating Target
                    deltas = [indicator - order_price for indicator in pivots]
                    pos_deltas = [delta for delta in deltas if delta > (order_price * 0.005)]
                    min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                    target = round(min_pos_delta + order_price + (order_price * target_buffer_multiplier), 1)

                    # Print Pointers
                    data.Order_Status[0] = order_status
                    data.Order_Signal[0] = order_signal
                    data.Order_Price[0] = order_price
                    data.Target[0] = target
                    data.Stop_Loss[0] = stop_loss
                    live_order_data = pd.DataFrame(index=[0],
                                                   columns=['order_id', 'transaction_type', 'price', 'stoploss',
                                                            'target',
                                                            'status', 'semi-target_status', 'target_status',
                                                            'stoploss_status',
                                                            'day_high', 'day_low'])
                    live_order_data_subset = pd.DataFrame({'order_id': [trade_count],
                                                           'transaction_type':[order_signal],
                                                           'price': [order_price],
                                                           'stoploss': [stop_loss],
                                                           'target': [target],
                                                           'status': [np.nan],
                                                           'semi-target_status': [0],
                                                           'target_status': [0],
                                                           'stoploss_status': [0],
                                                           'day_high': [entry_high_target],
                                                           'day_low': [entry_low_target]})
                    live_order_data = live_order_data.append(live_order_data_subset)
                    live_order_data.reset_index(drop= True)
                    live_order_data = live_order_data[1:]
                    live_order_data.to_csv(live_order_file_name)
                    message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)


                # Short Entry Action
                elif data.Close[0] < entry_low_target:
                    order_status = 'Entry'
                    order_signal = 'SELL'
                    semi_target_flag = 0
                    trade_count = trade_count + 1
                    order_price = round(data.Close[0], 1)
                    stop_loss = entry_high_target + round((target_buffer_multiplier * order_price), 1)
                    profit = profit + order_price

                    # Calculating Target
                    deltas = [round(indicator,1) - order_price for indicator in pivots]
                    neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.005)]
                    max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                    target = round(order_price + max_neg_delta - (order_price * target_buffer_multiplier), 1)

                    # Print Pointers
                    data.Order_Status[0] = order_status
                    data.Order_Signal[0] = order_signal
                    data.Order_Price[0] = order_price
                    data.Target[0] = target
                    data.Stop_Loss[0] = stop_loss
                    live_order_data = pd.DataFrame(index=[0],
                                                   columns=['order_id', 'transaction_type', 'price', 'stoploss',
                                                            'target',
                                                            'status', 'semi-target_status', 'target_status',
                                                            'stoploss_status',
                                                            'day_high', 'day_low'])
                    live_order_data_subset = pd.DataFrame({'order_id': [trade_count],
                                                           'transaction_type': [order_signal],
                                                           'price': [order_price],
                                                           'stoploss': [stop_loss],
                                                           'target': [target],
                                                           'status': [np.nan],
                                                           'semi-target_status': [0],
                                                           'target_status': [0],
                                                           'stoploss_status': [0],
                                                           'day_high': [entry_high_target],
                                                           'day_low': [entry_low_target]})
                    live_order_data = live_order_data.append(live_order_data_subset)
                    live_order_data.reset_index(drop= True)
                    live_order_data = live_order_data[1:]
                    live_order_data.to_csv(live_order_file_name)
                    message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

            # Other Trade Entries
            else:
                # Long Entry
                if (data.High[0] > entry_high_target) and (long_count == 0):
                    order_status = 'Entry'
                    order_signal = 'BUY'
                    semi_target_flag = 0
                    trade_count = trade_count + 1
                    order_price = entry_high_target
                    stop_loss = entry_low_target - round((target_buffer_multiplier * order_price), 1)
                    profit = profit - order_price

                    # Calculating Target
                    deltas = [indicator - order_price for indicator in pivots]
                    pos_deltas = [delta for delta in deltas if delta > (order_price * 0.005)]
                    min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                    target = round(min_pos_delta + order_price + (order_price * target_buffer_multiplier),1)

                    # Print Pointers
                    data.Order_Status[0] = order_status
                    data.Order_Signal[0] = order_signal
                    data.Order_Price[0] = order_price
                    data.Target[0] = target
                    data.Stop_Loss[0] = stop_loss
                    if path.exists(live_order_file_name):
                        live_order_data = pd.read_csv(live_order_file_name)
                        live_order_data_subset = pd.DataFrame({'order_id': [trade_count],
                                                           'transaction_type': [order_signal],
                                                           'price': [order_price],
                                                           'stoploss': [stop_loss],
                                                           'target': [target],
                                                           'status': [np.nan],
                                                           'semi-target_status': [0],
                                                           'target_status': [0],
                                                           'stoploss_status': [0],
                                                           'day_high': [entry_high_target],
                                                           'day_low': [entry_low_target]})
                        live_order_data = live_order_data.append(live_order_data_subset)
                        live_order_data.reset_index(drop = True)
                    else:
                        live_order_data = pd.DataFrame(index=[0],
                                                       columns=['order_id', 'transaction_type', 'price', 'stoploss',
                                                                'target',
                                                                'status', 'semi-target_status', 'target_status',
                                                                'stoploss_status',
                                                                'day_high', 'day_low'])
                        live_order_data_subset = pd.DataFrame({'order_id': [trade_count],
                                                               'transaction_type': [order_signal],
                                                               'price': [order_price],
                                                               'stoploss': [stop_loss],
                                                               'target': [target],
                                                               'status': [np.nan],
                                                               'semi-target_status': [0],
                                                               'target_status': [0],
                                                               'stoploss_status': [0],
                                                               'day_high': [entry_high_target],
                                                               'day_low': [entry_low_target]})
                        live_order_data = live_order_data.append(live_order_data_subset)
                        live_order_data.reset_index(drop=True)
                        live_order_data = live_order_data[1:]
                        live_order_data.to_csv(live_order_file_name)
                    message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                # Short Entry
                elif (data.Low[0] < entry_low_target) and (short_count == 0):
                    order_status = 'Entry'
                    order_signal = 'SELL'
                    semi_target_flag = 0
                    trade_count = trade_count + 1
                    order_price = entry_low_target
                    stop_loss = entry_high_target + round((target_buffer_multiplier * order_price),1)
                    profit = profit + order_price

                    # Calculating Target
                    deltas = [indicator - order_price for indicator in pivots]
                    neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.005)]
                    max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                    target = round(order_price + max_neg_delta - (order_price * target_buffer_multiplier), 1)

                    # Print Pointers
                    data.Order_Status[0] = order_status
                    data.Order_Signal[0] = order_signal
                    data.Order_Price[0] = order_price
                    data.Target[0] = target
                    data.Stop_Loss[0] = stop_loss
                    if path.exists(live_order_file_name):
                        live_order_data = pd.read_csv(live_order_file_name)
                        live_order_data_subset = pd.DataFrame({'order_id': [trade_count],
                                                               'transaction_type': [order_signal],
                                                               'price': [order_price],
                                                               'stoploss': [stop_loss],
                                                               'target': [target],
                                                               'status': [np.nan],
                                                               'semi-target_status': [0],
                                                               'target_status': [0],
                                                               'stoploss_status': [0],
                                                               'day_high': [entry_high_target],
                                                               'day_low': [entry_low_target]})
                        live_order_data = live_order_data.append(live_order_data_subset)
                        live_order_data.reset_index(drop= True)
                    else:
                        live_order_data = pd.DataFrame(index=[0],
                                                       columns=['order_id', 'transaction_type', 'price', 'stoploss',
                                                                'target',
                                                                'status', 'semi-target_status', 'target_status',
                                                                'stoploss_status',
                                                                'day_high', 'day_low'])
                        live_order_data_subset = pd.DataFrame({'order_id': [trade_count],
                                                               'transaction_type': [order_signal],
                                                               'price': [order_price],
                                                               'stoploss': [stop_loss],
                                                               'target': [target],
                                                               'status': [np.nan],
                                                               'semi-target_status': [0],
                                                               'target_status': [0],
                                                               'stoploss_status': [0],
                                                               'day_high': [entry_high_target],
                                                               'day_low': [entry_low_target]})
                        live_order_data = live_order_data.append(live_order_data_subset)
                        live_order_data.reset_index(drop= True)
                        live_order_data = live_order_data[1:]
                        live_order_data.to_csv(live_order_file_name)
                    message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

        # If Open Order Exists
        else:
            # If Long Entry Exists
            if order_signal == 'BUY':

                # Exit From Stop Loss
                if data.Low[0] <= stop_loss:
                    order_status = 'Exit'
                    order_signal = 'SELL'
                    order_price = stop_loss
                    # trade_count = trade_count + 1
                    long_count = 1
                    short_count = 0
                    profit = profit + order_price

                    # Print Pointers
                    data.Order_Status[0] = order_status
                    data.Order_Signal[0] = order_signal
                    data.Order_Price[0] = order_price
                    live_order_data = pd.read_csv(live_order_file_name)
                    live_order_data['stoploss_status'][len(live_order_data) - 1] = 1
                    message = 'Stock Name: ' + name + '\n Long Exit ---' + '\nOrder Price: ' + str(order_price) + '\nRemarks: Exit From Stop Loss'
                    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                    ## Take Short Entry if semi target is not hit
                    if semi_target_flag == 0:
                        order_status = 'Entry'
                        order_signal = 'SELL'
                        semi_target_flag = 0
                        trade_count = trade_count + 1
                        stop_loss = entry_high_target + round((target_buffer_multiplier * order_price),1)
                        profit = profit + order_price

                        # Calculating Target
                        deltas = [indicator - order_price for indicator in pivots]
                        neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.005)]
                        max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                        target = round(order_price + max_neg_delta - (order_price * target_buffer_multiplier),1)

                        # Print Pointers
                        data.Target[0] = target
                        data.Stop_Loss[0] = stop_loss
                        live_order_data = pd.read_csv(live_order_file_name)
                        live_order_data_subset = pd.DataFrame({'order_id': [trade_count],
                                                               'transaction_type': [order_signal],
                                                               'price': [order_price],
                                                               'stoploss': [stop_loss],
                                                               'target': [target],
                                                               'status': [np.nan],
                                                               'semi-target_status': [0],
                                                               'target_status': [0],
                                                               'stoploss_status': [0],
                                                               'day_high': [entry_high_target],
                                                               'day_low': [entry_low_target]})
                        live_order_data = live_order_data.append(live_order_data_subset)
                        live_order_data.reset_index(drop= True)
                        message = 'Stock Name: ' + name + '\n Short Entry ---' + '\nOrder Price: ' + str(order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                # Exit From Target
                elif data.High[0] >= target:
                    order_status = 'Exit'
                    order_signal = 'SELL'
                    order_price = target
                    # trade_count = trade_count + 1
                    long_count = 1
                    short_count = 0
                    profit = profit + order_price

                    # Print Pointers
                    data.Order_Status[0] = order_status
                    data.Order_Signal[0] = order_signal
                    data.Order_Price[0] = order_price
                    live_order_data = pd.read_csv(live_order_file_name)
                    live_order_data['target_status'][len(live_order_data) - 1] = 1
                    message = 'Stock Name: ' + name + '\n Long Exit ---' + '\nOrder Price: ' + str(order_price) + '\nRemarks: Exit From Target'
                    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                # Action on Semi Target
                elif data.Close[0] >= (order_price + (order_price * semi_target_multiplier)):
                    stop_loss = round(order_price + (order_price * semi_target_multiplier), 1)
                    # semi_target_flag = 1
                    live_order_data = pd.read_csv(live_order_file_name)
                    live_order_data['semi-target_status'][len(live_order_data) - 1] = 1
                    message = 'Stock Name: ' + name + '\nRemarks: Semi Target Crossed and Stop Loss Modified --- \nStop Loss: ' + str(stop_loss)
                    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

            # If Short Entry Exists
            elif order_signal == 'SELL':

                # Exit From Stop Loss
                if data.High[0] >= stop_loss:
                    order_status = 'Exit'
                    order_signal = 'BUY'
                    order_price = stop_loss
                    # trade_count = trade_count + 1
                    long_count = 0
                    short_count = 1
                    profit = profit - order_price

                    # Print Pointers
                    data.Order_Status[0] = order_status
                    data.Order_Signal[0] = order_signal
                    data.Order_Price[0] = order_price
                    live_order_data = pd.read_csv(live_order_file_name)
                    live_order_data['stoploss_status'][len(live_order_data) - 1] = 1
                    message = 'Stock Name: ' + name + '\n Short Exit ---' + '\nOrder Price: ' + str(order_price) + '\nRemarks: Exit From Stop Loss'
                    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                    ## Take Long Entry if semi target is not hit
                    if semi_target_flag == 0:
                        order_status = 'Entry'
                        order_signal = 'BUY'
                        stop_loss = round(entry_low_target - (target_buffer_multiplier * order_price),1)
                        profit = profit - order_price

                        # Calculating Target
                        deltas = [indicator - order_price for indicator in pivots]
                        pos_deltas = [delta for delta in deltas if delta > (order_price * 0.005)]
                        min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                        target = round(min_pos_delta + order_price + (order_price * target_buffer_multiplier), 1)

                        # Print Pointers
                        data.Target[0] = target
                        data.Stop_Loss[0] = stop_loss
                        live_order_data = pd.read_csv(live_order_file_name)
                        live_order_data_subset = pd.DataFrame({'order_id': [np.nan],
                                                               'transaction_type': [order_signal],
                                                               'price': [order_price],
                                                               'stoploss': [stop_loss],
                                                               'target': [target],
                                                               'status': [np.nan],
                                                               'semi-target_status': [0],
                                                               'target_status': [0],
                                                               'stoploss_status': [0],
                                                               'day_high': [entry_high_target],
                                                               'day_low': [entry_low_target]})
                        live_order_data = live_order_data.append(live_order_data_subset)
                        live_order_data.reset_index(drop= True)
                        message = 'Stock Name: ' + name + '\n Long Entry ---' + '\nOrder Price: ' + str(order_price) + '\nTarget: ' + str(target) + '\nStop Loss: ' + str(stop_loss)
                        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                # Exit From Target
                elif data.Low[0] <= target:
                    order_status = 'Exit'
                    order_signal = 'BUY'
                    order_price = target
                    # trade_count = trade_count + 1
                    long_count = 0
                    short_count = 1
                    profit = profit - order_price

                    # Print Pointers
                    data.Order_Status[0] = order_status
                    data.Order_Signal[0] = order_signal
                    data.Order_Price[0] = order_price
                    live_order_data = pd.read_csv(live_order_file_name)
                    live_order_data['target_status'][len(live_order_data) - 1] = 1
                    message = 'Stock Name: ' + name + '\n Short Exit ---' + '\nOrder Price: ' + str(order_price) + '\nRemarks: Exit From Target'
                    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                # Action on Semi Target
                elif data.Close[0] <= (order_price - (order_price * semi_target_multiplier)):
                    stop_loss = round(order_price - (order_price * semi_target_multiplier), 1)
                    # semi_target_flag = 1
                    live_order_data = pd.read_csv(live_order_file_name)
                    live_order_data['semi-target_status'][len(live_order_data) - 1] = 1
                    message = 'Stock Name: ' + name + '\n Semi Target Crossed and Stop Loss Modified  --- \nStop Loss: ' + str(stop_loss)
                    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

    entry_high_target = round(max(entry_high_target, data.High[0]), 1)
    entry_low_target = round(min(entry_low_target, data.Low[0]), 1)
    if path.exists(live_order_file_name):
        live_order_data['day_high'][len(live_order_data) - 1] = entry_high_target
        live_order_data['day_low'][len(live_order_data) - 1] = entry_low_target
        live_order_data.to_csv(live_order_file_name)

    # Combining all the required pointers in a list
    result = [order_status, order_signal, order_price, target, stop_loss,
              entry_high_target, entry_low_target, long_count, short_count, trade_count,
              semi_target_flag, profit, skip_date]

    return data, result
