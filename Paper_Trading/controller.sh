export IFS=","
cat stocks_info.csv | while read a b c d;
do python "/home/ubuntu/APT/APT/Paper_Trading/paper_trader.py" $a $b $c $d & python "/home/ubuntu/APT/APT/Paper_Trading/MasterScript_Paper_Pivot.py" $a $b $c $d &
done
$SHELL
