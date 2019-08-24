import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
## Initial Inputs
###############################################################
folder_path = "/home/ubuntu/APT/APT/Paper_Trading"
file_phrase = "PaperTrading_Output"

files = os.listdir(folder_path)
pt_op_files = [file for file in files if file.startswith(file_phrase)]

os.chdir(folder_path)
summary_df = pd.DataFrame()
for file in pt_op_files:
    stock_name = file[len(file_phrase):(len(file) - 4)]
    trade_data = pd.read_csv(file)
    trade_count = trade_data['Order_Status'][trade_data['Order_Status'] == 'Exit'].count()

    trade_data['Double_Entry_Flag'] = np.where(trade_data['Order_Status'] == 'Exit',
                                               np.where(trade_data['Target'] != 0.0,1,0),0)
    trade_data['Amount'] = np.where(trade_data['Order_Signal'] == 'Buy',
                                    np.where(trade_data['Double_Entry_Flag'] == 1,
                                             (-2) * trade_data['Order_Price'],
                                             (-1) * trade_data['Order_Price']),
                                    np.where(trade_data['Order_Signal'] == 'Sell',
                                             np.where(trade_data['Double_Entry_Flag'] == 1,
                                                      2 * trade_data['Order_Price'],
                                                      trade_data['Order_Price']),0.0))
    profit = trade_data['Amount'].sum()
    summary_df = pd.concat([summary_df,pd.DataFrame(data = [[stock_name,profit]],columns = ['Company','Profit'])])

time_now = str(datetime.now().date())
summary_df.to_csv('PaperTrading_' + time_now,index= False)

