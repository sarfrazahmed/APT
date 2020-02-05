import csv
import time

path = 'D:\\DevAPT\\APT\\Backtesting\\tick_data_2.csv'
for i in range(1, 100):
    fread = open(path, 'r')
    reader = csv.reader(fread)
    for row in reader:
        print(row)
    time.sleep(1)
