activate algotrading
./anaconda3/bin/python ./APT/APT/Paper_Trading/authenticator.py
IFS=","
sed 1d ./APT/APT/Paper_Trading/stock_list_updated.csv | while read -r a b c d;
do ./anaconda3/bin/python ./APT/APT/Paper_Trading/paper_trader.py $a $b $d & ./anaconda3/bin/python ./APT/APT/Paper_Trading/MasterScript_Paper_Pivot.py $a $c &
done
$SHELL
