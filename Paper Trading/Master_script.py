# Import dependencies
import pandas as pd
import datetime
import time

## Initial Inputs
###############################################################
lot_size = 500
# max_one_stock_price = 1300
target_profit_1 = 3500
semi_target = 2000
max_stop_loss = 500

order_status = 'Exit'
order_signal = ''
order_price = 0.0
entry_high_target = 0.0
entry_low_target = 10000.0
stop_loss = 0.0
target = 0.0
skip_date = datetime.strptime('2019-01-01','%Y-%m-%d')



# Get data after every 5 mins
if (datetime.datetime.now().minute % 5 == 0) and (datetime.datetime.now().second == 1):
    data = pd.read_csv('ohlc_data.csv')
    data.columns = ['Date','Open','High','Low','Close']
    
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
    data['Hour'] = [j.hour for j in data['Date']]
    data['Minute'] = [j.minute for j in data['Date']]
    print('Data Preparation Completed')


