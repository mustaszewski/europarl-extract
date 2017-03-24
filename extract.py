'''
Prior to running this script, do the following (TODO: PREPARE .sh SCRIPT TO RUN ALL STEPS AT ONCE)
1) delete all empty lines:
  $ sed -i '/^$/d' txt/*/*.txt
  or use bash supplied script instead:
  $ ./extract_tools/deleteemptylines.sh txt/ # will perform deletion recursively in all subfolders

2) Delete all <P> tags:
  $ ./extract_tools/deleteXMLPar.sh txt/
  
3) Pre-process corpus files using the supplied script insertSpeakerID.py:
  $ python3 extract_tools/insertSpeakerID.py txt/ --d
  
  /home/m9/NLPLinguisticResources/europarl/in_test/b/ --d
 
'''

import sys
import os.path
import re
import pandas as pd
import numpy as np
import argparse
from unidecode import unidecode
from string import punctuation
from pandas.tools.tests.test_util import CURRENT_LOCALE
from itertools import zip_longest


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

def write_speaker(line, nextline, speakerMatch, filename_base): #(line, nextline, speakerMatch, day_ID, chapter_ID, filename_base)
  speaker_ID = speakerMatch.group(1)
  #unique_id = day_ID + "|" + chapter_ID + "|" + speaker_ID
  unique_id = filename_base + "|" + speaker_ID
  nameMatch = nameTag.search(line)
  if nameMatch:
    name = nameMatch.group(1).partition('(')[0].strip()
    name_normalised = normalise_name(name)
  else:
    name = ""
    name_normalised = 'nnnn' #or 'nnn' if length of normalised name is 3
    
  languageMatch = languageTag.search(line)
  #languageMatch = re.search(r'LANGUAGE="(\w{2})"', line.strip())
  if languageMatch:
    lang = languageMatch.group(1)
  else:
    lang = ""
  
  alt_lang_tag = langcode.search(nextline)
  #  make sure no exception of type (ES) Nr. 123 in next line is mistakingly taken as language code
  #  where in fact (ES) is only an abbreviation for European Commission in several languages (eg. CS, SK)
  if alt_lang_tag and not langcode_exception.search(nextline):
    additional_lang_tag = alt_lang_tag.group(1)
  else:
    additional_lang_tag = ""

  
  
  # if speakerID is already in data frame, update language code if provided
  if unique_id not in speaker_list.index:
    speaker_list.loc[unique_id] = [{}, {}, '', {}, '', {}]  # 'ID', 'NAMES_FULL_COUNT', 'NAMES_NORMALISED_SUMMARY', 'NAMES_MATCHING', 'ORIGINAL_LANGUAGE', 'SL', 'ADDITIONAL_LANGUAGE', 'SL2' # speaker_ID as first item was deleted
    if len(name) > 0:
      speaker_list.loc[unique_id].loc['NAMES_FULL_COUNT'][name] = 1
      #speaker_list.loc[unique_id].loc['NAMES_NORMALISED_COUNT'][name_normalised] = 1
    if len(lang) > 0:
      speaker_list.loc[unique_id].loc['ORIGINAL_LANGUAGE'][lang] = 1
    if len(additional_lang_tag) > 0:
      speaker_list.loc[unique_id].loc['ADDITIONAL_LANGUAGE'][additional_lang_tag] = 1
    
    
  else:
    
    if len(name) > 0:
      if name not in speaker_list.loc[unique_id].loc['NAMES_FULL_COUNT'].keys():
        speaker_list.loc[unique_id].loc['NAMES_FULL_COUNT'][name] = 1
      else:
        speaker_list.loc[unique_id].loc['NAMES_FULL_COUNT'][name] += 1
      #if name_normalised not in speaker_list.loc[unique_id].loc['NAMES_NORMALISED_COUNT'].keys():
      #  speaker_list.loc[unique_id].loc['NAMES_NORMALISED_COUNT'][name_normalised] = 1
      #else:
      #  speaker_list.loc[unique_id].loc['NAMES_NORMALISED_COUNT'][name_normalised] += 1
    
    
    if len(lang) > 0:
      if lang not in speaker_list.loc[unique_id].loc['ORIGINAL_LANGUAGE'].keys():
        speaker_list.loc[unique_id].loc['ORIGINAL_LANGUAGE'][lang] = 1
      else:
        speaker_list.loc[unique_id].loc['ORIGINAL_LANGUAGE'][lang] += 1
    
    if len(additional_lang_tag) > 0:
      if additional_lang_tag not in speaker_list.loc[unique_id].loc['ADDITIONAL_LANGUAGE'].keys():
        speaker_list.loc[unique_id].loc['ADDITIONAL_LANGUAGE'][additional_lang_tag] = 1
      else:
        speaker_list.loc[unique_id].loc['ADDITIONAL_LANGUAGE'][additional_lang_tag] += 1    

  #### END FUNCTION write_speaker()

