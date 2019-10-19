kill -9 $(ps ax | grep google | fgrep -v grep | awk '{ print $1 }')
kill -9 $(ps ax | grep chrome | fgrep -v grep | awk '{ print $1 }')
kill -9 $(ps ax | grep python | fgrep -v grep | awk '{ print $1 }')
