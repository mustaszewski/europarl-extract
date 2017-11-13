#!/bin/sh
# This script performs proeprocessing and cleaning of the source files from the original EuroParl distribution (see http://www.statmt.org/europarl/v7/europarl.tgz)
# Input:	.txt files
# Output:	.txt files in same folder as input folder (processing in-file)
#
# Usage: $ preprocess/cleanSourceFiles.sh infolder
#
# Usage example:
# $ cd europarl
# $ ./preprocess/cleanSourceFiles.sh txt/
#
# Make sure that this script has permission for execution as program:
# $ ls -l europarl_extract/preprocess/cleanSourceFiles.sh
# To set permission for execution, do e.g.:
# $ chmod +x europarl_extract/preprocess/cleanSourceFiles.sh

infolder=$1

echo "\nSTEP 1: Cleaning EuroParl source files in folder $infolder: deleting empty lines and cleaning XML tags\n"
echo "... Please wait, this process will take a while!\n"

for folder in $(find $infolder -mindepth 1 -type d)
do
	printf "\tProcessing folder $folder\t..."
	for file in $(find $folder -type f -name '*.txt')
	do
		sed -i '/^[[:space:]]*$/d' $file # delete empty lines and lines containing only whitespace characters
		sed -i '/^<BRK>$/d' $file # delete lines containing XML markup <BRK>
		sed -i '/^<\/.*>$/d' $file # delete lines containing closing XML tags </xyz>
		sed -i '/^<SpeakerType>/d' $file # delete lines consisting of <SpeakerType> only
		sed -i 's/<P ALIGN=\"JUSTIFY\">/<P>/g' $file # replace <P ALIGN> with <P>
		sed -i 's/LANGUAGE="UK"/LANGUAGE="EN"/g' $file # change language code UK to EN
	done
	printf "\tDONE!\n"
done
echo "\nDONE! Source files in all folders in $infolder cleaned successfully!\n"