## group_speakers(dict) creates adictionary containing short forms of normalised names (3 characters long)
# as keys and counts as values
# a simple heuristic groups all names that belong together irrespective of discrepancies in writing.
def group_speakers(dict1):
  speakers_summary = {}

  if len(dict1) == 1:
    for k, v in dict1.items():
      speakers_summary[normalise_name(k)[0:4]] = v #[0:3] to change length of normalised name tag to 4 instead of 3
  elif len(dict1) < 1:
    speakers_summary = {}

  else:
    pairwise_name_matches = [] # this list stores pairwise tuples that indicate which two normalised short names belong together 
    names = list(dict1.items()) # list of tuples containing speakername and count
    for i in range(len(names)):
      names[i] = (normalise_name(names[i][0]), names[i][1])
      if names[i][0][0:4] not in speakers_summary: #[0:3] to change length of normalised name tag to 4 instead of 3
        speakers_summary[names[i][0][0:4]] = int(names[i][1]) #[0:3] to change length of normalised name tag to 4 instead of 3
      else:
        speakers_summary[names[i][0][0:4]] += names[i][1] #[0:3] to change length of normalised name tag to 4 instead of 3
    #print("### " + str(names))
    #print("    " + str(speakers_summary))
    #speakers_summary[names[0][0][0:3]] = 0
    #print("    pairwise_name_matches:" + str(pairwise_name_matches) + "\n")
    names_copy = list(names)

    # iterate over names and names_copy to find which pairs of names belong together
    for n in names:
      names_copy.remove(n)
      name = n[0]
      count = n[1]
      for n_c in names_copy:
        name_copy = n_c[0]
        #print ("%s\tvs.\t%s" %(name, name_copy))
        
        if name[0:4] in name_copy[0:15]: #name_copy[0:15] restricts the full string to a 25 character version in order to avoid inflation of matches in very long names #[0:3] to change length of normalised name tag to 4 instead of 3
          #print("  %s\tis  in %s" %(name[0:3], name_copy[0:15]))
          if {name[0:4], name_copy[0:4]} not in pairwise_name_matches and len({name[0:4], name_copy[0:4]}) >1: #[0:3] to change length of normalised name tag to 4 instead of 3
            #print("  ADDING (%s, %s) to pairwise_name_matches" %(name[0:3], name_copy[0:3]))
            pairwise_name_matches.append({name[0:4], name_copy[0:4]}) #[0:3] to change length of normalised name tag to 4 instead of 3
      names_copy.append(n)
      ## At this point, pairwise_name_matches contains all 2-tuples of normalised short names that belong together
      

    #print("\nNOW ADDING COUNTS ACCORDING TO SETS!\n")
    #print("\n-_-_-_ " + str(speakers_summary) + "\n")
    #print("pairwise_name_matches: " + str(pairwise_name_matches))
    #print("Common elements: ")
    # Now iterare over pairwise_name_matches to find names that ocur several times across tuples
    # Such names will be the nucleus to group all other tuples that contain such shared names
    # These names will be stored in shared_names, with the shared names as keys and all names belonging to this shared name as values
    name_ocurrences = {}
    shared_names = {}

    # iterate over pairwise_name_matches and count in dictionary name_ocurrences how many times each element of each parwise_name_match ocurrs 
    for pnm in pairwise_name_matches:
      for name_short in pnm:
        if name_short in name_ocurrences:
          name_ocurrences[name_short] += 1
        else:
          name_ocurrences[name_short] = 1
    #print("NAME OCURRENCES: " + str(name_ocurrences))
    # iterate over name_ocurrences (holding nr. of ocurrences of each short name in pairwise matches) to find all short names that ocurr more than once and hence will form nuclei to group all names belonging to them
    for k,v in name_ocurrences.items():
      if v > 1:
        shared_names[k] = set()

    #print("Common keys: " + str(shared_names))
    
    for sn in shared_names:
      for pnm in pairwise_name_matches:
        if sn in pnm:
          shared_names[sn] = shared_names[sn] | pnm
    # At this point, shared_names contains all names that are being shared across sets as keys and all names that belong to them as values. The keys are thus the nuclei that group all names belonging to them

    # Update shared_names by finding those pairwise name matches that are not yet included in shared_names
    for pnm in pairwise_name_matches:
      if all(name_short not in shared_names.keys() for name_short in pnm):
        #print("%s contains element not present in shared_names" %(pnm))
        additionalkey = next(iter(pnm))
        shared_names[additionalkey] = pnm
    # At this point, shared_names contains groups of names that belong together. The groups are stored as values and the keys are represented by the nulei that were used to group names around them (i.e. names that are being shared across pairwise name matches)
    #print("Updated pairwise_name_matches: " + str(shared_names))
       #  if not all(only_roman_chars(k) for k in d.keys())


    # Now iterate over all group of names that belong together (stored as values in shared_names) to calculate aggregate sum of ocurrences for each group of names
    duplicatecheck = []
    for namegroup in shared_names.values():
      if not namegroup in duplicatecheck:
        duplicatecheck.append(namegroup)
        #print("Set: " + str(namegroup))
        joint_count = 0
        max_val = 0
        max_key = ''
        for nm in namegroup:
          joint_count += speakers_summary[nm]
          if speakers_summary[nm] > max_val:
            max_key = nm
            max_val = speakers_summary[nm]
          #speakers_summary.pop(nm)
          speakers_summary[nm] = 0
          #print(" Popping " + nm)
        #print("Count for %s = %s; max-key is %s (= %s)" %(namegroup, joint_count, max_key, max_val))
        speakers_summary[max_key] = joint_count
    #print("\nFINAL SHARED DICT: " + str(speakers_summary))
    speakers_summary_copy = {}
    for k, v in speakers_summary.items():
      if v != 0:
        speakers_summary_copy[k] = v
    #print(speakers_summary_copy)
    speakers_summary = speakers_summary_copy
    #print("HOOOOOPE!")
    #print(speakers_summary)
  return(speakers_summary)

def language_vote(originalLanguages, additionalLanguages):
  #print("o: " + str(originalLanguages))
  #print("a: " + str(additionalLanguages))

  # if no language in originalLanguages: vote = xNAN
  # if 1 language in originalLanguages: vote = the only language of originallanguages
  # if >1 languages in originalLanguages:  - if only one maximum count -> chose this language
  #                                        - if >1 maximum count: add counts from additional language tag (if applicable) to determine maximum count language
  
  if len(originalLanguages) > 1:
    maxkeys = [k for k, v in originalLanguages.items() if v == max(originalLanguages.values())]
    if len(maxkeys) == 1:
      vote = maxkeys[0]
      #print("Max is " + maxkeys[0])
    else:
      sums = {}
      for k in maxkeys:
        sums[k] = originalLanguages[k]

      for k in maxkeys:
        if k in additionalLanguages.keys():
          sums[k] = sums[k] + additionalLanguages[k]
      #print("Sums plus additionalLanguages: " + str(sums))
      #print("Max is " + str(max(sums, key=sums.get)))
      vote = str(max(sums, key=sums.get))
  elif len(originalLanguages) == 1:
    for k in originalLanguages.keys():
      x = k
    vote = str(x)

  else:
    #print("VAIN!!!!")
    if args.additionalLanguagetags:
      if len(additionalLanguages) == 0:
        vote = "zNAN"
      elif len(additionalLanguages) == 1:
        vote = list(additionalLanguages.keys())[0]
      else:
        sum_counts = sum(additionalLanguages.values())
        max_count = max(additionalLanguages.values())
        if max_count/sum_counts > 0.6:
          max_key = list(additionalLanguages.keys())[list(additionalLanguages.values()).index(max_count)]
          vote = max_key
        else:
          vote = "zNAN"
    else:
      vote = "xNAN"
  return(vote)
  ### END FUNCTION GROUP_NAMES()

