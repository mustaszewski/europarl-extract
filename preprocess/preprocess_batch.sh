#!/bin/sh
# This script performs all steps of source file preprocessing sequentially without the need to execute each step individually.
# Input:	.txt files
# Output:	.txt files in same folder as input folder (processing in-file)
#
# Usage: $ preprocess/preprocess_batch.sh <input_folder>
#
# Usage example:
# $ cd europarl-extract
# $ ./reprocess/preprocess_batch.sh txt/
#
# Make sure that this script has permission for execution as program:
# $ ls -l europarl_extract/preprocess/preprocess_batch.sh
# To set permission for execution, do e.g.:
# $ chmod +x preprocess/preprocess_batch.sh

infolder=$1

./preprocess/cleanSourceFiles.sh $infolder
python3 disambiguate_speaker_IDs.py $infolder
./preprocess/segment_EuroParl.sh $infolder


