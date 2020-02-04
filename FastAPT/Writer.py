import csv
import shutil
import time

mypath = 'D:\\DevAPT\\APT\\Backtesting\\tick_data_1.csv'
for i in range(1, 100):
    fwrite = open(mypath, 'w')
    writer = csv.writer(fwrite)
    writer.writerow(str(i))
    fwrite.close()
    print(str(i) + ' written')
    shutil.copy(mypath, mypath.replace('_1', '_2'))
    time.sleep(1)
