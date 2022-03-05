#!/bin/bash

# usage: ./add_frams.sh path/to/*.csv
#
# dataframe headers are DEC, PAIR, COUNT: an instance of a char pair

# combine every csv into a single file, removing the header from each
awk 'FNR > 1' $@ > combined.csv

# take out the index column
cut -d , -f 2-4 combined.csv > to_sum.csv

# add in a new header
sed -i '.bak' '1s/^/DEC,PAIR,COUNT\'$'\n/g' to_sum.csv

# sum all the duplicate entries in COUNT
awk 'BEGIN{FS=OFS=","}
     NR==1{print; next}
          {q=$3;$3="~"; if(!($0 in a)) b[++c]=$0; a[$0]+=q} 
     END  {for(k=1;k<=c;k++) {sub("~",a[b[k]],b[k]); print b[k]}}' to_sum.csv > final_pairs.csv

# remove extra files
rm to_sum.csv to_sum.csv.bak combined.csv
