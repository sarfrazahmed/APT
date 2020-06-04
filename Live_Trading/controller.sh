activate algotrading
./anaconda3/bin/python ./APT/APT/Live_Trading/scrip_scanner.py
IFS=","
sed 1d ./APT/APT/Live_Trading/Selected_Stock_List.csv | while read -r a b c d;
do ./anaconda3/bin/python ./APT/APT/Live_Trading/strategy_redefined.py $a $b $d $c
done
$SHELL
