#!/bin/sh
#usage: $./deleteemptylines infolder
# for example: $ ./extract_tools/deleteemptylines.sh txt/

infolder=$1
for file in $infolder*/*.txt
do
    sed -i '/^$/d' $file
done
echo "\nEmpty lines have been successfully removed from all files in folder $infolder\n"
