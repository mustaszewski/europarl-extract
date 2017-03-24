#!/bin/sh
#usage: $./deleteXMLPar.sh infolder
# for example: $ ./extract_tools/deleteXMLPar.sh txt/

infolder=$1
for file in $infolder*/*.txt
do
	sed -i '/<P>/d' $file
	sed -i '/<\/P/d' $file
	sed -i '/<P ALIGN/d' $file
done
echo "\nTags <P> have been successfully removed from all files in folder $infolder\n"
