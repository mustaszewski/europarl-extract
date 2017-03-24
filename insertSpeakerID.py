'''
This script pre-processes EuroParl files, which is a necessary step
for the extraction of directional multilingual parallel corpora.

The -d parameter disambiguates speaker IDs to avoid that two or more speech segments are assigned the same ID

# DEPRECATED: The -c parameter assigns unique running speaker IDs to each speech segment in the corpus files.


'''

import fileinput
import re
import argparse
import os
import sys

def get_inputfile(path):
  if path.endswith('.txt'):
    file_list.append(path)
  else:
    print("Specified input file must have extension .txt")
    exit(1)
  ### end of function get_inputfile()

def get_inputfiles_from_folder(path):
  for root, dirs, files in os.walk(path):
    for filename in files:
      if filename.endswith('.txt'):
        file_list.append(os.path.join(root, filename))
        
  if len(file_list) == 0:
    print ("\nNo files with extension .txt were found in folder %s\n\n" %(path))
    exit(1)
  ### end of function get_inputfiles_from_folder()

def disambiguate_IDs(inputfile):
  usedIDs = {}
  for line in fileinput.FileInput(inputfile ,inplace=1):
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

''' # DEPRECATED FUNCTION clean_IDs, use disambiguate_IDs instead!
def clean_IDs(inputfile):
  # Get the first ID in file and create unique running IDs by increasing first ID by one
  # This is done for each line that contains a tag of form <SPEAKER ID="xxx"> 
  first_ID = True
  for line in fileinput.FileInput(inputfile ,inplace=1):
    line = line.strip()
    speakerID_match = speakerID_pattern.search(line)
    if speakerID_match:
      original_ID = speakerID_match.group(1)
      if first_ID:
        new_ID = int(speakerID_match.group(1))
        first_ID = False
      print(line.replace(original_ID, "{0:03}".format(new_ID)))
      new_ID += 1
    else:
      print(line)
  fileinput.close()
  ### end of function cleanIDs
'''

def preprocess_file(inputfile):
  #print(inputfile)
  prevline = ""
  new_speaker_id = 1
  
  
  for line in fileinput.FileInput(inputfile ,inplace=1):
    if exception1.search(line):
      print("~" + exception1.search(line).group(1) + "~")
    if langcode.search(line) and not speaker_tag.search(prevline):
      prevline = line.strip()
      lang = langcode.search(line).group(1)
      #line = line.replace(line, "XXXXXXXXXXXXXX\n" + line)
      line = line.replace(line, "<SPEAKER ID=\"x" + "{0:03}".format(new_speaker_id) + "\" LANG=\"" + lang + "\">\n" + re.sub(langcode, '', line).strip())
      new_speaker_id += 1
    else:
      prevline = line.strip()
    print (line.strip())
    fileinput.close()
    ### end of function preprocess_file()

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
parser.add_argument("-i", "--insert", action="store_true", help="Insert missing Speaker IDs")
#parser.add_argument("-c", "--clean", action="store_true", help="Clean up Speaker IDs by replacing duplicate IDs")
parser.add_argument("-d", "--disambiguateIDs", action="store_true", help="Disambiguate speaker IDs if one ID is assigned to multiple speech segments")
parser.add_argument("-f", "--file", action="store_true", help="Process a single file rather than all files in a directory")
args = parser.parse_args()
path = args.path

### Get input file(s) from arguments 
file_list = []
if args.file:
  get_inputfile(path)
else:
  get_inputfiles_from_folder(path)


### Main Program
if args.file:
  print("\nPreprocessing file %s \n" %(path))
else:
  print("\nPreprocessing %s files in folder %s \n" %(len(file_list), path))

if args.log:
  open('log_preprocess.txt', 'w').close()
  logfile = open('log_preprocess.txt', mode='a')


if args.disambiguateIDs:
  counter = 1
  print("\nDisambiguating speaker IDs\n")
  for inputfile in file_list:
    if args.log:
      logfile.write(inputfile + "\n")
    disambiguate_IDs(inputfile)
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


if args.insert:
  counter = 1
  print("\nInserting missing speaker IDs\n")
  for inputfile in file_list:
    preprocess_file(inputfile)
    # Print progress status bar after cleaning file
    progress = int((counter/len(file_list))*100)
    statusbar = int(progress/2)
    sys.stdout.write("\r")
    sys.stdout.write("\t["+"="*statusbar+" "*(50-statusbar)+"]"+"\t"+str(progress)+" %")
    counter +=1
  print("\n\nInserting IDs completed!")

  
print("\n\n%s files have been preprocessed successfully!\n" %(len(file_list)))
### End of main Program