def normalise_name(name):
  if exceptions_nonroman.search(name):
    name = latinise_name(name)
  if president.search(name):
    norm = "prsd"
  else:
    norm = unidecode(name).lower().translate(str.maketrans({a:None for a in punctuation})).replace(' ','')
  if len(norm) < 1:
    norm = "xxxx"
  return(norm) #t = re.sub(r'[^\w\s]','',s, re.UNICODE)

def latinise_name(name):
  replacements = {
  'Жозе Мануел Барозу':'José Manuel Barroso',
  'Сесилия Малмстрьом' : 'Cecilia Malmström',
  'Катрин Аштън' : 'Catherine Ashton',
  'Κυριάκος' : 'Kyriacos',
  'Мишел' : 'Michel',
  'Гюнтер' : 'Günther',
  'Жак' : 'jacques',
  'Δημήτρ' : 'Dimitr',
  'Оли Рен' : 'Olli Rehn',
  'Χαρ' : 'Char',
  'Ευαγγελία' : 'Evangelia',
  'Συλβάνα' : 'Sylvana',
  'Χρ' : 'Chr',
  'Щефан' : 'Stefan',
  'Μπ' : 'B',
  'Σπύρος' : 'Spyros',
  'Хосе' : 'Jose',
  'Хоакин' : 'Joaquin',
  'Йоханес' : 'Johannes',
  'Ян' : 'Jan',
  'Джо' : 'Joe',
  'Нели' : 'Neelie',
  'Сесилия': 'Cecilia',
  'Σηφουνάκης' : 'Sifunakis',
  'Παφίλης' : 'Pafilis',
  'Φώλιας' : 'Folias',
  'Джон' : 'John',
  'Петя' : 'Petya',
  'Кони' : 'Connie',
  'Мойра' : 'Máire',
  'Ив ' : 'Yves',
  'Жан-Клод Трише' : 'Jean-Claude Trichet',
  'Филип ' : 'Philippe', 
  }
  pattern = re.compile('|'.join(replacements.keys()))
  latinisation = pattern.sub(lambda x: replacements[x.group()], name)
  return(latinisation)

def string_difference(s1, s2):
  s1 = s1 + "#" * (4-len(s1)) #make sure that s1 is 3 (or 4 according to length of nomalised tag) characters long: add # to s if s shorter than 3
  s2 = s2 + "#" * (4-len(s2))
  diff = 0
  for i in range (len(s1)):
    #print("%s vs %s" %(string1[i],string2[i]))
    if s1[i] != s2[i]:
      diff += 1
  return(diff)

# match_speakers(dict) is used to determine whether the speaker names for each statement tag
# are matching or contradictory. If contradictory, the speaker names are regarded unambiguous if
# one name IDs accounts for at least 70% of all name IDs
def match_speakers(dict):
  values = list(dict.values())
  keys = list(dict.keys())
  
  if len(keys) == 0:
    speaker = "xNAN"
  elif len(keys) == 1:
    speaker = keys[0]
    #print("  Only one speaker in " + str(dict))
  elif len(keys) == 2:
    if 'prd' in keys:
      speaker = "xAMB"
      #print("  President in " + str(dict))
    else:
      sum_values = sum(values)
      max_value = max(values)
      if max_value/sum_values >= 0.9:
        #print("  Majority vote positive in " + str(dict))
        if string_difference(keys[0], keys[1]) <= 1:
          #print("  Majority and string difference check positive in " + str(dict))
          max_key = keys[values.index(max_value)]
          speaker = max_key
        else:
          #print("  String difference check negative in " + str(dict))
          speaker = "xAMB"     
      else:
        speaker = "xAMB"
        #print("  Majority vote negative in " + str(dict))
  else:
    speaker = "xAMB"
    #print("  More than 2 speakers in " + str(dict))
  return(speaker)
  

def analyse_file(inputfile):
  
  filename_base = inputfile.split("/")[-1].split(".txt")[0].split("ep-")[1]
 
  # get day identifier from filename

  #identifier_base = inputfile.split('.')[0].split('ep-')[1]

  #identifier_day = identifier_base.split('-')[0:4]

  #identifier_suffix = identifier_base.split('-')[3:]
  #day_ID = 'y'+identifier_day[0] + 'm'+identifier_day[1] + 'd'+identifier_day[2]

  
  #ep-07-04-26-015-01.txt # (n = 3000)
  #ep-09-09-16-010.txt      (n=  5500)
  #ep-09-09-15.txt          (n =  650)
  
  # to avoid EOF errors, reading file line by line looks behind instead of looking ahead
  # this means that after reading a line it will be stored as prev_line (in for-loop renamed to current_line for verbosity)
  prev_line = None
  
  with open(inputfile, 'rt', encoding='utf-8', errors='ignore') as fl: # flag errors='ignore' is used in order to prevent program terminating upon encoding errors (one such error can be found in file /txt/pl/ep-09-10-22-009.txt)
    #iterate over whole file, extract chapterIDs, SpeakerIDs and language codes (the latter in write_speaker)
    for line in fl:
      if not prev_line == None:
        current_line = prev_line.strip()
        next_line = line.strip()
        #print(current_line[0:80])
        chapterMatch = chapterTag.search(current_line)
        if chapterMatch:
          chapter_ID = chapterMatch.group(1)
        speakerMatch = speakerTag.search(current_line)
        if speakerMatch:
          #print(prev_line[0:30])
          write_speaker(current_line, next_line, speakerMatch, filename_base) #(current_line, next_line, speakerMatch, day_ID, chapter_ID, filename_base)
      prev_line = line.strip()
    
    # after reaching the last line of file (stored as prev_line), check once again whether there is a language tag
    # this time, next_line is empty because it is the end of file, therefore we pass '' to function write_speaker()
    #print("EOF: %s" %(prev_line[0:80]))
    
    if prev_line == None:
      prev_line = ''
    chapterMatch = chapterTag.search(prev_line)
    if chapterMatch:
      chapter_ID = chapterMatch.group(1)
    speakerMatch = speakerTag.search(prev_line)
    if speakerMatch:
      write_speaker(prev_line, '', speakerMatch, filename_base) # here prev_line is the last line of fie and next_line is '' because of EOF
  #speaker_list.loc['y06m04d04|1|005'].loc['ORIGINAL_LANGUAGE']['XY'] = 'xy'
  ###### END FUNCTION analyse_file()

