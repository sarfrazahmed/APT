## Import Libraries
###############################################################
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import copy
import kiteconnect as kc
import os


## Simple Moving Average
###############################################################
def sma(data, period):
    moving_average = data["Close"].rolling(window=period).mean()
    return moving_average


## RSI
###############################################################
def get_rsi(data, n=14):
    # RSI = 100 - (100 / (1 + RS))
    # where RS = (Wilder-smoothed n-period average of gains / Wilder-smoothed n-period average of -losses)
    # Note that losses above should be positive values
    # Wilder-smoothing = ((previous smoothed avg * (n-1)) + current value to average) / n
    # For the very first "previous smoothed avg" (aka the seed value), we start with a straight average.
    # Therefore, our first RSI value will be for the n+2nd period:
    #     0: first delta is nan
    #     1:
    #     ...
    #     n: lookback period for first Wilder smoothing seed value
    #     n+1: first RSI
    # First, calculate the gain or loss from one price to the next. The first value is nan so replace with 0.
    deltas = (data['Close'] - data['Close'].shift(1)).fillna(0)

    # Calculate the straight average seed values.
    # The first delta is always zero, so we will use a slice of the first n deltas starting at 1,
    # and filter only deltas > 0 to get gains and deltas < 0 to get losses
    avg_of_gains = deltas[1:n + 1][deltas > 0].sum() / n
    avg_of_losses = -deltas[1:n + 1][deltas < 0].sum() / n

    # Set up pd.Series container for RSI values
    rsi_series = pd.Series(0.0, deltas.index)

    # Now calculate RSI using the Wilder smoothing method, starting with n+1 delta.
    up = lambda x: x if x > 0 else 0
    down = lambda x: -x if x < 0 else 0
    i = n + 1
    for d in deltas[n + 1:]:
        avg_of_gains = ((avg_of_gains * (n - 1)) + up(d)) / n
        avg_of_losses = ((avg_of_losses * (n - 1)) + down(d)) / n
        if avg_of_losses != 0:
            rs = avg_of_gains / avg_of_losses
            rsi_series[i] = 100 - (100 / (1 + rs))
        else:
            rsi_series[i] = 100
        i += 1

    return rsi_series


## Exponential Moving Average
###############################################################
def ema(data, period, target):
    exp1 = data[target].ewm(span=period, adjust=False).mean()
    return exp1


## ATR
###############################################################
def ATR(data, period):
    """
    Function to compute Average True Range (ATR)

    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])

    Returns :
        df : Pandas DataFrame with new columns added for
            True Range (TR)
            ATR (ATR_$period)
    """
    atr = 'ATR_' + str(period)

    # Compute true range only if it is not computed and stored earlier in the df
    if not 'TR' in data.columns:
        data['h-l'] = data['Open'] - data['High']
        data['h-yc'] = abs(data['Open'] - data['Low'].shift())
        data['l-yc'] = abs(data['High'] - data['Low'].shift())

        data['TR'] = data[['h-l', 'h-yc', 'l-yc']].max(axis=1)

        data.drop(['h-l', 'h-yc', 'l-yc'], inplace=True, axis=1)

    # Compute EMA of true range using ATR formula after ignoring first row
    data[atr] = ema(data, period, 'TR')
    return data


