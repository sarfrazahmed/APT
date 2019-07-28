## Import Libraries
###############################################################
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import copy
import kiteconnect as kc
import os


## Function to Execute Long Entry
###############################################################
def long_entry(data, index, lot_size, sl, tp):
    data.Order_Status[index] = 'Entry'
    data.Order_Signal[index] = 'Buy'
    data.Order_Price[index] = data.Close[index]
    # data.Quantity[index] = qty
    data.Target[index] = data.Close[index] + (tp / lot_size)
    data.Stop_Loss[index] = sl
    print('Long Entry @' + str(data.Close[index]))
    return data


## Function to Execute Long Entry
###############################################################
def short_entry(data, index, lot_size, sl, tp):
    data.Order_Status[index] = 'Entry'
    data.Order_Signal[index] = 'Sell'
    data.Order_Price[index] = data.Close[index]
    # data.Quantity[index] = qty
    data.Target[index] = data.Close[index] + (tp / lot_size)
    data.Stop_Loss[index] = sl
    print('Long Entry @' + str(data.Close[index]))
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


## Gap-Up Strategy Function For Paper Trading
###############################################################
def GapUpStrategy(data, target_profit_1, semi_target, max_stop_loss, lot_size,
                  order_status, order_signal,
                  order_price, entry_high_target, entry_low_target,
                  stop_loss, target, skip_date):
    if data.Date[0].hour == 9 and data.Date[0].minute == 15:
        # day_flag = 'selected' if ((ads_iteration.Open[i] > entry_high_target) or
        #                          (entry_low_target > ads_iteration.Open[i])) else 'not selected'
        # skip_date = ads_iteration.DatePart[i] if day_flag == 'not selected' else skip_date
        entry_high_target = data.High[0]
        entry_low_target = data.Low[0]

    # Exit from Ongoing Order, if any (Check)
    elif data.Date[0].hour == 15 and data.Date[0].minute == 20:
        if order_status == 'Entry':
            if order_signal == 'Buy':
                data = long_exit(data, 0, data.Close[0])
                order_status = data.Order_Status[0]
                order_signal = data.Order_Signal[0]
                order_price = data.Order_Price[0]
                # money = money + order_qty * order_price
                # target_cross = 0
                # order_qty = 0
                print('Order Status: ' + order_status)
                print('Order Signal: ' + order_signal)

            else:
                data = short_exit(data, 0, data.Close[0])
                order_status = data.Order_Status[0]
                order_signal = data.Order_Signal[0]
                order_price = data.Order_Price[0]
                # money = money + order_qty * order_price
                # target_cross = 0
                # order_qty = 0
                print('Order Status: ' + order_status)
                print('Order Signal: ' + order_signal)

    elif data.DatePart[0] != skip_date:
        if order_status == 'Exit':
            # Long Entry Action
            if data.Close[0] > entry_high_target:
                # calc_stop_loss = max(entry_low_target,(ads_iteration.Next_Candle_Open[i] - (max_stop_loss / lot_size)))
                calc_stop_loss = data.Close[0] - (max_stop_loss / lot_size)
                data = long_entry(data, 0, lot_size, calc_stop_loss, target_profit_1)
                order_status = data.Order_Status[0]
                order_signal = data.Order_Signal[0]
                target = data.Target[0]
                stop_loss = data.Stop_Loss[0]
                order_price = data.Order_Price[0]
                # order_qty = data.Quantity[i]
                # money = money - order_qty * order_price
                # data.Money[i] = money

            # Short Entry Action
            elif data.Close[0] < entry_low_target:
                # calc_stop_loss = min(entry_high_target, (ads_iteration.Next_Candle_Open[i] + (max_stop_loss / lot_size)))
                calc_stop_loss = data.Close[0] + (max_stop_loss / lot_size)
                data = short_entry(data, 0, lot_size, calc_stop_loss, target_profit_1)
                order_status = data.Order_Status[0]
                order_signal = data.Order_Signal[0]
                target = data.Target[0]
                stop_loss = data.Stop_Loss[0]
                order_price = data.Order_Price[0]
                # order_qty = data.Quantity[0]
                # money = money + order_qty * order_price

        # Decision Tree For Exiting the Order
        elif order_status == 'Entry':
            # Exiting From Long Position
            if order_signal == 'Buy':

                # Exit Condition
                if data.Low[0] < stop_loss:
                    data = long_exit(data, 0, stop_loss)
                    order_status = data.Order_Status[0]
                    order_signal = data.Order_Signal[0]
                    order_price = data.Order_Price[0]
                    # money = money + order_qty * order_price
                    # target_cross = 0
                    # order_qty = 0
                    print('Order Status: ' + order_status)
                    print('Order Signal: ' + order_signal)

                elif data.High[0] > target:
                    # target_cross = target_cross + 1
                    data = long_exit(data, 0, target)
                    order_status = data.Order_Status[0]
                    order_signal = data.Order_Signal[0]
                    order_price = data.Order_Price[0]
                    # money = money + order_qty * order_price
                    # target_cross = 0
                    # order_qty = 0
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
                elif (data.High[0] - order_price) > (semi_target / lot_size):
                    stop_loss = copy.deepcopy(order_price + ((semi_target / lot_size) * 0.5))

            # Exiting From Short Position
            elif order_signal == 'Sell':
                # Exit Condition
                if data.High[0] > stop_loss:
                    data = short_exit(data, 0, stop_loss)
                    order_status = data.Order_Status[0]
                    order_signal = data.Order_Signal[0]
                    order_price = data.Order_Price[0]
                    # money = money - order_qty * order_price
                    # target_cross = 0
                    # order_qty = 0
                    print('Order Status: ' + order_status)
                    print('Order Signal: ' + order_signal)

                # Order Holding Calculation
                elif data.Low[i] < target:
                    # target_cross = target_cross + 1
                    data = short_exit(data, 0, target)
                    order_status = data.Order_Status[0]
                    order_signal = data.Order_Signal[0]
                    order_price = data.Order_Price[0]
                    # money = money - order_qty * order_price
                    # target_cross = 0
                    # order_qty = 0
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

                elif (order_price - data.Low[0]) > (semi_target / lot_size):
                    stop_loss = copy.deepcopy(order_price - ((semi_target / lot_size) * 0.5))

    entry_high_target = max(entry_high_target, data.High[0])
    entry_low_target = min(entry_low_target, data.Low[0])

    result_list = [order_status, order_signal,
                  order_price, entry_high_target, entry_low_target,
                  stop_loss, target, skip_date]
    return data, result_list
