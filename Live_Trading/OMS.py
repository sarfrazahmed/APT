# Import dependencies
import pandas as pd
from kiteconnect import KiteConnect
import configparser
import os
import time
import sys
from datetime import datetime
import requests


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
    if transaction_type == 'Buy':
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


def start(name, access_token, lot_size):
    # Authenticate
    time.sleep(140)
    path = '/home/ubuntu/APT/APT/Live_Trading'
    os.chdir(path)
    config = configparser.ConfigParser()
    config_path = path + '/config.ini'
    config.read(config_path)
    api_key = config['API']['API_KEY']

    # Connect to kite
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    # Initialise variables
    first_order = 1
    stoploss_modified = 0
    local_order = 0

    day_high = 0
    day_low = 0
    quantity = 5

    # Read previous day data file
    data = pd.read_csv(path + '/previous_day_data_' + name + '.csv')
    pivots = pivotpoints(data)

    # Local orders dataframes
    strategy_orders = pd.DataFrame()
    previous_strategy_orders = pd.DataFrame()

    # Create current order tracker dataframe
    current_order_parameters = ['order_id', 'order_type', 'transaction_type', 'parent_order_id', 'price', 'status']
    current_order = pd.DataFrame(columns=current_order_parameters)
    all_orders = pd.DataFrame(columns=current_order_parameters)

    # Get order update from KITE
    previous_kite_orders = pd.DataFrame(kite.orders())
    print("Order Management Started")
    message = ("Order Management script started for: " + str(name))
    requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

    # Start infinite loop
    while True:
        if datetime.now().second % 10 == 0:
            kite_orders = pd.DataFrame(kite.orders())
            current_order = current_order.reset_index(drop=True)

            # Proceed if any new updates are there
            if not kite_orders.equals(previous_kite_orders):

                if len(current_order) == 1:
                    # check if status of order is complete
                    if kite_orders['status'][kite_orders['order_id'] == current_order.at[0, 'order_id']].values[0] == 'COMPLETE':
                        # change current order status
                        current_order = current_order.reset_index(drop=True)
                        current_order.at[0, 'status'] = 'COMPLETE'

                        # append executed order to all orders
                        all_orders = all_orders.append(current_order)

                        # append stoploss and target orders
                        current_order = current_order.append(kite_orders.loc[kite_orders['parent_order_id'] == current_order.at[0, 'order_id'], current_order_parameters])
                        current_order = current_order.reset_index(drop=True)

                        # send message to telegram
                        message = (str(current_order.at[0, 'transaction_type'])+" order executed for " + name + " at " + str(current_order.at[0, 'price']))
                        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)


                if len(current_order) == 2:
                    # cancel secondary order on execution of primary order and vice-versa
                    if kite_orders['status'][kite_orders['order_id'] == current_order.at[0, 'order_id']].values[0] == 'COMPLETE':
                        kite.cancel_order(variety='bo',
                                          order_id=current_order.at[1, 'order_id'].values[0])

                        # drop cancelled order row
                        current_order = current_order.drop(current_order.index[1])
                        first_order = 0

                        # change current order status
                        current_order = current_order.reset_index(drop=True)
                        current_order.at[0, 'status'] = 'COMPLETE'

                        # append executed order to all orders
                        all_orders = all_orders.append(current_order)

                        # append stoploss and target orders
                        current_order = current_order.append(kite_orders.loc[kite_orders['parent_order_id'] == current_order.at[0, 'order_id'], current_order_parameters])
                        current_order = current_order.reset_index(drop=True)

                        # send message to telegram
                        message = (str(current_order.at[0, 'transaction_type']) + " order executed for " + name + " at " + str(current_order.at[0, 'price']))
                        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)



                    elif kite_orders['status'][kite_orders['order_id'] == current_order.at[1, 'order_id']].values[0] == 'COMPLETE':
                        kite.cancel_order(variety='bo',
                                          order_id=current_order.at[0, 'order_id'].values[0])

                        # drop cancelled order row
                        current_order = current_order.drop(current_order.index[0])
                        first_order = 0

                        # change current order status
                        current_order = current_order.reset_index(drop=True)
                        current_order.at[0, 'status'] = 'COMPLETE'

                        # append stoploss and target orders
                        current_order = current_order.append(kite_orders.loc[kite_orders['parent_order_id'] == current_order.at[0, 'order_id'], current_order_parameters])
                        current_order = current_order.reset_index(drop=True)

                        # append executed order to all orders
                        all_orders = all_orders.append(current_order)

                        # send message to telegram
                        message = (str(current_order.at[0, 'transaction_type']) + " order executed for " + name + " at " + str(current_order.at[0, 'price']))
                        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                # if stoploss hits
                if len(current_order) == 3:
                    if kite_orders['status'][kite_orders['order_id'] == current_order['order_id'][current_order['order_type'] == 'SL'].values[0]].values[0] == 'COMPLETE':

                        # order transaction type
                        primary_transaction_type = 'SELL' if current_order.at[0, 'transaction_type'] == 'BUY' else 'BUY'
                        secondary_transaction_type = current_order.at[0, 'transaction_type']

                        # entry price
                        primary_entry_price = current_order['price'][current_order['order_type'] == 'SL']
                        secondary_entry_price = day_high if primary_transaction_type == 'SELL' else day_low

                        # update local order id
                        local_order = local_order + 1

                        # clear previous orders
                        current_order = current_order[0:0]

                        # place first order at current market price
                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=primary_transaction_type,
                                                    quantity=quantity,
                                                    price=primary_entry_price,
                                                    trigger_price=primary_entry_price,
                                                    order_type=kite.ORDER_TYPE_SL,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=(day_high - primary_entry_price) if primary_transaction_type == 'SELL' else (primary_entry_price - day_low),
                                                    squareoff=get_target(pivots, primary_entry_price, primary_transaction_type, lot_size))
                        current_order = current_order.append({'order_id': order_id,
                                                              'local_order_id': local_order,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': primary_transaction_type,
                                                              'parent_order_id': 'NA',
                                                              'price': primary_entry_price,
                                                              'status': 'OPEN'}, ignore_index=True)

                        # send message to telegram
                        message = (primary_transaction_type + " order placed for " + name + " at " + str(primary_entry_price))
                        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                        # place second order at stoploss
                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=secondary_transaction_type,
                                                    quantity=quantity,
                                                    price=secondary_entry_price,
                                                    trigger_price=secondary_entry_price,
                                                    order_type=kite.ORDER_TYPE_SL,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=(day_high - secondary_entry_price) if secondary_transaction_type == 'SELL' else (secondary_entry_price - day_low),
                                                    squareoff=get_target(pivots, secondary_entry_price, secondary_transaction_type, lot_size))
                        current_order = current_order.append({'order_id': order_id,
                                                              'local_order_id': local_order+1,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': secondary_transaction_type,
                                                              'parent_order_id': 'NA',
                                                              'price': secondary_entry_price,
                                                              'status': 'OPEN'}, ignore_index=True)

                        # send message to telegram
                        message = (secondary_transaction_type + " order placed for " + name + " at " + str(secondary_entry_price))
                        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                        # update stoploss status
                        stoploss_modified = 0

                # if target hits
                if len(current_order) == 3:
                    if kite_orders['status'][kite_orders['order_id'] == current_order['order_id'][(current_order['order_type'] == 'LIMIT') & (current_order['transaction_type'] != current_order.at[0, 'transaction_type'])].values[0]].values[0] == 'COMPLETE':

                        # order transaction type
                        transaction_type = 'SELL' if current_order.at[0, 'transaction_type'] == 'BUY' else 'BUY'

                        # entry price
                        entry_price = day_low if transaction_type == 'SELL' else day_high

                        # update local order id
                        local_order = local_order + 1

                        # clear previous orders
                        current_order = current_order[0:0]

                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=transaction_type,
                                                    quantity=quantity,
                                                    price=entry_price,
                                                    trigger_price=entry_price,
                                                    order_type=kite.ORDER_TYPE_SL,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=(day_high - entry_price) if transaction_type == 'SELL' else (entry_price - day_low),
                                                    squareoff=get_target(pivots, entry_price, transaction_type, lot_size))
                        current_order = current_order.append({'order_id': order_id,
                                                              'local_order_id': local_order,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': transaction_type,
                                                              'parent_order_id': 'NA',
                                                              'price': entry_price,
                                                              'status': 'OPEN'}, ignore_index=True)

                        # send message to telegram
                        message = (transaction_type + " order placed for " + name + " at " + str(entry_price))
                        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                        # update stoploss status
                        stoploss_modified = 0

                # copy current orders to previous orders
                previous_kite_orders = kite_orders.copy(deep=True)
            time.sleep(1)


        elif datetime.now().minute % 5 == 0 and datetime.now().second % 15 == 0:
            if os.path.isfile('live_order_' + name + '_' + str(datetime.now().date()) + '.csv'):
                strategy_orders = pd.read_csv('live_order_' + name + '_' + str(datetime.now().date()) + '.csv')

                # if orders present in strategy orders file
                if not strategy_orders.equals(previous_strategy_orders):

                    # first order of the day
                    if first_order == 1:
                        local_order = strategy_orders.at[0, 'order_id']
                        # place first order at current market price
                        transaction_type = strategy_orders.at[0, 'transaction_type']
                        entry_price = strategy_orders.at[0, 'price']
                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=transaction_type,
                                                    quantity=quantity,
                                                    price=entry_price,
                                                    trigger_price=entry_price,
                                                    order_type=kite.ORDER_TYPE_SL,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=(strategy_orders.at[0, 'stoploss'] - entry_price) if transaction_type == 'SELL' else ( entry_price - strategy_orders.at[0, 'stoploss']),
                                                    squareoff=(entry_price - strategy_orders.at[0, 'target']) if transaction_type == 'SELL' else (strategy_orders.at[0, 'target'] - entry_price))
                        current_order = current_order.append({'order_id': order_id,
                                                              'local_order_id': local_order,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': transaction_type,
                                                              'parent_order_id': 'NA',
                                                              'price': entry_price,
                                                              'status': 'OPEN'}, ignore_index=True)

                        # send message to telegram
                        message = (transaction_type + " order placed for " + name + " at " + str(entry_price))
                        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                        # place second order at stoploss
                        transaction_type = 'SELL' if strategy_orders.at[0, 'transaction_type'] == 'BUY' else 'BUY'
                        entry_price = strategy_orders.at[0, 'stoploss']
                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=transaction_type,
                                                    quantity=quantity,
                                                    price=entry_price,
                                                    trigger_price=entry_price,
                                                    order_type=kite.ORDER_TYPE_SL,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=(day_high - entry_price) if strategy_orders.at[0, 'transaction_type'] == 'SELL' else (entry_price - day_low),
                                                    squareoff=get_target(pivots, entry_price, transaction_type, lot_size))
                        current_order = current_order.append({'order_id': order_id,
                                                              'local_order_id': local_order+1,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': transaction_type,
                                                              'parent_order_id': 'NA',
                                                              'price': entry_price,
                                                              'status': 'OPEN'}, ignore_index=True)
                        # send message to telegram
                        message = (str(transaction_type) + " order placed for " + name + " at " + str(entry_price))
                        requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                        first_order = 0
                        local_order = local_order + 1


                    # update day high and day low
                    day_high = strategy_orders.loc[(strategy_orders['order_id'] == current_order.at[0, 'local_order_id']), 'day_high']
                    day_low = strategy_orders.loc[(strategy_orders['order_id'] == current_order.at[0, 'local_order_id']), 'day_low']

                    # modify stoploss if semi-target is hit
                    if strategy_orders['semi-target_status'][strategy_orders['order_id'] == current_order.at[0, 'local_order_id']].values[0] == 1 and stoploss_modified == 0:
                        # if order is executed
                        if current_order.at[0, 'status'] == 'COMPLETE':
                            # modify stoploss
                            modified_price = strategy_orders['semi-target'][strategy_orders['order_id'] == current_order.at[0, 'local_order_id']].values[0]
                            order_id = kite.modify_order(variety='bo',
                                                         order_id=current_order.at[0, 'order_id'],
                                                         quantity=quantity,
                                                         price=modified_price)
                            # send message to telegram
                            message = ("Stoploss modified to " + str(modified_price) + " for " + name)
                            requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                            # update stoploss status
                            stoploss_modified = 1

                        # if order was not executed
                        elif current_order.at[0, 'status'] == 'OPEN' and current_order.at[1, 'status'] == 'OPEN':
                            transaction_type = 'SELL' if current_order.at[0, 'transaction_type'] == 'BUY' else 'BUY'
                            entry_price = current_order.at[1, 'semi-target']

                            # cancel both pending orders
                            kite.cancel_order(variety='bo',
                                              order_id=current_order.at[0, 'order_id'].values[0])
                            kite.cancel_order(variety='bo',
                                              order_id=current_order.at[1, 'order_id'].values[0])
                            # empty dataframe
                            current_order = current_order[0:0]

                            # place new order
                            order_id = kite.place_order(tradingsymbol=name,
                                                        variety='bo',
                                                        exchange=kite.EXCHANGE_NSE,
                                                        transaction_type=transaction_type,
                                                        quantity=quantity,
                                                        price=entry_price,
                                                        trigger_price=entry_price,
                                                        order_type=kite.ORDER_TYPE_SL,
                                                        product=kite.PRODUCT_MIS,
                                                        stoploss=(day_high - entry_price) if transaction_type == 'SELL' else (entry_price - day_low),
                                                        squareoff=get_target(pivots, entry_price, transaction_type, lot_size))
                            current_order = current_order.append({'order_id': order_id,
                                                                  'local_order_id': local_order+1,
                                                                  'order_type': 'LIMIT',
                                                                  'transaction_type': transaction_type,
                                                                  'parent_order_id': 'NA',
                                                                  'price': entry_price,
                                                                  'status': 'OPEN'}, ignore_index=True)

                            # send message to telegram
                            message = (str(transaction_type) + " order placed for " + name + " at " + str(entry_price))
                            requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)

                            # update stoploss status
                            stoploss_modified = 0
                            local_order = local_order + 1
                previous_strategy_orders = strategy_orders.copy(deep=True)
            time.sleep(1)
        elif datetime.now().hour == 9 and datetime.now().minute >= 59:
            all_orders.to_csv('LiveTrading_Output'+name+'.csv')
            # send message to telegram
            message = ("Live orders file sent to mail")
            requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)
            time.sleep(120)
        else:
            time.sleep(1)



if __name__ == '__main__':
    name = sys.argv[1]
    lot_size = int(sys.argv[2])
    access_token = sys.argv[3]
    start(name, access_token, lot_size)


#######################################################################
# check if order id changes after modifying a stoploss order
# check if kite orders changes every 10 secs even when no update is there
# record order updates for 5 minutes and write it to a csv
# try modifying stoploss order using only parent order id or order id
########################################################################


