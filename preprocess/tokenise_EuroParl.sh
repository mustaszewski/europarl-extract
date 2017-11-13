#!/bin/bash
# This script calls the sentence segmentation script written by Philipp Koehn and Josh Schroeder as part of the EuroParl distribution (see http://www.statmt.org/europarl/v7/tools.tgz) in order to tokenise the sentences of the EuroParl input files.
# Input:	.txt files
# Output:	.txt files in same folder as input folder
#
# Make sure that this script has permission for execution as program. If not, set permissions by:
# $ chmod +x europarl_extract/preprocess/tokenise_EuroParl.sh
#
# Usage: preprocess/tokenise_EuroParl.sh txt/


infolder=$1

printf "\nSTEP 3: Tokenising EuroParl source files in folder $infolder\n"
printf "\n... Please wait, this process may take a while!\n\n"

for folder in $(find $infolder -mindepth 1 -type d)
do
	printf "\tProcessing folder $folder\t..."
	lang=$(echo $folder | tail -c 3)

	for file in $(find $folder -type f -name '*.txt')
	do
		preprocess/thirdpartytools/tokenizer.perl -q -l $lang < $file > $file.tok
		mv $file.tok $file

	done
	printf "\tDONE!\n"
done
printf "\nDONE! Source files in all subfolders of $infolder tokenised successfully!\n\n"


