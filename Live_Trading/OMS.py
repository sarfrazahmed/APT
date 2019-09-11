# Import dependencies
import pandas as pd
from kiteconnect import KiteConnect
import configparser
import os
import time
import sys
from datetime import datetime, timedelta


def start(name, access_token):
    # Authenticate
    config = configparser.ConfigParser()
    path = os.getcwd()
    print(path)
    config_path = path + '\\config.ini'
    config.read(config_path)
    api_key = config['API']['API_KEY']

    # Connect to kite
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

    # Initialise variables
    order_punched = 1
    first_order = 1
    stoploss_modified = 0
    day_high = 0
    day_low = 0
    quantity = 1

    # Create temp dataframes
    current_order = pd.DataFrame(columns=['order_id', 'order_type', 'parent_order_id', 'price', 'status'])

    # Get order update from KITE
    previous_kite_orders = pd.DataFrame(kite.orders())

    # Start looping
    while True:
        if datetime.now().second % 10 == 0:
            kite_orders = pd.DataFrame(kite.orders())

            # Proceed if any new updates are there
            if not kite_orders.equals(previous_kite_orders):

                if first_order == 1:
                    # cancel secondary order on execution of primary order and vice-versa
                    if kite_orders['status'][kite_orders['order_id'] == current_order.at[0, 'order_id']].values[0] == 'COMPLETE':
                        kite.cancel_order(variety='bo',
                                          order_id=current_order.at[1, 'order_id'].values[0])
                        # get specific columns in current order dataframe
                        current_order = kite_orders[['order_id', 'order_type', 'parent_order_id', 'price', 'status']]

                        # drop cancelled order row
                        current_order = current_order[current_order['status'] != 'CANCELLED']
                        first_order = 0

                    elif kite_orders['status'][kite_orders['order_id'] == current_order.at[1, 'order_id']].values[0] == 'COMPLETE':
                        kite.cancel_order(variety='bo',
                                          order_id=current_order.at[0, 'order_id'].values[0])
                        # get specific columns in current order dataframe
                        current_order = kite_orders[['order_id', 'order_type', 'parent_order_id', 'price', 'status']]

                        # drop cancelled order row
                        current_order = current_order[current_order['status'] != 'CANCELLED']
                        first_order = 0





        elif datetime.now().minute % 5 == 0:
            strategy_orders = pd.read_csv('filename' + name +'.csv')

            # if orders present in strategy orders file
            if len(strategy_orders) > 0:

                # first order of the day
                if order_punched == 1:
                    # place first order at current market price
                    order_id = kite.place_order(tradingsymbol=name,
                                                variety='bo',
                                                exchange=kite.EXCHANGE_NSE,
                                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                quantity=quantity,
                                                price='price',
                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                product=kite.PRODUCT_MIS,
                                                stoploss='stoploss',
                                                squareoff='target')
                    current_order = current_order.append({'order_id': order_id,
                                                          'order_type': 'LIMIT',
                                                          'parent_order_id': 'NA',
                                                          'price': strategy_orders.at[0, 'price'],
                                                          'status': 'OPEN'}, ignore_index=True)

                    # place second order at stoploss
                    order_id = kite.place_order(tradingsymbol=name,
                                                variety='bo',
                                                exchange=kite.EXCHANGE_NSE,
                                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                                quantity=quantity,
                                                price='price',
                                                order_type=kite.ORDER_TYPE_LIMIT,
                                                product=kite.PRODUCT_MIS,
                                                stoploss='stoploss',
                                                squareoff='target')
                    current_order = current_order.append({'order_id': order_id,
                                                          'order_type': 'LIMIT',
                                                          'parent_order_id': 'NA',
                                                          'price': strategy_orders.at[1, 'price'],
                                                          'status': 'OPEN'}, ignore_index=True)
                    order_punched = 0


                # update day high and day low
                day_high = strategy_orders.at[len(strategy_orders)-1, 'day_high']
                day_low = strategy_orders.at[len(strategy_orders)-1, 'day_low']

                # modify stoploss if semi-target is hit
                if strategy_orders['semi-target_status'][strategy_orders['order_id'] == current_order.at[0, 'order_id']].values[0] == 1 and stoploss_modified == 0:
                    order_id = kite.modify_order(variety='bo',
                                                 order_id=current_order.at[0, 'order_id'],
                                                 quantity=quantity,
                                                 price=strategy_orders['semi-target_status'][strategy_orders['order_id'] == current_order.at[0, 'semi-target']].values[0])
                    stoploss_modified = 1



if __name__ == '__main__':
    name = sys.argv[1]
    access_token = sys.argv[3]
    start(name, access_token)



# check if order id changes after modifying a stoploss order
# check if kite orders changes every 10 secs even when no update is there
# record order updates for 5 minutes and write it to a csv
# try modifying stoploss order using only parent order id or order id

