activate algotrading
./anaconda3/bin/python ./APT/APT/Paper_Trading/authenticator.py
IFS=","
<<<<<<< HEAD
cat ./APT/APT/Paper_Trading/stock_list_updated.csv | while read -r a b c d;
do ./anaconda3/bin/python ./APT/APT/Paper_Trading/paper_trader.py $a $b $d & ./anaconda3/bin/python ./APT/APT/Paper_Trading/MasterScript_Paper_Pivot.py $a $c &
=======
cat "D:\DevAPT\APT\Paper_Trading\stock_list_updated.csv" | while read -r a b c d;
do python "D:\DevAPT\APT\Paper_Trading\paper_trader.py" $a $b $d & python "D:\DevAPT\APT\Paper_Trading\MasterScript_Paper_Pivot.py" $a $c &
>>>>>>> f4f3904002ab1ca4b95bdbc27db428881fc1c712
done
$SHELL
