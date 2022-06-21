#!/bin/bash

head_len=19

uci_lines=$((`cat $1 | wc -l` - $head_len))

tmp_sec=`date +%s`
tmp_file="$tmp_sec.uci"
head -n $head_len $2 > $tmp_file
tail -n $uci_lines $1 >> $tmp_file
mv $tmp_file $2
