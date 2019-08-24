activate algotrading
IFS=","
cat ./APT/APT/Simulation/stock_list_updated.csv | while read -r a b c d;
do ./anaconda3/bin/python ./APT/APT/Simulation/candle_generator.py $a $b $d & ./anaconda3/bin/python ./APT/APT/Simulation/MasterScript_Paper_Pivot.py $a $c &
done