## Super Trend
###############################################################
def SuperTrend(data, period, multiplier):
    """
    Function to compute SuperTrend

    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        multiplier : Integer indicates value to multiply the ATR
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])

    Returns :
        df : Pandas DataFrame with new columns added for
            True Range (TR), ATR (ATR_$period)
            SuperTrend (ST_$period_$multiplier)
            SuperTrend Direction (STX_$period_$multiplier)
    """

    ATR(data, period)
    atr = 'ATR_' + str(period)
    st = 'ST_' + str(period) + '_' + str(multiplier)
    stx = 'STX_' + str(period) + '_' + str(multiplier)

    """
    SuperTrend Algorithm :

        BASIC UPPERBAND = (HIGH + LOW) / 2 + Multiplier * ATR
        BASIC LOWERBAND = (HIGH + LOW) / 2 - Multiplier * ATR

        FINAL UPPERBAND = IF( (Current BASICUPPERBAND < Previous FINAL UPPERBAND) or (Previous Close > Previous FINAL UPPERBAND))
                            THEN (Current BASIC UPPERBAND) ELSE Previous FINALUPPERBAND)
        FINAL LOWERBAND = IF( (Current BASIC LOWERBAND > Previous FINAL LOWERBAND) or (Previous Close < Previous FINAL LOWERBAND)) 
                            THEN (Current BASIC LOWERBAND) ELSE Previous FINAL LOWERBAND)

        SUPERTREND = IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close <= Current FINAL UPPERBAND)) THEN
                        Current FINAL UPPERBAND
                    ELSE
                        IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close > Current FINAL UPPERBAND)) THEN
                            Current FINAL LOWERBAND
                        ELSE
                            IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close >= Current FINAL LOWERBAND)) THEN
                                Current FINAL LOWERBAND
                            ELSE
                                IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close < Current FINAL LOWERBAND)) THEN
                                    Current FINAL UPPERBAND
    """

    # Compute basic upper and lower bands
    data['basic_ub'] = (data['High'] + data['Low']) / 2 + multiplier * data[atr]
    data['basic_lb'] = (data['High'] + data['Low']) / 2 - multiplier * data[atr]

    # Compute final upper and lower bands
    data['final_ub'] = 0.00
    data['final_lb'] = 0.00
    for i in range(period, len(data)):
        data['final_ub'].iat[i] = data['basic_ub'].iat[i] if data['basic_ub'].iat[i] < data['final_ub'].iat[i - 1] or \
                                                             data['Low'].iat[i - 1] > data['final_ub'].iat[i - 1] else \
            data['final_ub'].iat[i - 1]
        data['final_lb'].iat[i] = data['basic_lb'].iat[i] if data['basic_lb'].iat[i] > data['final_lb'].iat[i - 1] or \
                                                             data['Low'].iat[i - 1] < data['final_lb'].iat[i - 1] else \
            data['final_lb'].iat[i - 1]

    # Set the Supertrend value
    data[st] = 0.00
    for i in range(period, len(data)):
        data[st].iat[i] = data['final_ub'].iat[i] if data[st].iat[i - 1] == data['final_ub'].iat[i - 1] and \
                                                     data['Low'].iat[i] <= data['final_ub'].iat[i] else \
            data['final_lb'].iat[i] if data[st].iat[i - 1] == data['final_ub'].iat[i - 1] and \
                                       data['Low'].iat[i] > data['final_ub'].iat[i] else \
                data['final_lb'].iat[i] if data[st].iat[i - 1] == data['final_lb'].iat[i - 1] and \
                                           data['Low'].iat[i] >= data['final_lb'].iat[i] else \
                    data['final_ub'].iat[i] if data[st].iat[i - 1] == data['final_lb'].iat[i - 1] and \
                                               data['Low'].iat[i] < data['final_lb'].iat[i] else 0.00

    # Mark the trend direction up/down
    data[stx] = np.where((data[st] > 0.00), np.where((data['Low'] < data[st]), 'down', 'up'), np.NaN)

    # Remove basic and final bands from the columns
    data.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)

    data.fillna(0, inplace=True)

    return data


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


## Bollinger Band Calculation
###############################################################
def bband(data, period, multiplier):
    sma_array = sma(data, period)
    sd = data['Close'].rolling(window=period).std()
    data['BBand_Upper'] = sma_array + (multiplier * sd)
    data['BBand_Lower'] = sma_array - (multiplier * sd)

    data['BBand_Upper'].fillna(0, inplace=True)
    data['BBand_Lower'].fillna(0, inplace=True)
    return data


## Function to calculate Gaps between current close and reqd
## indicators (mentioned in the inital input part)
###############################################################
# def find_gaps(data, index, indicators):
#     deltas = [(data[i][index] - data['Close'][index]) for i in indicators]
#     return np.asarray(deltas)


