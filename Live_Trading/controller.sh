activate algotrading
./anaconda3/bin/python ./APT/APT/Live_Trading/authenticator.py
IFS=","
sed 1d ./APT/APT/Live_Trading/stock_list_updated.csv | while read -r a b c d;
do ./anaconda3/bin/python ./APT/APT/Live_Trading/paper_trader.py $a $b $d & ./anaconda3/bin/python ./APT/APT/Live_Trading/MasterScript_Paper_Pivot.py $a $c & ./anaconda3/bin/python ./APT/APT/Live_Trading/OMS.py $a $d
done
$SHELL
