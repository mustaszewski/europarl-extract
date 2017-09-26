#!/bin/sh
#usage: $./deleteemptylines infolder
# for example: $ ./extract_tools/deleteemptylines.sh txt/

infolder=$1

echo "\nSTEP 1: Deleting empty lines from source files in folder $infolder\n"
echo "... Please wait, this process may take around 30 minutes!\n"

for file in $infolder*/*.txt
do
    sed -i '/^$/d' $file
done
echo "  DONE! Empty lines have been successfully removed from all files in folder $infolder\n"
