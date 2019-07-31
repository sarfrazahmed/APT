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


## Function to Execute Long Entry
###############################################################
def long_entry(data, index, sl):
    data.Order_Status[index] = 'Entry'
    data.Order_Signal[index] = 'Buy'
    data.Order_Price[index] = data.Next_Candle_Open[index]
    data.Stop_Loss[index] = sl
    print('Long Entry @' + str(data.Next_Candle_Open[index]))
    return data


## Function to Execute Long Entry
###############################################################
def short_entry(data, index, sl):
    data.Order_Status[index] = 'Entry'
    data.Order_Signal[index] = 'Sell'
    data.Order_Price[index] = data.Next_Candle_Open[index]
    data.Stop_Loss[index] = sl
    print('Short Entry @' + str(data.Next_Candle_Open[index]))
    return data


## Function to Execute Long Exit
###############################################################
def long_exit(data, index, stop_loss):
    data.Order_Status[index] = 'Exit'
    data.Order_Signal[index] = 'Sell'
    data.Order_Price[index] = stop_loss
    print('Long Exit @' + str(stop_loss))
    return data


## Function to Execute Long Exit
###############################################################
def short_exit(data, index, stop_loss):
    data.Order_Status[index] = 'Exit'
    data.Order_Signal[index] = 'Buy'
    data.Order_Price[index] = stop_loss
    print('Short Exit @' + str(stop_loss))
    return data


## Initial Inputs
###############################################################
working_dir = 'F:\APT\Historical Data'
input_file = 'SunPharma_5MIN.csv'
output_file = 'Gap_Up_Strategy_Output_Sunpharma_pivot.csv'
lot_size = 1100
min_gap = 0.01
min_target = 3500
max_stop_loss = 1500
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
# ads_analysis = ads_fin[ads_fin['Date'] >= ads_fin['Date'].max().replace(year = 2018,hour = 9, minute = 15)]
ads_analysis = ads_fin[ads_fin['Year'] == 2019]

# Include Necessary Technical Indicators in the dataset
ads_analysis = pivotpoints(ads_analysis)  # Getting Simple Pivot Points
ads_analysis = pivotpoints(ads_analysis, type='fibonacci')  # Getting Fibonacci Pivot Points
ads_analysis = ads_analysis[ads_analysis.DatePart > min(ads_analysis.DatePart)]
print('Data Extracted')

# Define Target for each point
ads_analysis['Target_High'] = 0.01
ads_analysis['Target_Low'] = 0.01
for i in ads_analysis.index.values:
    deltas = [ads_analysis[indicator][i] - ads_analysis['Close'][i] for indicator in indicator_columns]
    pos_deltas = [delta for delta in deltas if delta > 5]
    neg_deltas = [delta for delta in deltas if delta < -5]
    min_pos_delta = min(pos_deltas) if len(pos_deltas) != 0 else (min_target / lot_size)
    max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else ((min_target / lot_size) * -1)
    ads_analysis.Target_High[i] = ads_analysis['Close'][i] + min_pos_delta
    ads_analysis.Target_Low[i] = ads_analysis['Close'][i] + max_neg_delta
    print(ads_analysis.Date[i])

# ads_analysis.to_csv('Reliance_5mins_Pivot.csv',index = False)
print('Target Points Included')


# Define Strategy Pointers
ads_analysis = pd.read_csv('Reliance_5mins_Pivot.csv')
ads_analysis['Date'] = [datetime.strptime(i, '%Y-%m-%d %H:%M:%S') for i in ads_analysis['Date']]
ads_analysis['DatePart'] = [i.date() for i in ads_analysis['Date']]
ads_analysis['Year'] = [i.year for i in ads_analysis['Date']]

order_status = 'Exit'
order_signal = ''
order_price = 0.0
target = 0.0
stop_loss = 0.0
entry_high_target = 0.0
entry_low_target = 10000.0
long_count = 0
short_count = 0
skip_date = ads_analysis['DatePart'].min()
closing_time = ads_analysis['Date'].min() + timedelta(hours=6, minutes=10)
prev_day_close = float(ads_analysis[ads_analysis['Date'] == closing_time].Close)


