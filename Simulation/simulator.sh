activate algotrading
./anaconda3/bin/python ./APT/APT/Simulation/authenticator.py
IFS=","
cat ./APT/APT/Simulation/stock_list_updated.csv | while read -r a b c d e;
do ./anaconda3/bin/python ./APT/APT/Simulation/candle_generator.py $a $e $d & ./anaconda3/bin/python ./APT/APT/Simulation/MasterScript_Paper_Pivot.py $a $c &
done