'''
def get_languagepairs(sourceLanguages, targetLanguages):
  languagepairs = []
  for tl in targetLanguages:
    for sl in sourceLanguages:
      if sl != tl:
        languagepairs.append((sl, tl))
  return(languagepairs)
'''
    

def create_folders_comparable_nontranslated(outDir, tl):
  '''try:
    os.makedirs(outDir + "/comparable")
    os.makedirs(outDir + "/comparable/translated")
    os.makedirs(outDir + "/comparable/non-translated")
  except OSError:
    pass
  '''
  #for lp in languagePairs:
  try:
    #os.makedirs(outDir + "/comparable/translated/" + lp[1] + "/" + lp[0] + "-" + lp[1])
    os.makedirs(outDir + "/comparable/non-translated/" + tl)
  except OSError:
    pass

  
def create_folders_comparable_translated(outDir, sl, tl):
  '''
  try:
    os.makedirs(outDir + "/comparable")
    os.makedirs(outDir + "/comparable/translated")
    os.makedirs(outDir + "/comparable/non-translated")
  except OSError:
    pass
  
  for lp in languagePairs:'''
  try:
    os.makedirs(outDir + "/comparable/translated/" + tl + "/" + sl + "-" + tl)
    #os.makedirs(outDir + "/comparable/non-translated/" + lp[1])
  except OSError:
    pass




def create_folders_parallel(outDir, sl, tl):
  try:
    os.makedirs(outDir + "/parallel/" + sl + "-" + tl + "/" + sl + "_sl")
    os.makedirs(outDir + "/parallel/" + sl + "-" + tl + "/" + tl + "_tl")
    if args.tmx:
      os.makedirs(outDir + "/parallel/" + sl + "-" + tl + "/tmx")
  except OSError:
    pass

def write_statements_to_files(filename_input, filename_output, ids):
  # from list of ids create regex pattern to match speaker IDs for nontranslated statemens to be extracted
  speakerID_pattern = re.compile(r'<SPEAKER ID="?(' + '|'.join(ids) +')"? ')
  #print("  " + str(speakerID_pattern))
  
  # Open EuroParl input file and iterate linewise to find (non)translated statements to be extracted
  # All of these statements will be written to separate output files 
  with open(filename_input, 'rt', encoding='utf-8', errors='ignore') as fl_in:    
    prev_line = None
    do_extraction = False
    for line in fl_in:
      if not prev_line == None:
        current_line = prev_line.strip()
        next_line = line.strip()
        
        # if regex finds speaker ID in line write statement to output file
        # all lines until the ocurrence of a further < > tag will be written to output file
        if speakerID_pattern.search(current_line):

          statementID = speakerID_pattern.search(current_line).group(1)
          fname_out = filename_output.replace('xIDx', statementID)
          #print("Writing to output file\t" + fname_out)
          #filename_output = (outDir + "/comparable/non-translated/" + tl + "/" + filename + "_" + statementID + "_" + tl.lower() + ".txt").replace('//', '/')
          open(fname_out, mode='w').close() # make sure outputfile exists
          fl_out = open(fname_out, mode='a', encoding='utf-8')
          do_extraction = True
          
        if do_extraction == True: # and not speakerID_pattern.search(current_line): # remove and not speakerID_pattern.search(current_line): to preserve speaker id tag 
          fl_out.write(current_line+"\n")
        if do_extraction == True and xmlTag.search(next_line):#"<SPEAKER ID" in next_line:
          #print("S T O P P I N G,   N E X T   L I N E    I S : "+ next_line[0:40])
          do_extraction = False
          fl_out.close()
          #print("  nl " + next_line[0:40])

      prev_line = line.strip()
    current_line = prev_line
    next_line = ''
    if do_extraction == True:
      fl_out.write(current_line)
      fl_out.close()
      

