# Import dependencies
import pandas as pd
import os
from Paper_Trading import paper_trader
from Paper_Trading import Master_Script_PaperTrading
from subprocess import *
import time
import threading

path = os.getcwd()
os.chdir(path)

# Get metadata
metadata = pd.read_csv('nifty50_stocks_token.csv')
timeframe = '5min'
# for index, row in metadata.iterrows():
#     Popen(Master_Script_PaperTrading.start(row['Company']))
#     time.sleep(1)
#     Popen(paper_trader.start(row['Company'], row['Token'], timeframe))
#     print('Script invoked for ', row['Company'])
#     break

for index, row in metadata.iterrows():
    t1 = threading.Thread(target=Master_Script_PaperTrading.start(row['Company']))
    t2 = threading.Thread(target=paper_trader.start(row['Company'], row['Token'], timeframe))
    t1.start() | t2.start()
    print('Script invoked for ', row['Company'])
    break