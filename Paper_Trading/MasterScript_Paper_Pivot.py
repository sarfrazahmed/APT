## Import dependencies
###############################################################
import pandas as pd
import os
import time
import sys
import telebot
from datetime import datetime
from Paper_Trading import StrategyPaperTrading_Pivot as strategy

## Pivot Point Calculation
###############################################################
def pivotpoints(data):
    pivotpoint = (data['High'][0] + data['Low'][0] +
                                    data['Close'][0]) / 3

    s1_simple = (pivotpoint * 2) - data['High'][0]
    s1_fibonacci = pivotpoint - (0.382 * (data['High'][0] - data['Low'][0]))
    s2_simple = pivotpoint - (data['High'][0] - data['Low'][0])
    s2_fibonacci = pivotpoint - (0.618 * (data['High'][0] - data['Low'][0]))
    s3_simple = data['Low'][0] - (2 * (data['High'][0] - pivotpoint))

    r1_simple = (pivotpoint * 2) - data['Low'][0]
    r1_fibonacci = pivotpoint + (0.382 * (data['High'][0] - data['Low'][0]))
    r2_simple = pivotpoint + (data['High'][0] - data['Low'][0])
    r2_fibonacci = pivotpoint + (0.618 * (data['High'][0] - data['Low'][0]))
    r3_simple = data['High'][0] + (2 * (pivotpoint - data['Low'][0]))

    pivots = list([s3_simple,s2_simple,s2_fibonacci,s1_simple,s1_fibonacci,pivotpoint,
                   r1_simple,r1_fibonacci,r2_simple,r2_fibonacci,r3_simple])
    return pivots


## Initial Inputs
###############################################################
def start(name, lot_size):
    bot_token = '823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA'
    chat_id = '-383311990'
    bot = telebot.TeleBot(bot_token)
    bot.config['api_key'] = bot_token
    message = "Stock selected for today: " + str(name)
    bot.send_message(chat_id, message)
    print("Master Script started", flush=True)

    # Set Initial Pointers Value
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
    skip_date = datetime.strptime('2019-08-06','%Y-%m-%d').date()

    result_list = [order_status, order_signal, order_price, target, stop_loss,
              entry_high_target, entry_low_target, long_count, short_count, trade_count,
              semi_target_flag, profit, skip_date]
    Trade_Dataset = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Year', 'DatePart',
                                          'Order_Status', 'Order_Signal', 'Order_Price', 'Target', 'Stop_Loss',
                                          'Hour', 'Minute'])
    count = 0
    while True:
        # Get data after every 5 mins
        if (datetime.now().minute % 5 == 0) and (datetime.now().second >= 3) and count == 0:
            try:
                data = pd.read_csv('D:/APT/APT/Paper_Trading/ohlc_data_' + name + '.csv')
                prev_day_data = pd.read_csv('D:/APT/APT/Paper_Trading/previous_day_data_' + name + '.csv', columns=['Close', 'Date', 'High', 'Low', 'Open', 'Volume'])
            except:
                time.sleep(1)
                continue

            data.columns = ['Date', 'Open', 'High', 'Low', 'Close']

            # Date Column Handling
            data['Date'] = [datetime.strptime(i, '%Y-%m-%d %H:%M:%S') for i in data['Date']]
            data['Year'] = [i.year for i in data['Date']]
            data['DatePart'] = [i.date() for i in data['Date']]

            # Include Pointer Columns
            data['Order_Status'] = ''
            data['Order_Signal'] = ''
            data['Order_Price'] = 0.0
            data['Target'] = 0.0
            data['Stop_Loss'] = 0.0
            data['Day_High'] = 0.0
            data['Day_Low'] = 0.0
            data['Long_Count'] = 0
            data['Short_Count'] = 0
            data['Trade_Count'] = 0
            data['Profit'] = 0

            data['Hour'] = [j.hour for j in data['Date']]
            data['Minute'] = [j.minute for j in data['Date']]

            pivots = pivotpoints(prev_day_data)
            print('Data Preparation Completed', flush=True)

            # Implement Strategy
            data, result_list = strategy.GapUpStrategy_Pivot(data = data, name = name, lot_size = lot_size,
                                                             pivots = pivots, order_status= result_list[0],
                                                             order_signal= result_list[1], order_price= result_list[2],
                                                             target= result_list[3], stop_loss= result_list[4],
                                                             entry_high_target= result_list[5],
                                                             entry_low_target= result_list[6],
                                                             long_count= result_list[7], short_count= result_list[8],
                                                             trade_count= result_list[9],
                                                             semi_target_flag= result_list[10], profit= result_list[11],
                                                             skip_date= result_list[12],
                                                             prev_day_close = prev_day_data.Close[0])
            if data.Order_Signal[0] != "":

                # Update Trade Dataset
                Trade_Dataset = Trade_Dataset.append(data)

                # Generate Message for telegram
                message = 'Stock Name: ' + name + '\n Order Status: ' + result_list[0] + \
                    '\n Order Signal: ' + result_list[1] + '\n Order Price: ' + str(result_list[2]) + \
                          '\n Target: ' + str(result_list[3]) + '\n Stop Loss: ' + str(result_list[4])
                bot.send_message(chat_id, message)

                # Write Updated Trade History as CSV
                Trade_Dataset.to_csv('PaperTrading_Output' + name + '.csv', index=False)

            # Sleep for 4 min
            time.sleep(250)
            count = 1

        else:
            count = 0

if __name__ == '__main__':
    os.chdir("D:\APT\APT\Paper_Trading")

    # Get User Input from Bash File
    name = sys.argv[1]
    lot_size = int(sys.argv[2])
    start(name, lot_size)

