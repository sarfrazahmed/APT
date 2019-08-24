#mkdir ./AGDir
activate algotrading
#conda activate algotrading
IFS=","
cat ./APT/APT/Paper_Trading/stock_list_updated.csv | while read -r a b c d;
do ./anaconda3/bin/python ./APT/APT/Simulation/candle_generator.py $a & ./anaconda3/bin/python ./APT/APT/Simluation/MasterScript_Paper_Pivot.py $a $c &
done