def write_statements_to_tmx(filename_input_sl, filename_input_tl, filename_output_tmx, ids, sl, tl):
  #print("\n\n__ WRITE STATEMENTS TO TMX CALLED FOR FILE " + filename_input_sl + " IN LANGUAGE PAIR " + sl + "-" + tl + " __\n\n")
  # from list of ids create regex pattern to match speaker IDs for nontranslated statemens to be extracted
  speakerID_pattern = re.compile(r'<SPEAKER ID="?(' + '|'.join(ids) +')"? ')
  #print("  " + str(speakerID_pattern))
  
  paragraphs_sl = {}
  paragraphs_tl = {}
  # Open EuroParl input file and iterate linewise to find (non)translated statements to be extracted
  # All of these statements will be written to separate output files 
  with open(filename_input_sl, 'rt', encoding='utf-8', errors='ignore') as fl_in_sl:    
    prev_line = None
    do_extraction = False
    for line in fl_in_sl:
      if not prev_line == None:
        current_line = prev_line.strip()
        next_line = line.strip()
        
        # if regex finds speaker ID in line write statement to output file
        # all lines until the ocurrence of a further < > tag will be written to output file
        if speakerID_pattern.search(current_line):

          statementID = speakerID_pattern.search(current_line).group(1)
          fname_out = filename_output_tmx.replace('xIDx', statementID)
          #print("Adding key to paragraphs_sl\t" + fname_out)
          paragraphs_sl[fname_out] = []
          

          do_extraction = True
          
        if do_extraction == True and not speakerID_pattern.search(current_line): # and not speakerID_pattern.search(current_line):
          paragraphs_sl[fname_out].append(current_line)
          #print("  Adding line %s to paragraphs_sl for key %s" %(current_line[0:30], fname_out))
          #fl_out.write(current_line+"\n")
        if do_extraction == True and xmlTag.search(next_line):#"<SPEAKER ID" in next_line:
          #print("S T O P P I N G,   N E X T   L I N E    I S : "+ next_line[0:40])
          do_extraction = False
          #fl_out.close()
          #print("  nl " + next_line[0:40])

      prev_line = line.strip()
    current_line = prev_line
    next_line = ''
    if do_extraction == True:
      paragraphs_sl[fname_out].append(current_line)
      #fl_out.write(current_line)
  fl_in_sl.close()


  # All of these statements will be written to separate output files 
  with open(filename_input_tl, 'rt', encoding='utf-8', errors='ignore') as fl_in_tl:
    #print("##Opening TL input file %s for tmx extraction" %(filename_input_tl))
    prev_line_tl = None
    do_extraction = False
    for line_tl in fl_in_tl:
      if not prev_line_tl == None:
        current_line_tl = prev_line_tl.strip()
        next_line_tl = line_tl.strip()
        
        # if regex finds speaker ID in line write statement to output file
        # all lines until the ocurrence of a further < > tag will be written to output file
        if speakerID_pattern.search(current_line_tl):

          statementID = speakerID_pattern.search(current_line_tl).group(1)
          fname_out = filename_output_tmx.replace('xIDx', statementID)
          paragraphs_tl[fname_out] = []
          #print("Writing to output file\t" + fname_out)
          #filename_output = (outDir + "/comparable/non-translated/" + tl + "/" + filename + "_" + statementID + "_" + tl.lower() + ".txt").replace('//', '/')
          #open(fname_out, mode='w').close() # make sure outputfile exists
          #fl_out = open(fname_out, mode='a', encoding='utf-8')
          do_extraction = True
          
        if do_extraction == True and not speakerID_pattern.search(current_line_tl):
          paragraphs_tl[fname_out].append(current_line_tl)
          #fl_out.write(current_line+"\n")
        if do_extraction == True and xmlTag.search(next_line_tl):#"<SPEAKER ID" in next_line:
          #print("S T O P P I N G,   N E X T   L I N E    I S : "+ next_line[0:40])
          do_extraction = False
          #fl_out.close()
          #print("  nl " + next_line[0:40])

      prev_line_tl = line_tl.strip()
    current_line_tl = prev_line_tl
    next_line_tl = ''
    if do_extraction == True:
      paragraphs_tl[fname_out].append(current_line_tl)
      #fl_out.write(current_line)
  fl_in_tl.close()
  
  #print("Paragraphs:\n  SL (%s)\t%s\n  TL (%s)\t%s" %(len(paragraphs_sl), paragraphs_sl, len(paragraphs_tl), paragraphs_tl))
  for key in paragraphs_sl.keys():
    open(key, mode='w').close() # make sure outputfile exists
    fl_out = open(key, mode='a', encoding='utf-8')
    if key in paragraphs_tl.keys():
      fl_out.write("<tmx version=\"1.4b\">\n"\
                   "<header>\n"\
                   "</header>\n"\
                   "<body>\n"\
                   "<tu>\n")
      for translation_unit in zip_longest(paragraphs_sl[key], paragraphs_tl[key], fillvalue = ""):
        fl_out.write("<tuv xml:lang=\"%s\">\n"\
                     "<seg>%s</seg>\n"\
                     "</tuv>\n<tuv xml:lang=\"%s\">\n"\
                     "<seg>%s</seg>\n"\
                     "</tuv>\n"\
                     %(sl, translation_unit[0], tl, translation_unit[1]))
        fl_out.write('</tu>\n</body>\n</tmx>\n')
  fl_out.close()



def extract_comparable_nontranslated(statements_nontranslated, tl):
  for filename in statements_nontranslated.keys():
    #ids = statements_nontranslated[filename]
    # Generate file names for input and output. For each extracted statement, a new outputfile will be \
    # created. Name of output file contains the following: 1) Europarl filename (without prefix ep-), 2) Statement ID \
    # and 3) language code.
    fname_input = (inDir + "/" + tl.lower() + "/ep-" + filename + ".txt").replace('//', '/')
    fname_output = (outDir + "/comparable/non-translated/" + tl + "/" + filename + "_" + "xIDx" + "_" + tl.lower() + ".txt").replace('//', '/')
    
    if os.path.exists(fname_input):
      #print("\nReading Europarl-file " + fname_input)
      create_folders_comparable_nontranslated(outDir, tl)
      # Write to output director one statement file for each non-translated statement in given language \
      # from the Europarl inputfile by calling function write_statements_to_files(in, out, id)
      if args.debug:
        logfile.write("  Extracting non-translated comparable statements from\t%s (filename: %s)\n" %(fname_input, statements_nontranslated[filename]))
      write_statements_to_files(fname_input, fname_output, statements_nontranslated[filename]) #3rd argument = statement ID
  ######

