## Import Libraries
###############################################################
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import copy
import kiteconnect as kc
import os



## Pivot Point Calculation
###############################################################
def pivotpoints(data, type='simple'):
    type_str = '_Simple' if type == 'simple' else '_Fibonacci'
    if 'PivotPoint' in data.columns:
        data = data.drop(['Day_High',
                          'Day_Low',
                          'Day_Open',
                          'Day_Close',
                          'PivotPoint'], axis=1)

    data['DatePart'] = [i.date() for i in data['Date']]

    aggregation = {
        'High': {
            'Day_High': 'max'
        },
        'Low': {
            'Day_Low': 'min'
        },
        'Open': {
            'Day_Open': 'first'
        },
        'Close': {
            'Day_Close': 'last'
        }
    }
    data_datelevel = data.groupby('DatePart').agg(aggregation)
    data_datelevel.columns = data_datelevel.columns.droplevel()
    data_datelevel['DatePart'] = data_datelevel.index
    data_datelevel['PivotPoint'] = (data_datelevel['Day_High'] + data_datelevel['Day_Low'] +
                                    data_datelevel['Day_Close']) / 3
    data_datelevel['S1_Pivot' + type_str] = (data_datelevel['PivotPoint'] * 2) - data_datelevel['Day_High'] if \
        type == 'simple' else data_datelevel['PivotPoint'] - \
                              (0.382 * (data_datelevel['Day_High'] -
                                        data_datelevel['Day_Low']))
    data_datelevel['S2_Pivot' + type_str] = data_datelevel['PivotPoint'] - (data_datelevel['Day_High'] -
                                                                            data_datelevel['Day_Low']) if \
        type == 'simple' else data_datelevel['PivotPoint'] - \
                              (0.618 * (data_datelevel['Day_High'] -
                                        data_datelevel['Day_Low']))
    data_datelevel['R1_Pivot' + type_str] = (data_datelevel['PivotPoint'] * 2) - data_datelevel['Day_Low'] if \
        type == 'simple' else data_datelevel['PivotPoint'] + \
                              (0.382 * (data_datelevel['Day_High'] -
                                        data_datelevel['Day_Low']))
    data_datelevel['R2_Pivot' + type_str] = data_datelevel['PivotPoint'] + (data_datelevel['Day_High'] -
                                                                            data_datelevel['Day_Low']) if \
        type == 'simple' else data_datelevel['PivotPoint'] + \
                              (0.618 * (data_datelevel['Day_High'] -
                                        data_datelevel['Day_Low']))
    if type != 'simple':
        data_datelevel['S3_Pivot' + type_str] = data_datelevel['PivotPoint'] - (data_datelevel['Day_High'] -
                                                                                data_datelevel['Day_Low'])
        data_datelevel['R3_Pivot' + type_str] = data_datelevel['PivotPoint'] + (data_datelevel['Day_High'] -
                                                                                data_datelevel['Day_Low'])

    data_datelevel['PivotDate'] = data_datelevel['DatePart'].shift(-1)
    data_datelevel = data_datelevel.drop(['DatePart'], axis=1)
    pivot_data = pd.merge(data, data_datelevel, 'left',
                          left_on='DatePart',
                          right_on='PivotDate')
    pivot_data = pivot_data.drop(['PivotDate'], axis=1)
    return pivot_data


## Initial Inputs
###############################################################
working_dir = 'F:\APT\Historical Data'
info_data = pd.read_csv('Nifty50_Lot_Size.csv')
info_data['Profit'] = 0
info_data['Trades'] = 0

