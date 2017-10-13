#!/bin/sh
# Usage: $ cleanSourceFiles.sh infolder
# Usage example:
# $ cd europarl
# $ ./europarl_extract/cleanSourceFiles.sh txt/
#
# Make sure that the script has permission for execution as program:
# $ ls -l europarl_extract/cleanSourceFiles.sh
# To set permission for execution, do e.g.:
# $ chmod +x europarl_extract/cleanSourceFiles.sh

infolder=$1

echo "\nSTEP 1: Cleaning EuroParl source files in folder $infolder: deleting empty lines and cleaning XML tags\n"
echo "... Please wait, this process may take a while!\n"

for folder in $(find $infolder -mindepth 1 -type d)
do
	printf "\tProcessing folder $folder\t..."
	for file in $(find $folder -type f -name '*.txt')
	do
		sed -i '/^$/d' $file
		sed -i '/^<BRK>$/d' $file
		sed -i '/^<\/.*>$/d' $file
		sed -i '/^<SpeakerType>/d' $file
		sed -i 's/<P ALIGN=\"JUSTIFY\">/<P>/g' $file
		sed -i 's/LANGUAGE="UK"/LANGUAGE="EN"/g' $file
	done
	printf "\tDONE!\n"
done
echo "\nDONE! Source files in all folders in $infolder cleaned successfully!\n"
