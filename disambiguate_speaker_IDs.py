'''
This script pre-processes EuroParl files, which is a necessary step
for the extraction of directional multilingual parallel corpora.

The script disambiguates speaker IDs to avoid that two or more speech segments are assigned the same ID

Usage:

$ python3 europarl_extract/disambiguate_speaker_IDs.py txt/

'''

import fileinput
import re
import argparse
import os
import sys
import codecs
  
def get_sourcefile(path):
  if path.endswith('.txt'):
    file_list.append(path)
  else:
    print("Specified input file must have extension .txt")
    exit(1)
  ### end of function get_sourcefile()

def get_sourcefiles_from_folder(path):
  for root, dirs, files in os.walk(path):
    for filename in files:
      if filename.endswith('.txt'):
        file_list.append(os.path.join(root, filename))
        
  if len(file_list) == 0:
    print ("\nNo files with extension .txt were found in folder %s\n\n" %(path))
    exit(1)
  ### end of function get_sourcefiles_from_folder()

#
def disambiguate_speaker_IDs(inputfile):
  usedIDs = {}
  for line in fileinput.input(inputfile ,inplace=1):
    line = line.strip()
    speakerID_match = speakerID_pattern.search(line)
    if speakerID_match:
      original_ID = speakerID_match.group(1)
      if original_ID in usedIDs:
        runningNumber = usedIDs[original_ID]
        new_ID = original_ID + "_" + "{0:03}".format(runningNumber)
        runningNumber += 1
        usedIDs[original_ID] = runningNumber
        print(line.replace(original_ID, new_ID))
      else:
        usedIDs[original_ID] = 1
        print(line)
    else:
      print(line)
  fileinput.close()

# Function to get rid of non-utf-coded characters in file ep-09-10-22-009.txt
def clean_corrupt_file():
  corrupt_fn = re.compile(".+pl/ep-09-10-22-009.txt")
  problematic_files = list(filter(corrupt_fn.match, file_list))
  if len(problematic_files) > 0:
    for src in problematic_files:
      tmp = problematic_file_temp = src + ".clean"
      with codecs.open(src, 'r', encoding='utf-8', errors='ignore') as sourceFile:
        with codecs.open(tmp, "w", "utf-8") as tmpFile:
          while True:
            contents = sourceFile.read()
            if not contents:
              break
            tmpFile.write(contents)
      os.remove(src)
      os.rename(tmp, src)
  ### End of function clean_corrupt_file()


######### END OF FUNCTION DEFINITIONS #########

langcode = re.compile (r"\((BG|CS|DA|DE|EL|EN|ES|ET|FI|FR|GA\
                        |HU|IT|LT|LV|MT|NL|PL|PT|RO|SK|SV|SL)\)")
speaker_tag = re.compile(r'SPEAKER ID=')
speakerID_pattern = re.compile(r'<SPEAKER ID="?(\d+)"?')

exception1 = re.compile(r'(\(ES\) ?(č\.|č|št|št\.|Nr\.)? ?\d{2,})')
#exception_sl = re.compile(r'(\(ES\) ?(št\.|št)? ?\d{2,})') #(ES) št. 5
#exception1 = re.compile(r'(\(ES\) \d{2,})')

# TO DO: die muster nach (ES) bei exception1 müssen als (NOT THESE) folgen auf die sprachcodes con langcode

### Parse input arguments
parser = argparse.ArgumentParser(description="Preprocessing of EuroParl corpus files")
parser.add_argument("path", help="Path to file to be processed or directory containing files to be processed")
parser.add_argument("-l", "--log", action= "store_true",
                    help="Create a log file to track unprocessed files (if applicable)")
#parser.add_argument("-d", "--disambiguateIDs", action="store_true", help="Disambiguate speaker IDs if one ID is assigned to multiple speech segments")
parser.add_argument("-f", "--file", action="store_true", help="Process a single file rather than all files in a directory")
args = parser.parse_args()
path = args.path

### Get input file(s) from arguments 
file_list = []
if args.file:
  get_sourcefile(path)
else:
  get_sourcefiles_from_folder(path)


### Main Program

# BUGFIX:
# Call clean_corrupt_file() to convert ep-09-10-22-009.txt from Polish
# sub-folder (if exists) to UTF-8
# This is necessary because the file contains illegal non-unicode characters

clean_corrupt_file()


    
if args.file:
  print("\nPreprocessing file %s \n" %(path))
else:
  print("\nPreprocessing %s files in folder %s \n" %(len(file_list), path))

if args.log:
  open('log_preprocess.txt', 'w').close()
  logfile = open('log_preprocess.txt', mode='a')


#if args.disambiguateIDs:
counter = 1
print("\nDisambiguating speaker IDs\n")
for inputfile in file_list:
  if args.log:
    logfile.write(inputfile + "\n")
  disambiguate_speaker_IDs(inputfile)
  # Print progress status bar after cleaning file
  progress = int((counter/len(file_list))*100)
  statusbar = int(progress/2)
  sys.stdout.write("\r")
  sys.stdout.write("\t["+"="*statusbar+" "*(50-statusbar)+"]"+"\t"+str(progress)+" %")
  counter +=1
print("\n\nDisambiguation procedure completed!")

if args.log:
  logfile.close()

''' -c parameter has been depracated, use -d instead!
if args.clean:
  counter = 1
  print("\Cleaning speaker IDs\n")
  for inputfile in file_list:
    clean_IDs(inputfile)
    # Print progress status bar after cleaning file
    progress = int((counter/len(file_list))*100)
    statusbar = int(progress/2)
    sys.stdout.write("\r")
    sys.stdout.write("\t["+"="*statusbar+" "*(50-statusbar)+"]"+"\t"+str(progress)+" %")
    counter +=1
  print("\n\nCleaning completed!")
'''

  
print("\n\n%s files have been preprocessed successfully!\n" %(len(file_list)))
### End of main Program