for j in info_data.index.values:
    input_file = 'F:/APT/Historical Data/Data/July/' + info_data.Company[j] + '/5minute.csv'
    output_file = 'F:/APT/Historical Data/Pivot Strategy Output/' + info_data.Company[j] + '_pivot_July.csv'
    lot_size = info_data['Lot Size'][j]
    min_gap = 0.01
    semi_target_multiplier = 0.0005
    target_buffer_multiplier = 0.00075
    min_target = 3500
    # max_stop_loss = 3500
    # semi_target = 1500

    indicator_columns = ['R1_Pivot_Fibonacci',
                         'R2_Pivot_Fibonacci',
                         'R3_Pivot_Fibonacci',
                         'PivotPoint',
                         'S1_Pivot_Fibonacci',
                         'S2_Pivot_Fibonacci',
                         'S3_Pivot_Fibonacci',
                         'R1_Pivot_Simple',
                         'R2_Pivot_Simple',
                         'S1_Pivot_Simple',
                         'S2_Pivot_Simple']

    ## Data Preparation
    ###############################################################
    os.chdir(working_dir)
    ads_fin = pd.read_csv(input_file)
    ads_fin.drop(['Unnamed: 0'], inplace=True, axis=1)
    ads_fin.columns = ['Close', 'Date', 'High', 'Low', 'Open', 'Volume']

    # Date Column Handling
    ads_fin['Date'] = [i[:i.find('+')] for i in ads_fin['Date']]
    ads_fin['Date'] = [datetime.strptime(i, '%Y-%m-%d %H:%M:%S') for i in ads_fin['Date']]
    ads_fin['DatePart'] = [i.date() for i in ads_fin['Date']]
    ads_fin['Year'] = [i.year for i in ads_fin['Date']]

    # Subset Historical Data For Back Testing
    ads_analysis = ads_fin[ads_fin['Date'] >= ads_fin['Date'].max().replace(year=2018, hour=9, minute=15)]
    # ads_analysis = ads_fin[ads_fin['Year'] == 2019]

    # Include Necessary Technical Indicators in the dataset
    ads_analysis = pivotpoints(ads_analysis)  # Getting Simple Pivot Points
    ads_analysis = pivotpoints(ads_analysis, type='fibonacci')  # Getting Fibonacci Pivot Points
    ads_analysis = ads_analysis[ads_analysis.DatePart > min(ads_analysis.DatePart)]
    print('Data Extracted')

    order_status = 'Exit'
    order_signal = ''
    order_price = 0.0
    target = 0.0
    stop_loss = 0.0
    entry_high_target = 0.0
    entry_low_target = 10000.0
    long_count = 0
    short_count = 0
    trade_count = 0
    semi_target_flag = 0
    profit = 0
    skip_date = ads_analysis['DatePart'].min()
    closing_time = ads_analysis['Date'].min() + timedelta(hours=6, minutes=10)
    prev_day_close = float(ads_analysis[ads_analysis['Date'] == closing_time].Close)

    # Preparing Data For Iterating Over Strategy
    # ads_analysis = ads_analysis[ads_analysis['Year'] == 2019]
    ads_analysis['Date'] = [datetime.strptime(str(i), '%Y-%m-%d %H:%M:%S') for i in ads_analysis['Date']]
    ads_iteration = ads_analysis[ads_analysis['Date'] >= ads_analysis['Date'].min() + timedelta(days=1)]
    ads_iteration['Order_Status'] = ''
    ads_iteration['Order_Signal'] = ''
    ads_iteration['Order_Price'] = 0.0
    ads_iteration['Target'] = 0.0
    ads_iteration['Stop_Loss'] = 0.0
    # ads_iteration['Next_Candle_Open'] = ads_iteration['Open'].shift(-1)
    ads_iteration['Hour'] = [j.hour for j in ads_iteration['Date']]
    ads_iteration['Minute'] = [j.minute for j in ads_iteration['Date']]
    print('Data Preparation Completed')

    # Iterating Strategy over all rows
    for i in ads_iteration.index.values:

        # Selecting Tradable Day and Reset Day High and Day Low
        if ads_iteration.Date[i].hour == 9 and ads_iteration.Date[i].minute == 15:
            day_flag = 'selected' if abs(ads_iteration.Open[i] - prev_day_close) > (prev_day_close * min_gap) \
                else 'not selected'
            skip_date = ads_iteration.DatePart[i] if day_flag == 'not selected' else skip_date
            entry_high_target = ads_iteration.High[i]
            entry_low_target = ads_iteration.Low[i]
            print('Date: ' + str(ads_iteration.Date[i]))
            print('Status: ' + day_flag)
            continue

        # Exit from Ongoing Order, if any at 3:25 PM
        elif ads_iteration.Date[i].hour == 15 and ads_iteration.Date[i].minute == 20:

            # Check If Open Order Exists at 3:20
            if order_status == 'Entry':

                # Check if the open order is a long entry
                if order_signal == 'Buy':
                    order_status = 'Exit'
                    order_signal = 'Sell'
                    order_price = ads_iteration.Close[i]
                    trade_count = trade_count + 1
                    long_count = 1
                    short_count = 0
                    semi_target_flag = 0
                    profit = profit + order_price

                    # Print Pointers
                    ads_iteration.Order_Status[i] = order_status
                    ads_iteration.Order_Signal[i] = order_signal
                    ads_iteration.Order_Price[i] = order_price
                    print('Long Exit ---')
                    print('Order Price: ' + str(order_price))
                    print('Remarks: Exit At 3:25 PM')

                # Check If the open order is a short entry
                elif order_signal == 'Sell':
                    order_status = 'Exit'
                    order_signal = 'Buy'
                    order_price = ads_iteration.Close[i]
                    trade_count = trade_count + 1
                    long_count = 0
                    short_count = 1
                    semi_target_flag = 0
                    profit = profit - order_price

                    # Print Pointers
                    ads_iteration.Order_Status[i] = order_status
                    ads_iteration.Order_Signal[i] = order_signal
                    ads_iteration.Order_Price[i] = order_price
                    print('Short Exit ---')
                    print('Order Price: ' + str(order_price))
                    print('Remarks: Exit At 3:25 PM')

        # Reset Pointers at 3:30 PM
        elif ads_iteration.Date[i].hour == 15 and ads_iteration.Date[i].minute == 25:
            prev_day_close = ads_iteration.Close[i]
            long_count = 0
            short_count = 0
            trade_count = 0
            continue

        # Iterate over all the data points for the dates that have been selected by Gap Up/Down Condition
        elif ads_iteration.DatePart[i] != skip_date:

            # If No Open Order
            if order_status == 'Exit':

                # First Trade
                if trade_count == 0:

                    # Long Entry Action
                    if ads_iteration.Close[i] > entry_high_target:
                        order_status = 'Entry'
                        order_signal = 'Buy'
                        semi_target_flag = 0
                        order_price = ads_iteration.Close[i]
                        stop_loss = entry_low_target - (0.00075 * order_price)
                        profit = profit - order_price

                        # Calculating Target
                        deltas = [ads_iteration[indicator][i] - ads_iteration['Close'][i] for indicator in
                                  indicator_columns]
                        pos_deltas = [delta for delta in deltas if delta > (order_price * 0.005)]
                        min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                        target = min_pos_delta + order_price + (order_price * target_buffer_multiplier)

                        # Print Pointers
                        ads_iteration.Order_Status[i] = order_status
                        ads_iteration.Order_Signal[i] = order_signal
                        ads_iteration.Order_Price[i] = order_price
                        ads_iteration.Target[i] = target
                        ads_iteration.Stop_Loss[i] = stop_loss
                        print('Long Entry ---')
                        print('Order Price: ' + str(order_price))
                        print('Target: ' + str(target))
                        print('Stop Loss: ' + str(stop_loss))


                    # Short Entry Action
                    elif ads_iteration.Close[i] < entry_low_target:
                        order_status = 'Entry'
                        order_signal = 'Sell'
                        semi_target_flag = 0
                        order_price = ads_iteration.Close[i]
                        stop_loss = entry_high_target + (0.00075 * order_price)
                        profit = profit + order_price

                        # Calculating Target
                        deltas = [ads_iteration[indicator][i] - ads_iteration['Close'][i] for indicator in
                                  indicator_columns]
                        neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.005)]
                        max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                        target = order_price + max_neg_delta - (order_price * target_buffer_multiplier)

                        # Print Pointers
                        ads_iteration.Order_Status[i] = order_status
                        ads_iteration.Order_Signal[i] = order_signal
                        ads_iteration.Order_Price[i] = order_price
                        ads_iteration.Target[i] = target
                        ads_iteration.Stop_Loss[i] = stop_loss
                        print('Short Entry ---')
                        print('Order Price: ' + str(order_price))
                        print('Target: ' + str(target))
                        print('Stop Loss: ' + str(stop_loss))

                # Other Trade Entries
                else:

                    # Long Entry
                    if (ads_iteration.High[i] > entry_high_target) and (long_count == 0):
                        order_status = 'Entry'
                        order_signal = 'Buy'
                        semi_target_flag = 0
                        order_price = entry_high_target
                        stop_loss = entry_low_target - (0.00075 * order_price)
                        profit = profit - order_price

                        # Calculating Target
                        deltas = [ads_iteration[indicator][i] - ads_iteration['Close'][i] for indicator in
                                  indicator_columns]
                        pos_deltas = [delta for delta in deltas if delta > (order_price * 0.005)]
                        min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                        target = min_pos_delta + order_price + (order_price * target_buffer_multiplier)

                        # Print Pointers
                        ads_iteration.Order_Status[i] = order_status
                        ads_iteration.Order_Signal[i] = order_signal
                        ads_iteration.Order_Price[i] = order_price
                        ads_iteration.Target[i] = target
                        ads_iteration.Stop_Loss[i] = stop_loss
                        print('Long Entry ---')
                        print('Order Price: ' + str(order_price))
                        print('Target: ' + str(target))
                        print('Stop Loss: ' + str(stop_loss))

                    # Short Entry
                    elif (ads_iteration.Low[i] < entry_low_target) and (short_count == 0):
                        order_status = 'Entry'
                        order_signal = 'Sell'
                        semi_target_flag = 0
                        order_price = entry_low_target
                        stop_loss = entry_high_target + (0.00075 * order_price)
                        profit = profit + order_price

                        # Calculating Target
                        deltas = [ads_iteration[indicator][i] - ads_iteration['Close'][i] for indicator in
                                  indicator_columns]
                        neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.005)]
                        max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                        target = order_price + max_neg_delta - (order_price * target_buffer_multiplier)

                        # Print Pointers
                        ads_iteration.Order_Status[i] = order_status
                        ads_iteration.Order_Signal[i] = order_signal
                        ads_iteration.Order_Price[i] = order_price
                        ads_iteration.Target[i] = target
                        ads_iteration.Stop_Loss[i] = stop_loss
                        print('Short Entry ---')
                        print('Order Price: ' + str(order_price))
                        print('Target: ' + str(target))
                        print('Stop Loss: ' + str(stop_loss))

            # If Open Order Exists
            else:

                # If Long Entry Exists
                if order_signal == 'Buy':

                    # Exit From Stop Loss
                    if ads_iteration.Low[i] <= stop_loss:
                        order_status = 'Exit'
                        order_signal = 'Sell'
                        order_price = stop_loss
                        trade_count = trade_count + 1
                        long_count = 1
                        short_count = 0
                        profit = profit + order_price

                        # Print Pointers
                        ads_iteration.Order_Status[i] = order_status
                        ads_iteration.Order_Signal[i] = order_signal
                        ads_iteration.Order_Price[i] = order_price
                        print('Long Exit ---')
                        print('Order Price: ' + str(order_price))
                        print('Remarks: Loss')

                        ## Take Short Entry if semi target is not hit
                        if semi_target_flag == 0:
                            order_status = 'Entry'
                            order_signal = 'Sell'
                            semi_target_flag = 0
                            stop_loss = entry_high_target + (0.00075 * order_price)
                            profit = profit + order_price

                            # Calculating Target
                            deltas = [ads_iteration[indicator][i] - ads_iteration['Close'][i] for indicator in
                                      indicator_columns]
                            neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.005)]
                            max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
                            target = order_price + max_neg_delta - (order_price * target_buffer_multiplier)

                            # Print Pointers
                            ads_iteration.Target[i] = target
                            ads_iteration.Stop_Loss[i] = stop_loss
                            print('Short Entry ---')
                            print('Order Price: ' + str(order_price))
                            print('Target: ' + str(target))
                            print('Stop Loss: ' + str(stop_loss))

                    # Exit From Target
                    elif ads_iteration.High[i] >= target:
                        order_status = 'Exit'
                        order_signal = 'Sell'
                        order_price = target
                        trade_count = trade_count + 1
                        long_count = 1
                        short_count = 0
                        profit = profit + order_price

                        # Print Pointers
                        ads_iteration.Order_Status[i] = order_status
                        ads_iteration.Order_Signal[i] = order_signal
                        ads_iteration.Order_Price[i] = order_price
                        print('Long Exit ---')
                        print('Order Price: ' + str(order_price))
                        print('Remarks: Profit')

                    # Action on Semi Target
                    elif ads_iteration.High[i] >= (order_price + (order_price * semi_target_multiplier)):
                        stop_loss = (order_price + (order_price * semi_target_multiplier))
                        semi_target_flag = 1

                # If Short Entry Exists
                elif order_signal == 'Sell':

                    # Exit From Stop Loss
                    if ads_iteration.High[i] >= stop_loss:
                        order_status = 'Exit'
                        order_signal = 'Buy'
                        order_price = stop_loss
                        trade_count = trade_count + 1
                        long_count = 0
                        short_count = 1
                        profit = profit - order_price

                        # Print Pointers
                        ads_iteration.Order_Status[i] = order_status
                        ads_iteration.Order_Signal[i] = order_signal
                        ads_iteration.Order_Price[i] = order_price
                        print('Short Exit ---')
                        print('Order Price: ' + str(order_price))
                        print('Remarks: Loss')

                        ## Take Long Entry if semi target is not hit
                        if semi_target_flag == 0:
                            order_status = 'Entry'
                            order_signal = 'Buy'
                            stop_loss = entry_low_target - (0.00075 * order_price)
                            profit = profit - order_price

                            # Calculating Target
                            deltas = [ads_iteration[indicator][i] - ads_iteration['Close'][i] for indicator in
                                      indicator_columns]
                            pos_deltas = [delta for delta in deltas if delta > (order_price * 0.005)]
                            min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
                            target = min_pos_delta + order_price + (order_price * target_buffer_multiplier)

                            # Print Pointers
                            ads_iteration.Target[i] = target
                            ads_iteration.Stop_Loss[i] = stop_loss
                            print('Long Entry ---')
                            print('Order Price: ' + str(order_price))
                            print('Target: ' + str(target))
                            print('Stop Loss: ' + str(stop_loss))

                    # Exit From Target
                    elif ads_iteration.Low[i] <= target:
                        order_status = 'Exit'
                        order_signal = 'Buy'
                        order_price = target
                        trade_count = trade_count + 1
                        long_count = 0
                        short_count = 1
                        profit = profit - order_price

                        # Print Pointers
                        ads_iteration.Order_Status[i] = order_status
                        ads_iteration.Order_Signal[i] = order_signal
                        ads_iteration.Order_Price[i] = order_price
                        print('Short Exit ---')
                        print('Order Price: ' + str(order_price))
                        print('Remarks: Profit')

                    # Action on Semi Target
                    elif ads_iteration.Low[i] <= (order_price - (order_price * semi_target_multiplier)):
                        stop_loss = (order_price - (order_price * semi_target_multiplier))

        entry_high_target = max(entry_high_target, ads_iteration.High[i])
        entry_low_target = min(entry_low_target, ads_iteration.Low[i])

    ads_iteration.to_csv(output_file, index=False)
    info_data['Profit'][j] = profit
    info_data['Trades'][j] = len(ads_iteration[ads_iteration.Order_Status == 'Exit'])
    print('Completed For: ' + info_data['Company'][j])

# Write Backtesting Summary
info_data.to_csv('F:/APT/Historical Data/Pivot Strategy Output/BackTest_Summary.csv',index=False)
