#!/bin/bash
# This script calls a customised version of ixa-pipe-tok, the sentence splitter and tokeniser of the ixa-pipes written by Rodrigo Agerri (see https://github.com/ixa-ehu/ixa-pipe-tok) in order to split and tokenise the sentences of the EuroParl input files.
# Input: .txt files
# Output: .txt files in same folder as input folder
#
# Make sure that this script has permission for execution as program. If not, set permissions by:
# $ chmod +x europarl_extract/preprocess/segment-tokenise_ixaPipes.sh
#
# Usage: preprocess/segment-tokenise_ixaPipes.sh txt/

infolder=$1


printf "\nSTEP 3: Segmenting and tokenising sentences in EuroParl source files in folder $infolder\n"
printf "\n... Please wait, this process will take a while!\n\n"


for folder in $(find $infolder -mindepth 1 -type d)
do
	printf "\tProcessing folder $folder\t..."
	lang=$(echo $folder | tail -c 3)

	for file in $(find $folder -type f -name '*.txt')
	do
		#lang=$(echo $file | grep -o '/[[:lower:]]\{2\}/' | head -c 3 | tail -c 2)
		cat $file | java -jar preprocess/thirdpartytools/ixa-pipe-tok-1.8.4.jar tok -l $lang -o oneline --segmentOnLinebreak single --verbose no --tokeniseXML no > $file.tok
		mv $file.tok $file
	done
	printf "\tDONE!\n"

done
printf "\nDONE! Source files in all subfolders of $infolder segmented and tokenised successfully!\n\n"