def extract_comparable_translated(statements_sourcelanguage, sl, tl):
  #print("\nOBTAINING text in %s originally uttered in %s\n" %(tl, sl))
  for filename in statements_sourcelanguage.keys():
    # Generate filenames for input and output. Input: TL file with corresponding filename \
    # from statements_translated. Outputfile contains 1) Europarl filename (without prefix ep-), 2) Statement ID \
    # and 3) target language code
    fname_input = (inDir + "/" + tl.lower() + "/ep-" + filename + ".txt").replace('//', '/')
    fname_output = (outDir + "/comparable/translated/" + tl + "/" + sl + "-" + tl + "/" + filename + "_" + "xIDx" + "_" + tl.lower() + ".txt").replace('//', '/')
    
    if os.path.exists(fname_input):
      #print("Reading Europarl-file\t" + fname_input)
      create_folders_comparable_translated(outDir, sl, tl)
      if args.debug:
        logfile.write("  Extracting translated comparable statements from\t%s\n" %(fname_input))
      write_statements_to_files(fname_input, fname_output, statements_sourcelanguage[filename])
      

def extract_parallel(statements_sourcelanguage, sl, tl):
  #print("\nOBTAINING text originally uttered in %s and translated to %s\n" %(sl, tl))
  for filename in statements_sourcelanguage.keys():
    # Generate filenames for input and output. Input: TL file with corresponding filename \
    # from statements_translated. Outputfile contains 1) Europarl filename (without prefix ep-), 2) Statement ID \
    # and 3) target language code
    #fname_input = (inDir + "/" + tl.lower() + "/ep-" + filename + ".txt").replace('//', '/')
    fname_input_sl = (inDir + "/" + sl.lower() + "/ep-" + filename + ".txt").replace('//', '/')
    fname_input_tl = (inDir + "/" + tl.lower() + "/ep-" + filename + ".txt").replace('//', '/')
    
    #fname_output = (outDir + "/comparable/translated/" + tl + "/" + sl + "-" + tl + "/" + filename + "_" + "xIDx" + "_" + tl.lower() + ".txt").replace('//', '/')
    
    if os.path.exists(fname_input_sl) and os.path.exists(fname_input_tl):
      #print("Reading Europarl-files\n\t%s\n\t%s" %(fname_input_sl, fname_input_tl))
      fname_output_sl = (outDir + "/parallel/" + sl + "-" + tl + "/" + sl + "_sl/" + filename + "_" + "xIDx" + "_" + sl.lower() + ".txt").replace('//', '/')
      fname_output_tl = (outDir + "/parallel/" + sl + "-" + tl + "/" + tl + "_tl/" + filename + "_" + "xIDx" + "_" + tl.lower() + ".txt").replace('//', '/')    
      if args.tmx:
        fname_output_tmx = (outDir + "/parallel/" + sl + "-" + tl + "/tmx/" + filename + "_" + "xIDx" + "_" + sl.lower() + "-" + tl.lower() + ".tmx").replace('//', '/')    
      create_folders_parallel(outDir, sl, tl)
      #print(" Preparing output files\n\t%s\n\t%s" %(fname_output_sl, fname_output_tl))
      
      write_statements_to_files(fname_input_sl, fname_output_sl, statements_sourcelanguage[filename])
      write_statements_to_files(fname_input_tl, fname_output_tl, statements_sourcelanguage[filename])
      if args.tmx:
        write_statements_to_tmx(fname_input_sl, fname_input_tl, fname_output_tmx, statements_sourcelanguage[filename], sl, tl)
      
      
      #write_parallel_statements_to_files(fname_input_sl, fname_input_tl, fname_output_sl, fname_output_tl, statements_sourcelanguage[filename])
      
      #write_statements_to_files(fname_input, fname_output, statements_sourcelanguage[filename])

############################################ MAIN #####################################

### Define globally used regex-patterns
langcode = re.compile (r"\((BG|CS|DA|DE|EL|EN|ES|ET|FI|FR|GA|\
                        HU|IT|LT|LV|MT|NL|PL|PT|RO|SK|SV|SL)\)")
langcode_exception = re.compile(r'(\(ES\) ?(č\.|č|št|št\.|Nr\.)? ?\d{2,})')

chapterTag = re.compile(r'<CHAPTER ID="?([\d_]+)"?')
speakerTag = re.compile(r'<SPEAKER ID="?(\d+(_\d{3})?)"?')
languageTag = re.compile(r'LANGUAGE="(\w{2})"')
nameTag = re.compile(r'NAME="([^"]*)"')
president = re.compile(r'(Πρόεδρ|Président|Formand|Președin|Elnök|Przewodnicz|\
                              |Presid|Juhataja|Pirminink|Talman|Председа|Voorzitter|Předsed|\
                              |Puhemies|Puheenjoh|Präsident|Priekš|Přesed|Prieks|Prési|Predsed|Preisdente|\
                              |Preşdinte|Προεδρ|Preşedi|Представ|Ordförand|Preseda)', re.I)
exceptions_nonroman = re.compile(r'(|Барозу|Малмстрьом|Κυριάκος|Аштън|Мишел|Гюнтер|Йоханес|Хоакин|\
                                    |Хосе|Σπύρος|Щефан|Συλβάνα|Ευαγγελία|Оли Рен|Δημητρακόπουλος|\
                                    |Δημήτριος|Жак|Джо|Ян|Μπ|Χρ|Χαρ)')
xmlTag = re.compile(r'^<.+>$')


###  Define command line arguments