## Function to Execute Long Entry
###############################################################
def long_entry(data, index, qty, sl,tp):
    data.Order_Status[index] = 'Entry'
    data.Order_Signal[index] = 'Buy'
    data.Order_Price[index] = data.Next_Candle_Open[index]
    data.Quantity[index] = qty
    data.Target[index] = data.Next_Candle_Open[index] + (tp / lot_size)
    data.Stop_Loss[index] = sl
    print('Long Entry @' + str(data.Next_Candle_Open[index]))
    return data


## Function to Execute Long Entry
###############################################################
def short_entry(data, index, qty, sl,tp):
    data.Order_Status[index] = 'Entry'
    data.Order_Signal[index] = 'Sell'
    data.Order_Price[index] = data.Next_Candle_Open[index]
    data.Quantity[index] = qty
    data.Target[index] = data.Next_Candle_Open[index] - (tp / lot_size)
    data.Stop_Loss[index] = sl
    print('Short Entry @' + str(data.Next_Candle_Open[index]))
    return data


## Function to Execute Long Exit
###############################################################
def long_exit(data, index, stop_loss):
    data.Order_Status[index] = 'Exit'
    data.Order_Signal[index] = 'Sell'
    data.Order_Price[index] = stop_loss
    data.Quantity[index] = 0
    print('Long Exit @' + str(stop_loss))
    return data


## Function to Execute Long Exit
###############################################################
def short_exit(data, index, stop_loss):
    data.Order_Status[index] = 'Exit'
    data.Order_Signal[index] = 'Buy'
    data.Quantity[index] = 0
    data.Order_Price[index] = stop_loss
    print('Short Exit @' + str(stop_loss))
    return data


## Initial Inputs
###############################################################
working_dir = 'F:\APT\Historical Data'
input_file = 'Titan_5mins.csv'
output_file = 'Gap_Up_Strategy_Output_Titan.csv'
lot_size = 750
max_one_stock_price = 1400
target_profit_1 = 5000
# target_profit_2 = 7000

# indicator_columns = ['R1_Pivot_Fibonacci',
#                      'R2_Pivot_Fibonacci',
#                      'R3_Pivot_Fibonacci',
#                      'PivotPoint',
#                      'S1_Pivot_Fibonacci',
#                      'S2_Pivot_Fibonacci',
#                      'S3_Pivot_Fibonacci']

sma_period = 12
ema_period = 20

bband_period = 20
bband_multiplier = 2

## Data Preparation
###############################################################
os.chdir(working_dir)
ads_fin = pd.read_csv(input_file)
ads_fin.drop(['Unnamed: 0'], inplace=True, axis=1)
ads_fin.columns = ['Close', 'Date', 'High', 'Low', 'Open', 'Volume']

# Date Column Handling
ads_fin['Date'] = [i[:i.find('+')] for i in ads_fin['Date']]
ads_fin['Date'] = [datetime.strptime(i, '%Y-%m-%d %H:%M:%S') for i in ads_fin['Date']]
ads_fin['Year'] = [i.year for i in ads_fin['Date']]
ads_fin['DatePart'] = [i.date() for i in ads_fin['Date']]

# Subset Historical Data For Back Testing
ads_analysis = ads_fin[ads_fin['Year'] == 2019]
# ads_analysis = ads_fin

# Include Necessary Technical Indicators in the dataset
# ads_analysis = pivotpoints(ads_analysis)  # Getting Simple Pivot Points
# ads_analysis = pivotpoints(ads_analysis, type='fibonacci')  # Getting Fibonacci Pivot Points
# ads_analysis['SMA_' + str(sma_period)] = sma(ads_analysis, sma_period)  # Getting Simple Moving Average
# ads_analysis['EMA_' + str(ema_period)] = ema(ads_analysis, ema_period, 'Close')  # Getting Simple Moving Average
# ads_analysis = bband(ads_analysis, bband_period, bband_multiplier)  # Getting Bollinger Band

