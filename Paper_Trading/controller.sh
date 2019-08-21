python "D:\DevAPT\APT\Paper_Trading\authenticator.py"
IFS=","
cat "D:\DevAPT\APT\Paper_Trading\stock_list_updated.csv" | while read -r a b c d;
do python "D:\DevAPT\APT\Paper_Trading\paper_trader.py" $a $b $d & python "D:\DevAPT\APT\Paper_Trading\MasterScript_Paper_Pivot.py" $a $c &
done
$SHELL