choices_sl = ['all', 'BG', 'CS', 'DA', 'DE', 'EL', 'EN', 'ES', 'ET', 'FI', 'FR', 'GA', 'HU','IT',
             'LT', 'LV', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SL', 'SV']
choices_tl = ['all', 'BG', 'CS', 'DA', 'DE', 'EL', 'EN', 'ES', 'ET', 'FI', 'FR', 'HU', 'IT',
              'LT', 'LV', 'NL', 'PL', 'PT', 'RO', 'SK', 'SL', 'SV']

parser = argparse.ArgumentParser(description="Extraction of Comparable or Parallel Corpora from EuroParl")
subparsers = parser.add_subparsers(dest="subcommand")

#  Subparser for Comparable Corpora
parser_comparable = subparsers.add_parser("comparable", description="Extraction of comparable corpora from EuroParl")

langs_comparable = parser_comparable.add_argument_group("LANGUAGES")
langs_comparable.add_argument("-sl", metavar ="SOURCE LANGUAGE(S)", nargs='+', choices=choices_sl, required=True, help='Choose from {%(choices)s}')
langs_comparable.add_argument("-tl", metavar ="TARGET LANGUAGE(S)", nargs='+', choices=choices_tl, required=True, help='Choose from {%(choices)s}')

paths_comparable = parser_comparable.add_argument_group('PATHS')
paths_comparable.add_argument("-i", "--inputFolder", required=True, help="Path to file to be processed or directory that contains files to be processed")
paths_comparable.add_argument("-o", "--outputFolder", required=True, help="Output folder for storage of extracted corpus files")

iooptions_comparable = parser_comparable.add_argument_group("INPUT-/OUTPUT OPTIONS")
iooptions_comparable.add_argument("-d", "--debug", required=False, action= "store_true",
                    help="Create a log file to for debugging")
iooptions_comparable.add_argument("-f", "--file", action="store_true", required=False, help="Process a single input file rather than all files in a directory")
iooptions_comparable.add_argument("-s", "--statementList", nargs=1, required=False,
                    help="Supply External Statement List in CSV Format")
iooptions_comparable.add_argument("-al", "--additionalLanguagetags", action="store_true", required=False, help="Disseminate additional language tags to increase number of statements")


#  Subparser for Parallel Corpora
parser_parallel = subparsers.add_parser("parallel", description="Extraction of parallel corpora from EuroParl")

langs_parallel = parser_parallel.add_argument_group("LANGUAGES")
langs_parallel.add_argument("-sl", metavar ="SOURCE LANGUAGE(S)", nargs='+', choices=choices_sl, required=True, help='Choose from {%(choices)s}')
langs_parallel.add_argument("-tl", metavar ="TARGET LANGUAGE(S)", nargs='+', choices=choices_tl, required=True, help='Choose from {%(choices)s}')

paths_parallel = parser_parallel.add_argument_group('PATHS')
paths_parallel.add_argument("-i", "--inputFolder", required=True, help="Path to file to be processed or directory that contains files to be processed")
paths_parallel.add_argument("-o", "--outputFolder", required=True, help="Output folder for storage of extracted corpus files")

iooptions_parallel = parser_parallel.add_argument_group("INPUT-/OUTPUT OPTIONS")
iooptions_parallel.add_argument("-t", "--tmx", required=False, action= "store_true",
                    help="Save parallel corpora in TMX format")
iooptions_parallel.add_argument("-d", "--debug", required=False, action= "store_true",
                    help="Create a log file to for debugging")
iooptions_parallel.add_argument("-f", "--file", action="store_true", required=False, help="Process a single input file rather than all files in a directory")
iooptions_parallel.add_argument("-s", "--statementList", nargs=1, required=False,
                    help="Supply External Statement List in CSV Format")
iooptions_parallel.add_argument("-al", "--additionalLanguagetags", action="store_true", required=False, help="Disseminate additional language tags to increase number of statements")


#  Parse command line input
args = parser.parse_args()

corpustype = args.subcommand
  
inDir = args.inputFolder
outDir = args.outputFolder

#  Get input file(s) from arguments 
file_list = []
if args.file:
  get_inputfile(inDir)
else:
  get_inputfiles_from_folder(inDir)

sourceLanguages = args.sl
if 'all' in sourceLanguages:
  choices_sl.remove('all')
  sourceLanguages = choices_sl
  
targetLanguages = args.tl
if 'all' in targetLanguages:
  choices_tl.remove('all')
  targetLanguages = choices_tl
  
if args.debug:
  open(outDir + '/log_extraction.txt', 'w').close()
  logfile = open(outDir + '/log_extraction.txt', mode='a')

if args.statementList:
  statementList_path = args.statementList[0]
  print(statementList_path)

###  Parsing command line input completed

###  If no external CSV list of statements is supplied then generate it from EuroParl
if args.statementList:
  print("Reading list of statements from pre-compiled external CSV file %s" %(statementList_path))
  speaker_list = pd.read_csv(statementList_path, sep='\t', dtype=str, index_col=0)
  print("  CSV file loaded into memory.")
  #print(speaker_list)
  #print("~~~~~~~~~~ UNIQUE IDs ~~~~~~~~~~")
  #uniqueIDs = speaker_list.ix[:,0]
  #print(uniqueIDs)
else:
  if args.file:
    print("\nProcessing file %s \n" %(inDir))
  else:
    print("\nProcessing %s files in folder %s\n" %(len(file_list), inDir))
  speaker_list = pd.DataFrame(columns= ('NAMES_FULL_COUNT', 'NAMES_NORMALISED_SUMMARY', 'NAMES_MATCHING', 'ORIGINAL_LANGUAGE', 'SL', 'ADDITIONAL_LANGUAGE')) #, 'ALTERNATIVE_LANGUAGE' # 'ID', as first tag was disabled
  speaker_list.index.name = 'UNIQUE_ID'
  
#  Start iterating over input files to generate list of statements
  counter = 1
  for inputfile in file_list:
    if args.debug:
      logfile.write(inputfile + "\n")
    analyse_file(inputfile)
  
    progress = int((counter/len(file_list))*100)
    statusbar = int(progress/2)
    sys.stdout.write("\r")
    sys.stdout.write("\t["+"="*statusbar+" "*(50-statusbar)+"]"+"\t"+str(progress)+" %")
    counter +=1
    
  print("\n\nLength of list of statements: %s\n" %len(speaker_list))
#  Finished iterating over input files

#  Post-process generated list of statements:\
#  1) Disambiguate speakers by calling match_speakers() \
#  2) Determine source language from < > language tags (SL) and alternative parenthesis () language tags (SL2) \
#     by calling language_vote()
  print("Starting to post-process statement list, please wait\n")
  if args.debug:
    logfile.write("\n\n###### Start post-processing statement list ######\n\n")
  for index, row in speaker_list.iterrows(): # index is equivalent to column unique_id
    ## Start Post-Processing speaker_list
    #  Disambiguate Speakers
    if args.debug:
      logfile.write(index + "\n")
    row['NAMES_NORMALISED_SUMMARY'] = group_speakers(row['NAMES_FULL_COUNT'])
    row['NAMES_MATCHING'] = match_speakers(row['NAMES_NORMALISED_SUMMARY'])
    
    # Determine Source Language of Each Statement
    sourceLanguage = language_vote(row['ORIGINAL_LANGUAGE'], row['ADDITIONAL_LANGUAGE'])
    row['SL'] = sourceLanguage
    
    '''
    if not row['ORIGINAL_LANGUAGE']:
      if row['ADDITIONAL_LANGUAGE']:
        row['SL2'] = max(row['ADDITIONAL_LANGUAGE'], key=row['ADDITIONAL_LANGUAGE'].get) #language_vote(, row['ORIGINAL_LANGUAGE'])
      else:
        row['SL2'] = "xNAN"
    '''
    ##  Finished Post-Processing speaker_list
    
  print("Post-processing completed, final list of statements has been generated!\n")
  speaker_list.to_csv(outDir + 'statementList_full.csv', sep='\t', header=True, encoding='UTF-8')
  print("Speaker list successfully exported to CSV as " + outDir + "/statementList_full.csv !\n")
  #print(speaker_list)
###  Finished Generating and Post-Processing List of Statements from Input Files


###  Start Extracting Comparable or Parallel Corpus Files for Selected Languages according to Command Line Input 
############# COMPARABLE CORPUS #################


#output_stats = pd.DataFrame(columns= ('LANGUAGE_PAIR', 'NUMBER_OF_STATEMENTS')) 
#output_stats.index.name = 'INDEX'
if corpustype == "comparable":
  print("\n##\tSTARTING EXTRACTION OF COMPARABLE CORPORA ##\n")
  #print("  Extracting NON-TRANSLATED Original Text for Each Target Language")
###  Extracting NON-TRANSLATED Original Text for Each Target Language
  if args.debug:
    logfile.write("\n\n ###### START EXTRACTION OF NON-TRANSLATED COMPARABLE CORPORA ######\n")
  for tl in targetLanguages:
    #print("\nExtracting non-translated original text in language %s" %(tl))
    # Filter speaker_list to find statements originally written in selected language and with unambiguous speaker
    unambiguous_statemens_nontranslated = speaker_list[(speaker_list['SL'] == tl) & (speaker_list['NAMES_MATCHING'] != "xAMB")].index #sort_index(ascending=False).
    # put all non-translated statements for given language in dictionary statements_nontranslated
    # keys: filenames of files containing the statements, values: speaker IDs pointing to each non-translated statement 
    statements_nontranslated = {}
    for usn in unambiguous_statemens_nontranslated:
      fname_out = usn.split("|")[0]
      id = usn.split("|")[1]
      if fname_out not in statements_nontranslated:
        statements_nontranslated[fname_out] = [id]
      else:
        statements_nontranslated[fname_out].append(id)
    #print("\nThere are %s files containing non-translated statements uttered in target language %s\n %s" %(len(statements_nontranslated), tl, statements_nontranslated))
    extract_comparable_nontranslated(statements_nontranslated, tl)
###  Finished extracting NON-TRANSLATED part of comparable corpus for each target language ###
    
###  Starting Extraction of TRANSLATED text for each SL-TL pair
  if args.debug:
    logfile.write("\n\n ###### START EXTRACTION TRANSLATED COMPARABLE CORPORA ######\n")
  #print("\nExtracting translated text in language %s" %(tl))
  for sl in sourceLanguages:
    #print("\n\nExtracting statements uttered in language %s" %(sl))
    unambiguous_statemens_in_sourcelanguage = speaker_list[(speaker_list['SL'] == sl) & (speaker_list['NAMES_MATCHING'] != "xAMB")].index
    # put all source language statements for given language in dictionary statements_sourcelanguage
    # keys: filenames of files containing the statements, values: speaker IDs pointing to source language statement 
    statements_sourcelanguage = {}
    for uss in unambiguous_statemens_in_sourcelanguage:
      fname = uss.split("|")[0]
      id = uss.split("|")[1]
      if fname not in statements_sourcelanguage:
        statements_sourcelanguage[fname] = [id]
      else:
        statements_sourcelanguage[fname].append(id)
    #print("\nThere are %s files containing source-language statements uttered in language %s\n %s" %(len(statements_sourcelanguage), sl, statements_sourcelanguage))
    for tl in targetLanguages:
      if sl != tl: #avoid pairs of type BG-BG, which are equivalent to non-translated statements
        extract_comparable_translated(statements_sourcelanguage, sl, tl)
  print("\nExtraction of Comparable Corpora Completed!\n\n")


############# PARALLEL CORPUS #################
else:
  print("\n##\tSTARTING EXTRACTION OF PARALLEL CORPORA ##\n")
  
  for sl in sourceLanguages:
    #print("\n\nExtracting statements uttered in source language %s" %(sl))
    unambiguous_statemens_in_sourcelanguage = speaker_list[(speaker_list['SL'] == sl) & (speaker_list['NAMES_MATCHING'] != "xAMB")].index
    # put all source language statements for given language in dictionary statements_sourcelanguage
    # keys: filenames of files containing the statements, values: speaker IDs pointing to source language statement 
    statements_sourcelanguage = {}
    for uss in unambiguous_statemens_in_sourcelanguage:
      fname = uss.split("|")[0]
      id = uss.split("|")[1]
      if fname not in statements_sourcelanguage:
        statements_sourcelanguage[fname] = [id]
      else:
        statements_sourcelanguage[fname].append(id)
    #print("\nThere are %s files containing source-language statements originally uttered in language %s\n %s" %(len(statements_sourcelanguage), sl, statements_sourcelanguage))
    for tl in targetLanguages:
      if tl != sl: #avoid pairs of type BG-BG, which are equivalent to non-translated statements
        extract_parallel(statements_sourcelanguage, sl, tl)
  print("\nExtraction of PARALLEL Corpora Completed!\n\n")

      
if args.debug:
  logfile.close()