# ads_analysis.to_csv('AdaniPort_Indicators_2019.csv',index=False)

## Gap Day Strategy
########################################################################


# Strategy Pointers

money = max_one_stock_price * lot_size
order_status = 'Exit'
order_signal = ''
order_price = 0.0
order_qty = 0
# max_close = 0.0
entry_high_target = 0.0
entry_low_target = 10000.0
stop_loss = 0.0
target = 0.0
entry_cost = 0.0
exit_cost = 0.0
target_cross = 0

# Preparing Data For Iterating Over Strategy
ads_analysis['Date'] = [datetime.strptime(str(i), '%Y-%m-%d %H:%M:%S') for i in ads_analysis['Date']]
closing_time = ads_analysis['Date'].min() + timedelta(hours=6, minutes=10)
skip_date = ads_analysis['DatePart'].min()
prev_day_close = float(ads_analysis[ads_analysis['Date'] == closing_time].Close)
ads_iteration = ads_analysis[ads_analysis['Date'] >= ads_analysis['Date'].min() + timedelta(days=1)]
ads_iteration['Order_Status'] = ''
ads_iteration['Order_Signal'] = ''
ads_iteration['Order_Price'] = 0.0
ads_iteration['Quantity'] = 0
ads_iteration['Money'] = money
ads_iteration['Target'] = 0.0
ads_iteration['Stop_Loss'] = 0.0
ads_iteration['Next_Candle_Open'] = ads_iteration['Open'].shift(-1)
ads_iteration['Hour'] = [j.hour for j in ads_iteration['Date']]
ads_iteration['Minute'] = [j.minute for j in ads_iteration['Date']]
print('Data Preparation Completed')

