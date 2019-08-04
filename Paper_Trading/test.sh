export IFS=","
cat stocks_info.csv | while read a b c;
do python "D:\APT\APT\Paper_Trading\paper_trader.py" $a $b & python "D:\APT\APT\Paper_Trading\Master_Script_PaperTrading.py" $a &
done
$SHELL