# Preparing Data For Iterating Over Strategy
ads_analysis = ads_analysis[ads_analysis['Year'] == 2019]
ads_analysis['Date'] = [datetime.strptime(str(i), '%Y-%m-%d %H:%M:%S') for i in ads_analysis['Date']]
ads_iteration = ads_analysis[ads_analysis['Date'] >= ads_analysis['Date'].min() + timedelta(days=1)]
ads_iteration['Order_Status'] = ''
ads_iteration['Order_Signal'] = ''
ads_iteration['Order_Price'] = 0.0
ads_iteration['Stop_Loss'] = 0.0
ads_iteration['Next_Candle_Open'] = ads_iteration['Open'].shift(-1)
ads_iteration['Hour'] = [j.hour for j in ads_iteration['Date']]
ads_iteration['Minute'] = [j.minute for j in ads_iteration['Date']]
print('Data Preparation Completed')

# Iterating Strategy over all rows
for i in ads_iteration.index.values:

    # Selecting Tradable Day and Setting Up Initial Stop Loss and Target
    if ads_iteration.Date[i].hour == 9 and ads_iteration.Date[i].minute == 15:
        day_flag = 'selected' if abs(ads_iteration.Open[i] - prev_day_close) > (prev_day_close * min_gap) \
            else 'not selected'
        skip_date = ads_iteration.DatePart[i] if day_flag == 'not selected' else skip_date
        entry_high_target = ads_iteration.High[i]
        entry_low_target = ads_iteration.Low[i]
        print('Date: '+ str(ads_iteration.Date[i]))
        print('Status: ' + day_flag)
        continue

    # Exit from Ongoing Order, if any (Check)
    elif ads_iteration.Date[i].hour == 15 and ads_iteration.Date[i].minute == 20:
        if order_status == 'Entry':
            if order_signal == 'Buy':
                ads_iteration = long_exit(ads_iteration, i, stop_loss)
                order_status = ads_iteration.Order_Status[i]
                order_signal = ads_iteration.Order_Signal[i]
                order_price = ads_iteration.Order_Price[i]
                long_count = 1
                short_count = 0
                print('Order Status: ' + order_status)
                print('Order Signal: ' + order_signal)

            else:
                ads_iteration = short_exit(ads_iteration, i, ads_iteration.Close[i])
                order_status = ads_iteration.Order_Status[i]
                order_signal = ads_iteration.Order_Signal[i]
                order_price = ads_iteration.Order_Price[i]
                short_count = 1
                long_count = 0
                print('Order Status: ' + order_status)
                print('Order Signal: ' + order_signal)

    elif ads_iteration.Date[i].hour == 15 and ads_iteration.Date[i].minute == 25:
        prev_day_close = ads_iteration.Close[i]
        long_count = 0
        short_count = 0
        continue

    elif ads_iteration.DatePart[i] != skip_date:

            if order_status == 'Exit':

                # Long Entry Action
                if (ads_iteration.Close[i] > entry_high_target) and \
                        (long_count == 0):
                    # calc_stop_loss = max(entry_low_target,(ads_iteration.Next_Candle_Open[i] -
                    # (max_stop_loss / lot_size)))
                    ads_iteration = long_entry(ads_iteration, i, (ads_iteration.Next_Candle_Open[i] -
                    (max_stop_loss / lot_size)))
                    order_status = ads_iteration.Order_Status[i]
                    order_signal = ads_iteration.Order_Signal[i]
                    target = ads_iteration.Target_High[i]
                    stop_loss = ads_iteration.Stop_Loss[i]
                    order_price = ads_iteration.Order_Price[i]

                # Short Entry Action
                elif (ads_iteration.Close[i] < entry_low_target) and \
                        (short_count == 0):
                    # calc_stop_loss = min(entry_high_target,(ads_iteration.Next_Candle_Open[i] +
                    # (max_stop_loss / lot_size)))
                    ads_iteration = short_entry(ads_iteration, i, (ads_iteration.Next_Candle_Open[i] +
                    (max_stop_loss / lot_size)))
                    order_status = ads_iteration.Order_Status[i]
                    order_signal = ads_iteration.Order_Signal[i]
                    target = ads_iteration.Target_Low[i]
                    stop_loss = ads_iteration.Stop_Loss[i]
                    order_price = ads_iteration.Order_Price[i]

            # Decision Tree For Exiting the Order
            elif order_status == 'Entry':
                # Exiting From Long Position
                if order_signal == 'Buy':

                    # Exit Condition
                    if ads_iteration.Low[i] <= stop_loss:
                        ads_iteration = long_exit(ads_iteration, i, stop_loss)
                        order_status = ads_iteration.Order_Status[i]
                        order_signal = ads_iteration.Order_Signal[i]
                        order_price = ads_iteration.Order_Price[i]
                        long_count = 1
                        short_count = 0
                        print('Order Status: ' + order_status)
                        print('Order Signal: ' + order_signal)

                    elif ads_iteration.High[i] >= target:
                        # target_cross = target_cross + 1
                        ads_iteration = long_exit(ads_iteration, i, target)
                        order_status = ads_iteration.Order_Status[i]
                        order_signal = ads_iteration.Order_Signal[i]
                        order_price = ads_iteration.Order_Price[i]
                        long_count = 1
                        short_count = 0
                        print('Order Status: ' +  order_status)
                        print('Order Signal: ' + order_signal)
                        # Semi Exit
                        # if target_cross == 1:
                        #     ads_iteration.Quantity[i] = int(order_qty * 0.5)
                        #     ads_iteration.Order_Price[i] = target
                        #     stop_loss = order_price
                        #     order_price = target
                        #     order_qty = ads_iteration.Quantity[i]
                        #     money = money + order_qty * order_price
                        #     target = ((target_profit_2 - target_profit_1) / lot_size) + order_price
                        #
                        # else:
                        #     ads_iteration = long_exit(ads_iteration, i, target)
                        #     order_status = ads_iteration.Order_Status[i]
                        #     order_signal = ads_iteration.Order_Signal[i]
                        #     order_price = ads_iteration.Order_Price[i]
                        #     money = money + order_qty * order_price
                        #     target_cross = 0
                        #     order_qty = 0
                        #     print('Order Status: ' + order_status)
                        #     print('Order Signal: ' + order_signal)
                    elif (ads_iteration.High[i] - order_price) > (min_target / lot_size):
                        stop_loss = order_price + ((min_target / lot_size) * 0.5)

                # Exiting From Short Position
                elif order_signal == 'Sell':
               # Exit Condition
                    if ads_iteration.High[i] >= stop_loss:
                        ads_iteration = short_exit(ads_iteration, i, stop_loss)
                        order_status = ads_iteration.Order_Status[i]
                        order_signal = ads_iteration.Order_Signal[i]
                        order_price = ads_iteration.Order_Price[i]
                        short_count = 1
                        long_count = 0
                        print('Order Status: ' + order_status)
                        print('Order Signal: ' + order_signal)

                    # Order Holding Calculation
                    elif ads_iteration.Low[i] <= target:
                        # target_cross = target_cross + 1
                        ads_iteration = short_exit(ads_iteration, i, target)
                        order_status = ads_iteration.Order_Status[i]
                        order_signal = ads_iteration.Order_Signal[i]
                        order_price = ads_iteration.Order_Price[i]
                        short_count = 1
                        long_count = 0
                        print('Order Status: ' + order_status)
                        print('Order Signal: ' + order_signal)
                        # Semi Exit
                        # if target_cross == 1:
                        #     ads_iteration.Quantity[i] = int(order_qty * 0.5)
                        #     ads_iteration.Order_Price[i] = target
                        #     stop_loss = order_price
                        #     order_price = target
                        #     order_qty = ads_iteration.Quantity[i]
                        #     money = money - order_qty * order_price
                        #     target = ((target_profit_2 - target_profit_1) / lot_size) + order_price
                        #
                        # else:
                        #     ads_iteration = short_exit(ads_iteration, i, target)
                        #     order_status = ads_iteration.Order_Status[i]
                        #     order_signal = ads_iteration.Order_Signal[i]
                        #     order_price = ads_iteration.Order_Price[i]
                        #     money = money - order_qty * order_price
                        #     target_cross = 0
                        #     order_qty = 0
                        #     print('Order Status: ' + order_status)
                        #     print('Order Signal: ' + order_signal)

                    elif (order_price - ads_iteration.Low[i]) > (min_target / lot_size):
                        stop_loss = order_price - ((min_target / lot_size) * 0.5)

    entry_high_target = max(entry_high_target,ads_iteration.High[i])
    entry_low_target = min(entry_low_target,ads_iteration.Low[i])

profit = sum(ads_iteration.Order_Price[ads_iteration['Order_Signal'] == 'Sell']) - \
sum(ads_iteration.Order_Price[ads_iteration['Order_Signal'] == 'Buy'])
profit_percentage = (profit / max(ads_iteration.High)) * 100
ads_iteration.to_csv(output_file, index=False)