# Iterating Strategy over all rows
for i in ads_iteration.index.values:

    # Selecting Tradable Day and Setting Up Initial Stop Loss and Target
    if ads_iteration.Date[i].hour == 9 and ads_iteration.Date[i].minute == 15:
        # day_flag = 'selected' if ((ads_iteration.Open[i] > entry_high_target) or
        #                          (entry_low_target > ads_iteration.Open[i])) else 'not selected'
        # skip_date = ads_iteration.DatePart[i] if day_flag == 'not selected' else skip_date
        entry_high_target = ads_iteration.High[i]
        entry_low_target = ads_iteration.Low[i]
        ads_iteration.Money[i] = money
        continue

    # Exit from Ongoing Order, if any (Check)
    elif ads_iteration.Date[i].hour == 15 and ads_iteration.Date[i].minute == 20:
        if order_status == 'Entry':
            if order_signal == 'Buy':
                ads_iteration = long_exit(ads_iteration, i, ads_iteration.Close[i])
                order_status = ads_iteration.Order_Status[i]
                order_signal = ads_iteration.Order_Signal[i]
                order_price = ads_iteration.Order_Price[i]
                money = money + order_qty * order_price
                target_cross = 0
                order_qty = 0
                print('Order Status: ' + order_status)
                print('Order Signal: ' + order_signal)

            else:
                ads_iteration = short_exit(ads_iteration, i, ads_iteration.Close[i])
                order_status = ads_iteration.Order_Status[i]
                order_signal = ads_iteration.Order_Signal[i]
                order_price = ads_iteration.Order_Price[i]
                money = money - order_qty * order_price
                target_cross = 0
                order_qty = 0
                print('Order Status: ' + order_status)
                print('Order Signal: ' + order_signal)

    # elif ads_iteration.Date[i].hour == 15 and ads_iteration.Date[i].minute == 25:
    #     prev_day_close = copy.deepcopy(ads_iteration.Close[i])

    elif ads_iteration.DatePart[i] != skip_date:

            if order_status == 'Exit':

                # Long Entry Action
                if ((ads_iteration.Close[i] > entry_high_target) and
                   (ads_iteration.Next_Candle_Open[i] - entry_low_target) < 6):
                    # calc_stop_loss = max(entry_low_target,ads_iteration.Next_Candle_Open[i] - 5)
                    ads_iteration = long_entry(ads_iteration, i, lot_size, entry_low_target,target_profit_1)
                    order_status = ads_iteration.Order_Status[i]
                    order_signal = ads_iteration.Order_Signal[i]
                    target = ads_iteration.Target[i]
                    stop_loss = ads_iteration.Stop_Loss[i]
                    order_price = ads_iteration.Order_Price[i]
                    order_qty = ads_iteration.Quantity[i]
                    money = money - order_qty * order_price
                    # ads_iteration.Money[i] = money

                # Short Entry Action
                elif ((ads_iteration.Close[i] < entry_low_target) and
                     (entry_high_target - ads_iteration.Next_Candle_Open[i]) < 6.5):
                    # calc_stop_loss = min(entry_high_target, ads_iteration.Next_Candle_Open[i] + 5)
                    ads_iteration = short_entry(ads_iteration, i, lot_size, entry_high_target, target_profit_1)
                    order_status = ads_iteration.Order_Status[i]
                    order_signal = ads_iteration.Order_Signal[i]
                    target = ads_iteration.Target[i]
                    stop_loss = ads_iteration.Stop_Loss[i]
                    order_price = ads_iteration.Order_Price[i]
                    order_qty = ads_iteration.Quantity[i]
                    money = money + order_qty * order_price

            # Decision Tree For Exiting the Order
            elif order_status == 'Entry':
                # Exiting From Long Position
                if order_signal == 'Buy':

                    # Exit Condition
                    if ads_iteration.Low[i] < stop_loss:
                        ads_iteration = long_exit(ads_iteration, i, stop_loss)
                        order_status = ads_iteration.Order_Status[i]
                        order_signal = ads_iteration.Order_Signal[i]
                        order_price = ads_iteration.Order_Price[i]
                        money = money + order_qty * order_price
                        # target_cross = 0
                        order_qty = 0
                        print('Order Status: ' + order_status)
                        print('Order Signal: ' + order_signal)

                    elif ads_iteration.High[i] > target:
                        # target_cross = target_cross + 1
                        ads_iteration = long_exit(ads_iteration, i, target)
                        order_status = ads_iteration.Order_Status[i]
                        order_signal = ads_iteration.Order_Signal[i]
                        order_price = ads_iteration.Order_Price[i]
                        money = money + order_qty * order_price
                        # target_cross = 0
                        order_qty = 0
                        print('Order Status: ' + order_status)
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

                # Exiting From Short Position
                elif order_signal == 'Sell':
               # Exit Condition
                    if ads_iteration.High[i] > stop_loss:
                        ads_iteration = short_exit(ads_iteration, i, stop_loss)
                        order_status = ads_iteration.Order_Status[i]
                        order_signal = ads_iteration.Order_Signal[i]
                        order_price = ads_iteration.Order_Price[i]
                        money = money - order_qty * order_price
                        # target_cross = 0
                        order_qty = 0
                        print('Order Status: ' + order_status)
                        print('Order Signal: ' + order_signal)

                    # Order Holding Calculation
                    elif ads_iteration.Low[i] < target:
                        # target_cross = target_cross + 1
                        ads_iteration = short_exit(ads_iteration, i, target)
                        order_status = ads_iteration.Order_Status[i]
                        order_signal = ads_iteration.Order_Signal[i]
                        order_price = ads_iteration.Order_Price[i]
                        money = money - order_qty * order_price
                        # target_cross = 0
                        order_qty = 0
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

    entry_high_target = max(entry_high_target,ads_iteration.High[i])
    entry_low_target = min(entry_low_target,ads_iteration.Low[i])
    ads_iteration.Money[i] = money
# Write to csv
ads_output = ads_iteration[ads_iteration['Quantity'] != lot_size * 2]
ads_output['Month'] = [i.month for i in ads_output['Date']]
ads_output.to_csv(output_file, index=False)
profit_percentage = ((money - (max_one_stock_price * lot_size)) / (max_one_stock_price * lot_size)) * 100
