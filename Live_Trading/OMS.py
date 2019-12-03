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
        target = round(round(min_pos_delta + order_price + (order_price * target_buffer_multiplier), 1) - order_price, 1)
    else:
        deltas = [round(indicator, 1) - order_price for indicator in pivots]
        neg_deltas = [delta for delta in deltas if delta < -(order_price * 0.005)]
        max_neg_delta = max(neg_deltas) if len(neg_deltas) != 0 else -(min_target / lot_size)
        target = round(order_price - round(order_price + max_neg_delta - (order_price * target_buffer_multiplier), 1), 1)
    return target


def start(name, access_token, lot_size):
    logging.basicConfig(filename=name+"_OMS.log",
                        format='%(asctime)s %(message)s',
                        filemode='w')
    # Creating an object
    logger = logging.getLogger()

    # Setting the threshold of logger to DEBUG
    logger.setLevel(logging.DEBUG)

    # Authenticate
    time.sleep(140)
    logger.debug("OMS started")
    path = '/home/ubuntu/APT/APT/Live_Trading'
    os.chdir(path)
    config = configparser.ConfigParser()
    config_path = path + '/config.ini'
    config.read(config_path)
    api_key = config['API']['API_KEY']

    # Connect to kite
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    logger.debug("OMS Authenticated")

    # Bot API Link
    bot_link = "https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text="

    # Initialise variables
    first_order = 1
    stoploss_modified = 0
    local_order = 0

    day_high = 0
    day_low = 0
    if lot_size < 100:
        quantity = 1
    else:
        quantity = round(lot_size/100)

    # Read previous day data file
    data = pd.read_csv(path + '/previous_day_data_' + name + '.csv')
    pivots = pivotpoints(data)

    # Local orders dataframes
    previous_strategy_orders = pd.DataFrame()

    # Create current order tracker dataframe
    current_order_parameters = ['order_id',
                                'order_type',
                                'transaction_type',
                                'parent_order_id',
                                'price',
                                'trigger_price',
                                'status']
    current_order = pd.DataFrame(columns=['order_id',
                                          'local_order_id',
                                          'order_type',
                                          'transaction_type',
                                          'parent_order_id',
                                          'price',
                                          'trigger_price',
                                          'status'])
    all_orders = pd.DataFrame(columns=['order_id',
                                       'local_order_id',
                                       'order_type',
                                       'transaction_type',
                                       'parent_order_id',
                                       'price',
                                       'trigger_price',
                                       'status'])

    # Get order update from KITE
    previous_kite_orders = pd.DataFrame(kite.orders())
    kite_orders = pd.DataFrame(kite.orders())
    print("Order Management Started")
    message = ("Order Management script started for: " + str(name))
    requests.get(bot_link + message)

    # Start infinite loop
    while True:
        if datetime.now().second % 10 == 0:

            # Check if first order is placed
            if first_order == 0:
                try:
                    kite_orders = pd.DataFrame(kite.orders())
                except:
                    logger.debug("Too many requests error from server")
                    pass
                current_order = current_order.reset_index(drop=True)

                # Proceed if any new updates are there
                if not kite_orders.equals(previous_kite_orders):
                    if len(current_order) == 1:
                        # check if status of order is complete
                        if kite_orders['status'][kite_orders['order_id'] == current_order.at[0, 'order_id']].values[0] == 'COMPLETE':
                            logger.debug("Order executed case block entered")
                            # change current order status
                            current_order = current_order.reset_index(drop=True)
                            current_order.at[0, 'status'] = 'COMPLETE'

                            # append stoploss and target orders
                            current_order = current_order.append(kite_orders.loc[kite_orders['parent_order_id'] == current_order.at[0, 'order_id'], current_order_parameters])
                            current_order = current_order.reset_index(drop=True)

                            # append all orders to save
                            all_orders = all_orders.append(current_order)
                            all_orders.to_csv('LiveTrading_Output' + name + '.csv')
                            logger.debug("Order file saved")

                            # send message to telegram
                            message = (str(current_order.at[0, 'transaction_type'])+" order executed for "
                                       + name + " at " + str(current_order.at[0, 'price']))
                            requests.get(bot_link + message)
                            logger.debug("Order executed status case handled successfully")

                    # if stoploss hits
                    if len(current_order) > 1:
                        if kite_orders['status'][kite_orders['order_id'] == current_order['order_id'][(current_order['trigger_price'] != 0) & (current_order['transaction_type'] != current_order.at[0, 'transaction_type'])].values[0]].values[0] == 'COMPLETE':

                            logger.debug("Stoploss hit case block entered")

                            # order transaction type
                            transaction_type = 'SELL' if current_order.at[0, 'transaction_type'] == 'BUY' else 'BUY'

                            # entry price
                            entry_price = current_order['trigger_price'][current_order['trigger_price'] != 0].values[0]

                            # stoploss
                            stoploss_price = day_high if transaction_type == 'SELL' else day_low
                            stoploss = round((day_high - entry_price) if transaction_type == 'SELL'
                                             else (entry_price - day_low), 1)

                            # target
                            target = get_target(pivots, entry_price, transaction_type, lot_size)
                            target_price = round((target + entry_price) if transaction_type == 'BUY'
                                                 else (entry_price - target), 1)

                            # update local order id
                            local_order = local_order + 1

                            # clear previous orders
                            current_order = current_order[0:0]

                            # place first order at current market price
                            order_id = kite.place_order(tradingsymbol=name,
                                                        variety='bo',
                                                        exchange=kite.EXCHANGE_NSE,
                                                        transaction_type=transaction_type,
                                                        quantity=quantity,
                                                        price=entry_price,
                                                        order_type=kite.ORDER_TYPE_LIMIT,
                                                        product=kite.PRODUCT_MIS,
                                                        stoploss=stoploss,
                                                        squareoff=target)
                            current_order = current_order.append({'order_id': order_id,
                                                                  'local_order_id': local_order,
                                                                  'order_type': 'LIMIT',
                                                                  'transaction_type': transaction_type,
                                                                  'parent_order_id': 'NA',
                                                                  'price': entry_price,
                                                                  'trigger_price': 0,
                                                                  'status': 'OPEN'}, ignore_index=True)

                            # send message to telegram
                            message = ("STOPLOSS HIT: " + transaction_type + " order placed for " + str(quantity) + " stocks of " + name + " at " + str(entry_price) + " with stoploss at " + str(stoploss_price) + " and target at " + str(target_price))
                            requests.get(bot_link + message)

                            # update stoploss status
                            stoploss_modified = 0
                            logger.debug("Stoploss hit case handled")

                    # if target hits
                    if len(current_order) > 1:
                        if kite_orders['status'][kite_orders['order_id'] == current_order['order_id'][(current_order['trigger_price'] == 0) & (current_order['transaction_type'] != current_order.at[0, 'transaction_type'])].values[0]].values[0] == 'COMPLETE':

                            logger.debug("Target hit case block entered")

                            # order transaction type
                            transaction_type = 'SELL' if current_order.at[0, 'transaction_type'] == 'BUY' else 'BUY'

                            # entry price
                            entry_price = day_low if transaction_type == 'SELL' else day_high

                            # stoploss
                            stoploss_price = day_high if transaction_type == 'SELL' else day_low
                            stoploss = round((day_high - entry_price) if transaction_type == 'SELL'
                                             else (entry_price - day_low), 1)

                            # target
                            target = get_target(pivots, entry_price, transaction_type, lot_size)
                            target_price = round((target + entry_price) if transaction_type == 'BUY'
                                                 else (entry_price - target), 1)

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
                                                        stoploss=stoploss,
                                                        squareoff=target)
                            current_order = current_order.append({'order_id': order_id,
                                                                  'local_order_id': local_order,
                                                                  'order_type': 'LIMIT',
                                                                  'transaction_type': transaction_type,
                                                                  'parent_order_id': 'NA',
                                                                  'price': entry_price,
                                                                  'trigger_price': 0,
                                                                  'status': 'OPEN'}, ignore_index=True)

                            # send message to telegram
                            message = ("TARGET HIT: " + transaction_type + " order placed for " + str(quantity)
                                       + " stocks of " + name + " at " + str(entry_price) + " with stoploss at "
                                       + str(stoploss_price) + " and target at " + str(target_price))
                            requests.get(bot_link + message)

                            # update stoploss status
                            stoploss_modified = 0
                            logger.debug("Target hit case handled")

                    # copy current orders to previous orders
                    previous_kite_orders = kite_orders.copy(deep=True)
                    time.sleep(1)

                else:
                    time.sleep(1)
            else:
                time.sleep(1)

        elif datetime.now().minute % 5 == 0 and (datetime.now().second >= 7 and datetime.now().second <= 12):
            if os.path.isfile('live_order_' + name + '_' + str(datetime.now().date()) + '.csv'):
                strategy_orders = pd.read_csv('live_order_' + name + '_' + str(datetime.now().date()) + '.csv')
                strategy_orders = strategy_orders.reset_index(drop=True)
                kite_orders.to_csv('kite_orders_' + name + '_' + str(datetime.now().date()) + '.csv')
                current_order.to_csv('current_order_' + name + '_' + str(datetime.now().date()) + '.csv')

                # if orders present in strategy orders file
                if not strategy_orders.equals(previous_strategy_orders):

                    # first order of the day
                    if first_order == 1:

                        logger.debug("First order block entered")

                        # get order details
                        local_order = strategy_orders.at[0, 'order_id']
                        transaction_type = strategy_orders.at[0, 'transaction_type']
                        entry_price = strategy_orders.at[0, 'price']
                        stoploss_price = strategy_orders.at[0, 'stoploss']
                        target_price = strategy_orders.at[0, 'target']

                        stoploss = round((stoploss_price - entry_price) if transaction_type == 'SELL'
                                         else (entry_price - stoploss_price), 1)
                        target = round((entry_price - target_price) if transaction_type == 'SELL'
                                       else (target_price - entry_price), 1)

                        # place first order at current market price
                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=transaction_type,
                                                    quantity=quantity,
                                                    price=entry_price,
                                                    order_type=kite.ORDER_TYPE_LIMIT,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=stoploss,
                                                    squareoff=target)
                        current_order = current_order.append({'order_id': order_id,
                                                              'local_order_id': local_order,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': transaction_type,
                                                              'parent_order_id': 'NA',
                                                              'price': entry_price,
                                                              'trigger_price': 0,
                                                              'status': 'OPEN'}, ignore_index=True)

                        # send message to telegram
                        message = (transaction_type + " order placed for " + str(quantity) + " stocks of "
                                   + name + " at " + str(entry_price) + " with stoploss at "
                                   + str(stoploss_price) + " and target at " + str(target_price))
                        requests.get(bot_link + message)

                        first_order = 0
                        logger.debug("First order placed for "+name)
                        time.sleep(6)

                    # update day high and day low
                    day_high = strategy_orders.loc[(strategy_orders['order_id'] == current_order.at[0, 'local_order_id']), 'day_high'].values[0]
                    day_low = strategy_orders.loc[(strategy_orders['order_id'] == current_order.at[0, 'local_order_id']), 'day_low'].values[0]
                    message = (name + "\nDay high: " + str(day_high) + "\nDay low: " + str(day_low))
                    requests.get(bot_link + message)

                    # modify stoploss if semi-target is hit
                    if strategy_orders['semi-target_status'][strategy_orders['order_id'] == current_order.at[0, 'local_order_id']].values[0] == 1 \
                            and stoploss_modified == 0:

                        # if order is executed
                        if current_order.at[0, 'status'] == 'COMPLETE' and len(current_order) <= 3:

                            logger.debug("Semi-target modification in executed order block entered")

                            # fetch semi-target price
                            modified_price = strategy_orders.loc[(strategy_orders['order_id'] == current_order.at[0, 'local_order_id']), 'semi_target'].values[0]

                            try:
                                order_id = kite.modify_order(variety='bo',
                                                             parent_order_id=current_order.at[0, 'order_id'],
                                                             order_id=current_order['order_id'][current_order['trigger_price'] != 0].values[0],
                                                             order_type=kite.ORDER_TYPE_SL,
                                                             trigger_price=modified_price)
                            except Exception:
                                message = ("Stoploss cannot be modified to " + str(modified_price) + " for " + name + " , trying again...")
                                requests.get(bot_link + message)
                                time.sleep(2)
                                order_id = kite.modify_order(variety='bo',
                                                             parent_order_id=current_order.at[0, 'order_id'],
                                                             order_id=current_order['order_id'][current_order['trigger_price'] != 0].values[0],
                                                             order_type=kite.ORDER_TYPE_SL,
                                                             trigger_price=modified_price)
                                pass


                            # Replace the stoploss with the semi-target price
                            current_order['trigger_price'][current_order['trigger_price'] != 0] = modified_price

                            # send message to telegram
                            message = ("Stoploss modified to " + str(modified_price) + " for " + name)
                            requests.get(bot_link + message)

                            # update stoploss status
                            stoploss_modified = 1
                            logger.debug("Semi-target modification in executed order case handled")

                        # if order is executed in partial chunks
                        elif current_order.at[0, 'status'] == 'COMPLETE' and len(current_order) > 3:

                            logger.debug("Semi-target modification in partially filled orders block entered")

                            # get all order ids' list of stoploss orders
                            order_list = current_order['order_id'][current_order['trigger_price'] != 0].tolist()

                            # fetch semi-target price
                            modified_price = strategy_orders.loc[(strategy_orders['order_id'] == current_order.at[0, 'local_order_id']), 'semi_target'].values[0]

                            # iterate over all order ids
                            for order_id in order_list:
                                order_id = kite.modify_order(variety='bo',
                                                             parent_order_id=current_order.at[0, 'order_id'],
                                                             order_id=order_id,
                                                             order_type=kite.ORDER_TYPE_SL,
                                                             trigger_price=modified_price)
                                time.sleep(2)

                            # Replace the stoploss with the semi-target price
                            current_order['trigger_price'][current_order['trigger_price'] != 0] = modified_price

                            # send message to telegram
                            message = ("Stoploss modified to " + str(modified_price) + " for " + name)
                            requests.get(bot_link + message)

                            # update stoploss status
                            stoploss_modified = 1
                            logger.debug("Semi-target modification in executed order case handled")


                        # if order was not executed
                        elif current_order.at[0, 'status'] == 'OPEN':

                            logger.debug("Semi-target modification in open order block entered")

                            # cancel last placed order
                            kite.cancel_order(variety='bo',
                                              order_id=current_order.at[0, 'order_id'].values[0])

                            # transaction type
                            transaction_type = 'SELL' if current_order.at[0, 'transaction_type'] == 'BUY' else 'BUY'

                            # entry price
                            entry_price = strategy_orders.loc[(strategy_orders['order_id'] == current_order.at[0, 'local_order_id']), 'semi_target'].values[0]

                            # stoploss
                            stoploss_price = day_high if transaction_type == 'SELL' else day_low
                            stoploss = round((day_high - entry_price) if transaction_type == 'SELL'
                                             else (entry_price - day_low), 1)

                            # target
                            target = get_target(pivots, entry_price, transaction_type, lot_size)
                            target_price = round((target + entry_price) if transaction_type == 'BUY'
                                                 else (entry_price - target), 1)

                            # empty dataframe
                            current_order = current_order[0:0]

                            # update local order id
                            local_order = local_order + 1

                            # place new order
                            order_id = kite.place_order(tradingsymbol=name,
                                                        variety='bo',
                                                        exchange=kite.EXCHANGE_NSE,
                                                        transaction_type=transaction_type,
                                                        quantity=quantity,
                                                        price=entry_price,
                                                        order_type=kite.ORDER_TYPE_LIMIT,
                                                        product=kite.PRODUCT_MIS,
                                                        stoploss=stoploss,
                                                        squareoff=target)
                            current_order = current_order.append({'order_id': order_id,
                                                                  'local_order_id': local_order,
                                                                  'order_type': 'LIMIT',
                                                                  'transaction_type': transaction_type,
                                                                  'parent_order_id': 'NA',
                                                                  'price': entry_price,
                                                                  'trigger_price': 0,
                                                                  'status': 'OPEN'}, ignore_index=True)

                            # send message to telegram
                            message = (transaction_type + " order placed for " + str(quantity) + " stocks of "
                                       + name + " at " + str(entry_price) + " with stoploss at "
                                       + str(stoploss_price) + " and target at " + str(target_price))
                            requests.get(bot_link + message)

                            # update stoploss status
                            stoploss_modified = 0
                            logger.debug("Semi-target modification in open order case handled")

                    # if target is hit while order is open
                    if strategy_orders['target_status'][strategy_orders['order_id'] == current_order.at[0, 'local_order_id']].values[0] == 1 and \
                            current_order.at[0, 'status'] == 'OPEN':

                        logger.debug("Target hit in open order case enetered")

                        # cancel last placed order
                        kite.cancel_order(variety='bo',
                                          order_id=current_order.at[0, 'order_id'].values[0])

                        # order transaction type
                        transaction_type = 'SELL' if current_order.at[0, 'transaction_type'] == 'BUY' else 'BUY'

                        # entry price
                        entry_price = day_low if transaction_type == 'SELL' else day_high

                        # stoploss
                        stoploss_price = day_high if transaction_type == 'SELL' else day_low
                        stoploss = round(
                            (day_high - entry_price) if transaction_type == 'SELL' else (entry_price - day_low), 1)

                        # target
                        target = get_target(pivots, entry_price, transaction_type, lot_size)
                        target_price = round(
                            (target + entry_price) if transaction_type == 'BUY' else (entry_price - target), 1)

                        # update local order id
                        local_order = local_order + 1

                        # clear previous orders
                        current_order = current_order[0:0]

                        # place new order at day's high/low
                        order_id = kite.place_order(tradingsymbol=name,
                                                    variety='bo',
                                                    exchange=kite.EXCHANGE_NSE,
                                                    transaction_type=transaction_type,
                                                    quantity=quantity,
                                                    price=entry_price,
                                                    trigger_price=entry_price,
                                                    order_type=kite.ORDER_TYPE_SL,
                                                    product=kite.PRODUCT_MIS,
                                                    stoploss=stoploss,
                                                    squareoff=target)
                        current_order = current_order.append({'order_id': order_id,
                                                              'local_order_id': local_order,
                                                              'order_type': 'LIMIT',
                                                              'transaction_type': transaction_type,
                                                              'parent_order_id': 'NA',
                                                              'price': entry_price,
                                                              'trigger_price': 0,
                                                              'status': 'OPEN'}, ignore_index=True)

                        # send message to telegram
                        message = ("TARGET HIT IN OPEN ORDER: " + transaction_type + " order placed for " + str(
                            quantity) + " stocks of " + name + " at " + str(entry_price) + " with stoploss at " + str(
                            stoploss_price) + " and target at " + str(target_price))
                        requests.get(bot_link + message)

                        # update stoploss status
                        stoploss_modified = 0
                        logger.debug("Target hit in open order case handled")

                previous_strategy_orders = strategy_orders.copy(deep=True)
                time.sleep(6)

        elif datetime.now().hour == 9 and datetime.now().minute >= 50:
            all_orders.to_csv('LiveTrading_Output'+name+'.csv')
            logger.debug("Order file saved")

            # send message to telegram
            message = ("Live orders file sent to mail")
            requests.get(bot_link + message)
            time.sleep(600)

        else:
            time.sleep(1)



if __name__ == '__main__':
    name = sys.argv[1]
    lot_size = int(sys.argv[2])
    access_token = sys.argv[3]
    start(name, access_token, lot_size)