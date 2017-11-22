'''
Prior to running this script, do the following (TODO: PREPARE .sh SCRIPT TO RUN ALL STEPS AT ONCE)
1) Clean source files:
  $ cd europarl
  $ europarl_extract/preprocess/cleanSourceFiles.sh
  

2) Disambiguate conflicting IDs and insert missing IDs:
  $ python3 europarl_extract/disambiguate_speaker_IDs.py txt/

3) Split sentences and tokenise source files (splitting only required for parallel corpora, tokenisation is optional for both comparable and parallel corpora)
  $ europarl_extract/preprocess/segment-tokenise_EuroParl.sh txt/
  OR
  $ europarl_extract/preprocess/segment-tokenise_ixaPipes.sh txt/
  OR
  $ europarl_extract/preprocess/segment_EuroParl.sh txt/
  
4) Extract multilingual speaker turns:
4.1) For extraction of comparable corpora do:
  $ python3 europarl_extract/extract.py comparable -sl PL ES -tl DE -i txt/ -o output_folder/ -s statementList_full_beta.csv -al -c both
'''

import sys
import os.path
import re
import pandas as pd
import argparse
from unidecode import unidecode
from string import punctuation
from datetime import datetime
from gale_church import gale_church_alignment

''' # Function not required
def get_sourcefile(path):
  if path.endswith('.txt'):
    europarl_sourcefiles.append(path)
  else:
    print("Specified input file must have extension .txt")
    exit(1)
  ### end of function get_sourcefile()
'''

def get_sourcefiles_from_folder(path):
  """ Read list of EuroParl source files from input folder.
    
  Arguments:
    path (str) -- Path to input folder.

  Returns:
    sourcefiles (list) -- List of EuroParl source file names as strings.
    
  Raises:
    Terminates program if no source files in input folder.

  """
  sourcefiles = []
  for root, dirs, files in os.walk(path):
    for filename in files:
      if filename.endswith('.txt'):
        sourcefiles.append(os.path.join(root, filename))
        
  if len(sourcefiles) == 0:
    print ("\nNo files with extension .txt were found in folder %s\n\n" %(path))
    exit(1)
  return sourcefiles
### END OF FUNCTION DECLARATION



def analyse_sourcefile(inputfile):
  """ Extract metadata from EuroParl source file and pass it to function write_metadata_to_df(current_line, next_line, speakerMatch, filename_base).
    
  Arguments:
    inputfile (str) -- Path to input file.

  Returns:
    Nothing; instead, it calls function write_metadata_to_df(current_line, next_line, speakerMatch, filename_base) to write metadata to data frame.
    
  """
  filename_base = inputfile.split("/")[-1].split(".txt")[0].split("ep-")[1] # basename of the input file, i.e. truncate folder path and prefix 'ep' and suffix '.txt' from filename
  
  # Loop over input file line-by-line and match regex patterns indicating speaker turn metadata
  # To avoid EOF errors, reading file line by line looks behind instead of looking ahead
  # This means that after reading a line it will be stored as prev_line (in for-loop renamed to current_line for verbosity)
  prev_line = None
  
  with open(inputfile, 'rt', encoding='utf-8', errors='ignore') as fl: # flag errors='ignore' is used in order to prevent program terminating upon encoding errors (one such error can be found in file /txt/pl/ep-09-10-22-009.txt)
    # Loop over entire input file, extract chapterIDs, SpeakerIDs and language codes (the latter happens in write_metadata_to_df)
    for line in fl:
      if not prev_line == None:
        current_line = prev_line.strip()
        next_line = line.strip()
        chapterMatch = chapterTag.search(current_line)
        if chapterMatch:
          chapter_ID = chapterMatch.group(1)
        speakerMatch = speakerTag.search(current_line)
        if speakerMatch:
          write_metadata_to_df(current_line, next_line, speakerMatch, filename_base)
      prev_line = line.strip()
    
    # After reaching the last line of file (stored as prev_line), check once again whether there is a language tag in last line.
    # This time, next_line is empty because it is the end of file, therefore we pass '' to function write_metadata_to_df().
    if prev_line == None:
      prev_line = ''
    chapterMatch = chapterTag.search(prev_line)
    if chapterMatch:
      chapter_ID = chapterMatch.group(1)
    speakerMatch = speakerTag.search(prev_line)
    if speakerMatch:
      write_metadata_to_df(prev_line, '', speakerMatch, filename_base) # Here prev_line is the last line of input file and next_line is '' because of EOF
##### END OF FUNCTION DECLARATION



def group_speakers(all_name_forms):
  """ Apply a simple heuristic to group speaker names irrespective of discrepancies in writing, i.e. identify "John Doe" and "Doe John" as same speaker.
  The function creates for each statement a dictionary that contains short forms of normalised names (4 characters long) as keys and the respective counts as values.
  
  Arguments:
    all_name_forms (dict) -- Dictionary holding all names encountered for a speaker turn as keys and corresponding counts across all language files as values
      (e.g. {'Jim Higgins': 1, 'Higging': 2}

  Returns:
    speakers_summary (dict) -- Dictionary holding all normalised short forms as keys and corresponding counts as values Nothing; instead, it writes metadata directly to data frame speaker_list.
      (e.g. {'jimh': 1, 'higg': 2}

  """
  speakers_summary = {}

  if len(all_name_forms) == 1:
    for k, v in all_name_forms.items():
      speakers_summary[normalise_name(k)[0:4]] = v #[0:3] to change length of normalised name tag to 4 instead of 3
  elif len(all_name_forms) < 1:
    speakers_summary = {}

  else:
    pairwise_name_matches = [] # this list stores pairwise tuples that indicate which two normalised short names belong together 
    names = list(all_name_forms.items()) # list of tuples containing speakername and count
    for i in range(len(names)):
      names[i] = (normalise_name(names[i][0]), names[i][1])
      if names[i][0][0:4] not in speakers_summary: #[0:3] to change length of normalised name tag to 4 instead of 3
        speakers_summary[names[i][0][0:4]] = int(names[i][1]) #[0:3] to change length of normalised name tag to 4 instead of 3
      else:
        speakers_summary[names[i][0][0:4]] += names[i][1] #[0:3] to change length of normalised name tag to 4 instead of 3
    names_copy = list(names)

    # iterate over names and names_copy to find which pairs of names belong together
    for n in names:
      names_copy.remove(n)
      name = n[0]
      count = n[1]
      for n_c in names_copy:
        name_copy = n_c[0]        
        if name[0:4] in name_copy[0:15]: #name_copy[0:15] restricts the full string to a 25 character version in order to avoid inflation of matches in very long names #[0:3] to change length of normalised name tag to 4 instead of 3
          if {name[0:4], name_copy[0:4]} not in pairwise_name_matches and len({name[0:4], name_copy[0:4]}) >1: #[0:3] to change length of normalised name tag to 4 instead of 3
            pairwise_name_matches.append({name[0:4], name_copy[0:4]}) #[0:3] to change length of normalised name tag to 4 instead of 3
      names_copy.append(n)
      ## At this point, pairwise_name_matches contains all 2-tuples of normalised short names that belong together
    # Now iterare over pairwise_name_matches to find names that ocur several times across tuples
    # Such names will be the nucleus to group all other tuples that contain such shared names
    # These names will be stored in shared_names, with the shared names as keys and all names belonging to this shared name as values
    name_ocurrences = {}
    shared_names = {}

    # iterate over pairwise_name_matches and count in dictionary name_ocurrences how many times each element of each parwise_name_match occurs 
    for pnm in pairwise_name_matches:
      for name_short in pnm:
        if name_short in name_ocurrences:
          name_ocurrences[name_short] += 1
        else:
          name_ocurrences[name_short] = 1
    # iterate over name_ocurrences (holding nr. of occurrences of each short name in pairwise matches) to find all short names that ocurr more than once and hence will form nuclei to group all names belonging to them
    for k,v in name_ocurrences.items():
      if v > 1:
        shared_names[k] = set()
    
    for sn in shared_names:
      for pnm in pairwise_name_matches:
        if sn in pnm:
          shared_names[sn] = shared_names[sn] | pnm
    # At this point, shared_names contains all names that are being shared across sets as keys and all names that belong to them as values. The keys are thus the nuclei that group all names belonging to them

    # Update shared_names by finding those pairwise name matches that are not yet included in shared_names
    for pnm in pairwise_name_matches:
      if all(name_short not in shared_names.keys() for name_short in pnm):
        additionalkey = next(iter(pnm))
        shared_names[additionalkey] = pnm
    # At this point, shared_names contains groups of names that belong together. The groups are stored as values and the keys are represented by the nulei that were used to group names around them (i.e. names that are being shared across pairwise name matches)
       #  if not all(only_roman_chars(k) for k in d.keys())

    # Now iterate over all group of names that belong together (stored as values in shared_names) to calculate aggregate sum of ocurrences for each group of names
    duplicatecheck = []
    for namegroup in shared_names.values():
      if not namegroup in duplicatecheck:
        duplicatecheck.append(namegroup)
        joint_count = 0
        max_val = 0
        max_key = ''
        for nm in namegroup:
          joint_count += speakers_summary[nm]
          if speakers_summary[nm] > max_val:
            max_key = nm
            max_val = speakers_summary[nm]
          speakers_summary[nm] = 0
        speakers_summary[max_key] = joint_count
    speakers_summary_copy = {}
    for k, v in speakers_summary.items():
      if v != 0:
        speakers_summary_copy[k] = v
    speakers_summary = speakers_summary_copy
  return(speakers_summary)
##### END OF FUNCTION DECLARATION



def normalise_name(name):
  """ Normalise speaker name by latinising Cyrillic/Greek characters and unifying multilingual denominations of 'president'.
    
  Arguments:
    name (str) -- The name of the speaker.

  Returns:
    norm (str) -- The normalised form of the name.
    
  """
  if exceptions_nonroman.search(name):
    name = latinise_name(name)
  if president.search(name):
    norm = "prsd"
  else:
    norm = unidecode(name).lower().translate(str.maketrans({a:None for a in punctuation})).replace(' ','')
  if len(norm) < 1:
    norm = "xxxx"
  return(norm)
##### END OF FUNCTION DECLARATION

def latinise_name(name):
  """ Convert Cyrillic/Greek names to Latin alphabet form.
    
  Arguments:
    name (str) -- Name of speaker.

  Returns:
    name_latinised (str) -- Latinised form of the name.
    
  """
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
  name_latinised = pattern.sub(lambda x: replacements[x.group()], name)
  return(name_latinised)
##### END OF FUNCTION DECLARATION



def match_speakers(all_names_normalised):
  """ Determine whether speaker names for each statement ate matching or contradictory. If contradictory,
    the speaker names are regarded as umbiguous if one of the name IDs accounts for at least 70% of all name IDs for given speaker turn.
    
  Arguments:
    all_name_forms (dict) -- Dictionary holding all normalised name short forms encountered for a speaker turn as keys and corresponding counts across all language files as values
      (e.g. {'jimh': 1, 'higg': 7}

  Returns:
    speaker (str) -- The normalised four-character short form speaker name.
      (e.g. 'higg')

  """
  values = list(all_names_normalised.values())
  keys = list(all_names_normalised.keys())
  
  if len(keys) == 0:
    speaker = "xNAN"
  elif len(keys) == 1:
    speaker = keys[0]
  elif len(keys) == 2:
    if 'prd' in keys:
      speaker = "xAMB"
    else:
      sum_values = sum(values)
      max_value = max(values)
      if max_value/sum_values >= 0.9:
        if string_difference(keys[0], keys[1]) <= 1:
          max_key = keys[values.index(max_value)]
          speaker = max_key
        else:
          speaker = "xAMB"     
      else:
        speaker = "xAMB"
  else:
    speaker = "xAMB"
  return(speaker)



def string_difference(s1, s2):
  s1 = s1 + "#" * (4-len(s1)) #make sure that s1 is 3 (or 4 according to length of nomalised tag) characters long: add # to s if s shorter than 3
  s2 = s2 + "#" * (4-len(s2))
  diff = 0
  for i in range (len(s1)):
    if s1[i] != s2[i]:
      diff += 1
  return(diff)
##### END OF FUNCTION DECLARATION  



def language_vote(originalLanguages, additionalLanguages):
  """ Determine language of speaker turn by voting among multiple language tags found in source files.
    
  Arguments:
    originalLanguages (dict) -- Dictionary storing language codes identified from XML metadata tags across all source files.
      Dictionary keys represent language codes, values represent number of occurrences of each language code.
    additionalLanguages (dict) -- Dictionary storing language codes identified from language codes in lines following XML metadata tags across all source files.
      Dictionary keys represent language codes, values represent number of occurrences of each language code.

  Returns:
    vote (str) -- Language code determined by voting procedure.
    
  """

  # 1) If no language tag in originalLanguages: vote = xNAN
  # 2) If 1 language tag in originalLanguages: vote = the only language tag in dictionary keys of originallanguages
  # 3) if >1 language tags in originalLanguages:
  #    - if only one maximum count then chose language that has maximum number of occurrences
  #    - if >1 maximum counts then add counts from additional language tag (if applicable) to determine maximum count language
  
  if len(originalLanguages) > 1:
    maxkeys = [k for k, v in originalLanguages.items() if v == max(originalLanguages.values())]
    if len(maxkeys) == 1:
      vote = maxkeys[0]
    else:
      sums = {}
      for k in maxkeys:
        sums[k] = originalLanguages[k]
      for k in maxkeys:
        if k in additionalLanguages.keys():
          sums[k] = sums[k] + additionalLanguages[k]
      vote = str(max(sums, key=sums.get))
  elif len(originalLanguages) == 1:
    for k in originalLanguages.keys():
      x = k
    vote = str(x)

  else:
    if args.additionalLanguageTags:
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
### END OF FUNCTION DECLARATION



def write_metadata_to_df(line, nextline, speakerMatch, filename_base):
  """ Write metadata identified within function analyse_sourcefile(fn) to data frame spaker_list.
    
  Arguments:
    line (str) -- Current line of EuroParl source file being read by function analyse_sourcefile(fn).
    nextline (str) -- Next line of EuroParl source file being read by function analyse_sourcefile(fn).
    speakerMatch (:obj: 'SRE_Match object) -- Regex match object that stores XML metadata about speaker turn.
    filename_base (str) -- Basename of EuroParl source file.

  Returns:
    Nothing; instead, it writes metadata directly to data frame speaker_list.
    
  """
  speaker_ID = speakerMatch.group(1)
  unique_file_id = filename_base + "|" + speaker_ID
  nameMatch = nameTag.search(line)
  # If speaker name is found in XML tag, retrieve it from regex pattern and pass it to function normalise(name(name).
  if nameMatch:
    name = nameMatch.group(1).partition('(')[0].strip()
    name_normalised = normalise_name(name)
  # If no speaker name found in XML tag, set normalised name to dummy value 'nnnn'.
  else:
    name = ""
    name_normalised = 'nnnn'
    
  languageMatch = languageTag.search(line)
  if languageMatch:
    lang = languageMatch.group(1)
  else:
    lang = ""
  
  # Search additional language tag (a two-letter uppercase code in parenthesis) in line following
  # the current line containing XML metadata tag.
  additional_lang_tag = langcode.search(nextline)
  
  #  Make sure no language code exception of type "(ES) Nr. 123" in line following XML tag is mistakingly taken as language code
  #  where, in fact, (ES) is only an abbreviation for European Commission in several Slavic languages (eg. CS, SK).
  if additional_lang_tag and not langcode_exception.search(nextline):
    additional_lang_tag = additional_lang_tag.group(1)
  else:
    additional_lang_tag = ""

  # If speakerID is already stored in data frame, update language code if provided
  if unique_file_id not in speaker_list.index:
    speaker_list.loc[unique_file_id] = [{}, {}, '', {}, '', {}]  # 'ID', 'NAMES_FULL_COUNT', 'NAMES_NORMALISED_SUMMARY', 'NAMES_MATCHING', 'ORIGINAL_LANGUAGE', 'SL', 'ADDITIONAL_LANGUAGE', 'SL2' # speaker_ID as first item was deleted
    if len(name) > 0:
      speaker_list.loc[unique_file_id].loc['NAMES_FULL_COUNT'][name] = 1
    if len(lang) > 0:
      speaker_list.loc[unique_file_id].loc['ORIGINAL_LANGUAGE'][lang] = 1
    if len(additional_lang_tag) > 0:
      speaker_list.loc[unique_file_id].loc['ADDITIONAL_LANGUAGE'][additional_lang_tag] = 1
  else:
    if len(name) > 0:
      if name not in speaker_list.loc[unique_file_id].loc['NAMES_FULL_COUNT'].keys():
        speaker_list.loc[unique_file_id].loc['NAMES_FULL_COUNT'][name] = 1
      else:
        speaker_list.loc[unique_file_id].loc['NAMES_FULL_COUNT'][name] += 1
    if len(lang) > 0:
      if lang not in speaker_list.loc[unique_file_id].loc['ORIGINAL_LANGUAGE'].keys():
        speaker_list.loc[unique_file_id].loc['ORIGINAL_LANGUAGE'][lang] = 1
      else:
        speaker_list.loc[unique_file_id].loc['ORIGINAL_LANGUAGE'][lang] += 1
    if len(additional_lang_tag) > 0:
      if additional_lang_tag not in speaker_list.loc[unique_file_id].loc['ADDITIONAL_LANGUAGE'].keys():
        speaker_list.loc[unique_file_id].loc['ADDITIONAL_LANGUAGE'][additional_lang_tag] = 1
      else:
        speaker_list.loc[unique_file_id].loc['ADDITIONAL_LANGUAGE'][additional_lang_tag] += 1    
### END OF FUNCTION DECLARATION



def extract_comparable_nontranslated(statements_nontranslated, tl):
  """ Extract non-translated comparable statements from EuroParl source files.
    
  Arguments:
    statements_nontranslated (dict) -- The statements in the given language.
      Dictionary keys: File identifiers of EuroParl source files (e.g. 11-04-06-009).
      Dictionary values: Speaker IDs (e.g. 158) that point to translated statements in source files..
  tl (str) - Two-letter language identifier.

  Returns:
    Nothing; instead, it calls function write_statements_to_txt(fn_in, fn_out, ids) to write extracted statements to output files.
  
  """
  for filename in statements_nontranslated.keys():
    # Generate file names for input and output files.
    # For each extracted statement, a new outputfile will be created.
    # Name of output file contains the following:
    #    1) Europarl filename (without prefix ep-)
    #    2) Statement ID
    #    3) language code.
    fname_input = (inDir + "/" + tl.lower() + "/ep-" + filename + ".txt").replace('//', '/')
    fname_output = (outDir + "/comparable/non-translated/" + tl + "/" + filename + "_" + "xIDx" + "_" + tl.lower() + ".txt").replace('//', '/')
    
    if os.path.exists(fname_input):
      create_folders_comparable_nontranslated(outDir, tl)
      # Write to output director one statement file for each non-translated statement in given language
      # from the EuroParl source file by calling function write_statements_to_txt(in, out, ids)
      if args.debug:
        logfile.write("Extracting non-translated comparable text from\t%s (Turns: %s)\n" %(fname_input, " ".join(statements_nontranslated[filename])))
      write_statements_to_txt(fname_input, fname_output, statements_nontranslated[filename]) #3rd argument = statement ID
##### END OF FUNCTION DECLARATION




def create_folders_comparable_nontranslated(outDir, tl):
  """ Create subfolders in output folder for each language of comparable non-translated corpus.
    
  Arguments:
    outDir (str) -- Path to output folder.
    tl (str) -- Two-letter target language identifier.

  Returns:
    Nothing; instead, it creates the subfolders for each language.
  
  Raises:
    OSError
    
  """
  try:
    os.makedirs(outDir + "/comparable/non-translated/" + tl)
  except OSError:
    pass
##### END OF FUNCTION DECLARATION



def write_statements_to_txt(filename_input, filename_output, ids):
  """ Write statements extracted by function extract_comparable_nontranslated or extract_comparable_translated to output files.
    
  Arguments:
    filename_input (str) -- Name of EuroParl source file.
    filename_output (str) -- Name of output file.
    ids (str) -- List of IDs (strings) identyfing speaker turns to be written to output file.

  Returns:
    Nothing; instead, it writes the output files.
  """
  
  # From list of IDs create regex pattern to match speaker IDs for statemens to be extracted.
  speakerID_pattern = re.compile(r'<SPEAKER ID="?(' + '|'.join(ids) +')"? ')

  # Open EuroParl source file and read it linewise to locate statements to be extracted according to speakerID
  # All of these statements will be written to separate output files.
  with open(filename_input, 'rt', encoding='utf-8', errors='ignore') as fl_in:
    prev_line = None
    do_extraction = False
    for line in fl_in:
      if not prev_line == None:
        current_line = prev_line.strip()
        next_line = line.strip()
        # If regex matches speaker ID in current source file line then write current line to output file and write all subsequent source line lines
        # to output file until the occurrence of next XML metadata tag.
        if speakerID_pattern.search(current_line):
          linecounter = 0 # Count lines for subseqeunt deletion of files that do not contain any text except for XML metadata tags. 
          statementID = speakerID_pattern.search(current_line).group(1)
          fname_out = filename_output.replace('xIDx', statementID) # Generate output file name
          open(fname_out, mode='w').close() # Make sure outputfile exists and is empty if already existent.
          fl_out = open(fname_out, mode='a', encoding='utf-8')
          do_extraction = True          
        if do_extraction == True: 
          if isCleanOutput:
            current_line = clean_line(current_line)
          if len(current_line) > 0:
            fl_out.write(current_line+"\n")
            linecounter += 1
        if do_extraction == True and xmlTag.search(next_line):
          do_extraction = False
          fl_out.close()
          # Remove file if it is empty or consists only of XML meta tag
          if linecounter < min_lines_per_file:
            os.remove(fname_out)
      prev_line = line.strip()
    current_line = prev_line
    next_line = ''
    if do_extraction == True:
      if args.cleanOutput:
        current_line = clean_line(current_line)
      if len(current_line) > 0:
        fl_out.write(current_line)
        linecounter += 1
      fl_out.close()
      # Remove file if it is empty of consists only of XML meta tag
      if linecounter < min_lines_per_file:
        os.remove(fname_out)
##### END OF FUNCTION DECLARATION



def clean_line(txt):
  """ Remove XML metadata tag and/or additional language tag from current txt.
    
  Arguments:
    txt (str) -- Text to be cleaned.

  Returns:
    txt(str) -- The cleaned text.
  """
  if isCleanOutput == "lang" or isCleanOutput == "both":
    if langcode.search(txt) and not langcode_exception.search(txt):
      txt = re.sub(langcode, '', txt)
  if isCleanOutput == "speaker" or isCleanOutput == "both":
    if xmlTag_all.search(txt):
      txt = ""
  txt = re.sub('\s{2,}', ' ', txt)    
  return(txt.strip())
##### END OF FUNCTION DECLARATION



def extract_comparable_translated(statements_sourcelanguage, sl, tl):
  """ Extract translated comparable statements from EuroParl source files.
    
  Arguments:
    statements_sourcelanguage (dict) -- The statements in the source language.
      Dictionary keys: File identifiers of EuroParl source files (e.g. 11-04-06-009).
      Dictionary values: Speaker IDs (e.g. 158) that point to translated statements in source files..
    sl (str) -- Two-letter source language identifier.
    tl (str) -- Two-letter target language identifier.

  Returns:
    Nothing; instead, it calls function write_statements_to_txt(fn_in, fn_out, ids) to write extracted statements to output files.
  
  """
  for identifier in statements_sourcelanguage.keys():
    # Generate filenames for input and output files.
    # Input: EuroParl source file in given language with corresponding identifier from statements_translated.
    # Output file contains:
    #    1) Europarl identifier (without prefix ep-)
    #    2) Statement ID 
    #    3) Target language code
    fname_input = (inDir + "/" + tl.lower() + "/ep-" + identifier + ".txt").replace('//', '/')
    fname_output = (outDir + "/comparable/translated/" + tl + "/" + sl + "-" + tl + "/" + identifier + "_" + "xIDx" + "_" + tl.lower() + ".txt").replace('//', '/')
    
    if not os.path.exists(fname_input):
      continue
    create_folders_comparable_translated(outDir, sl, tl)
    if args.debug:
      logfile.write("Extracting translated comparable text from\t%s (Turns: %s)\n" %(fname_input, " ".join(statements_sourcelanguage[identifier])))
    write_statements_to_txt(fname_input, fname_output, statements_sourcelanguage[identifier])
##### END OF FUNCTION DECLARATION



def create_folders_comparable_translated(outDir, sl, tl):
  """ Create subfolders in output folder for each language combination of comparable translated corpus.
    
  Arguments:
    outDir (str) -- Path to output folder.
    sl (str) -- Two-letter source language identifier.
    tl (str) -- Two-letter target language identifier.

  Returns:
    Nothing; instead, it creates the subfolders for each language combination.
  
  Raises:
    OSError
    
  """
  try:
    os.makedirs(outDir + "/comparable/translated/" + tl + "/" + sl + "-" + tl)
  except OSError:
    pass
##### END OF FUNCTION DECLARATION



def extract_parallel(statements_sourcelanguage, sl, tl):
  """ Extract parallel statements from EuroParl source files.
    
  Arguments:
    statements_sourcelanguage (dict) -- The statements in the source language.
      Dictionary keys: File identifiers of EuroParl source files (e.g. 11-04-06-009).
      Dictionary values: Speaker IDs (e.g. 158) that point to translated statements in source files..
    sl (str) -- Two-letter source language identifier.
    tl (str) -- Two-letter target language identifier.

  Returns:
    Nothing; instead, it calls function write_statements_to_txt(fn_in, fn_out, ids) to write non-aligned extracted statements to output files or
    function align_statements(fn_in_sl, fn_in_tl, fn_out_generic, identifiers, sl, tl) to write aligned output files.
  
  """
  create_folders_parallel(outDir, sl, tl)
  for identifier in statements_sourcelanguage.keys():
    # Generate filenames for input and output.
    # Input: TL file with corresponding identifier from statements_sourcelanguage.
    # Outputfile contains:
    #    1) Europarl identifier (without prefix ep-)
    #    2) Statement ID
    #    3) target language code
    fname_input_sl = (inDir + "/" + sl.lower() + "/ep-" + identifier + ".txt").replace('//', '/')
    fname_input_tl = (inDir + "/" + tl.lower() + "/ep-" + identifier + ".txt").replace('//', '/')
    
    # Continue with next iteration of loop if input file and/or output file non-existent in input folder
    if not (os.path.exists(fname_input_sl) and os.path.exists(fname_input_tl)):
      continue
    
    if outputToTxt:
      fname_output_sl = (outDir + "/parallel/" + sl + "-" + tl + "/" + sl + "_sl/" + identifier + "_" + "xIDx" + "_" + sl.lower() + ".txt").replace('//', '/')
      fname_output_tl = (outDir + "/parallel/" + sl + "-" + tl + "/" + tl + "_tl/" + identifier + "_" + "xIDx" + "_" + tl.lower() + ".txt").replace('//', '/')    
      
      write_statements_to_txt(fname_input_sl, fname_output_sl, statements_sourcelanguage[identifier])
      write_statements_to_txt(fname_input_tl, fname_output_tl, statements_sourcelanguage[identifier])

      dirname_output_sl = (outDir + "/parallel/" + sl + "-" + tl + "/" + sl + "_sl/").replace('//', '/')
      dirname_output_tl = (outDir + "/parallel/" + sl + "-" + tl + "/" + tl + "_tl/").replace('//', '/')    

    if outputToTab or outputToTmx:
      fname_output_generic = (outDir + "/parallel/" + sl + "-" + tl + "/xyz/" + identifier + "_" + "xIDx" + "_" + sl.lower() + "-" + tl.lower() + ".xyz").replace('//', '/')
      align_statements(fname_input_sl, fname_input_tl, fname_output_generic, statements_sourcelanguage[identifier], sl, tl)

  # Remove spurious monolingual files from language-pair-specific subfolder of parallel corpus
  if outputToTxt:
    clean_parallel_texts(sl.lower(), dirname_output_sl, tl.lower(), dirname_output_tl)
##### END OF FUNCTION DECLARATION



def create_folders_parallel(outDir, sl, tl):
  """ Create subfolders in output folder for each language combination of parallel corpus.
    
  Arguments:
    outDir (str) -- Path to output folder.
    sl (str) -- Two-letter source language identifier
    tl (str) -- Two-letter target language identifier

  Returns:
    Nothing; instead, it creates the subfolders for each language combination.
  
  Raises:
    OSError
    
  """
  if outputToTmx:
    try:
      os.makedirs(outDir + "/parallel/" + sl + "-" + tl + "/tmx")
    except OSError:
      pass
    
  if outputToTab:
    try:
      os.makedirs(outDir + "/parallel/" + sl + "-" + tl + "/tab")
    except OSError:
      pass
    
  if outputToTxt:
    try:
      os.makedirs(outDir + "/parallel/" + sl + "-" + tl + "/" + sl + "_sl")
      os.makedirs(outDir + "/parallel/" + sl + "-" + tl + "/" + tl + "_tl")
    except OSError:
      pass
##### END OF FUNCTION DECLARATION


  
def align_statements(filename_in_sl, filename_in_tl, filename_out_generic, ids, sl, tl):
  """ Align parallel statements using third-party implementation of Gale-Church algorithm.
  
  Arguments:
    filename_in_sl (str) -- Name of EuroParl source language input file.
    filename_in_tl (str) -- Name of EuroParl target language input file.
    filename_out_generic (str) -- Generic placeholder for output file in aligned TAB or TMX format. 
    ids (str) -- List of IDs (e.g. ((e.g. 135, 058,...)) identifying speaker turns to be written to output file.
    sl (str) -- Two-character source language identifier.
    tl (str) -- Two-character target language identifier.

  Returns:
    Nothing; instead, it writes aligned output files in specified format.
  """
    
  # From list of IDs create regex pattern to match speaker IDs for parallel statements to be extracted
  speakerID_pattern = re.compile(r'<SPEAKER ID="?(' + '|'.join(ids) +')"? ')
  
  sentences_sl = {} # Dictionary storing source language sentences of bitext (Keys: names of output file, values:the sentences)
  sentences_tl = {} # Dictionary storing target language sentences of bitext (Keys: names of output file, values:the sentences)
  
  # Loop linewise over EuroParl input file for source language to extract statements that subsequently are to be aligned.
  # All of these statements will be written to separate aligned output files
  with open(filename_in_sl, 'rt', encoding='utf-8', errors='ignore') as fl_in_sl:    
    prev_line = None
    do_extraction = False
    for line in fl_in_sl:
      if not prev_line == None:
        current_line = prev_line.strip()
        next_line = line.strip()
        
        # If regex matches speaker ID in current line create list that contains paragraph markers at beginning and end (<P>) and
        # the sentences of speaker turn (one sentence per list element).
        # All lines from speaker ID match until occurrence of a next XML metadata tag will be stored in list.
        if speakerID_pattern.search(current_line):
          statementID = speakerID_pattern.search(current_line).group(1)
          fname_out = filename_out_generic.replace('xIDx', statementID)
          sentences_sl[fname_out] = ['<P>', current_line, '<P>'] # ['<P>', '<END_SL>'] 
          do_extraction = True
        if do_extraction == True and not speakerID_pattern.search(current_line):
          # Add current line to penultimate position of SL sentence list (the last position is reserved for <P>) 
          sentences_sl[fname_out].insert(-1, current_line)
        # Stop extracting lines from source file if next line contains XML metadata tag
        if do_extraction == True and xmlTag.search(next_line):
          do_extraction = False
      prev_line = line.strip()
    current_line = prev_line
    next_line = ''
    if do_extraction == True:
      sentences_sl[fname_out].insert(-1, current_line)
  fl_in_sl.close()
  ## Extraction of SL sentences to dictionary sentences_sl completed.


  # Loop linewise over EuroParl input file for target language to extract statements that subsequently are to be aligned.
  # All of these statements will be written to separate aligned output files  with open(filename_in_tl, 'rt', encoding='utf-8', errors='ignore') as fl_in_tl:
  with open(filename_in_tl, 'rt', encoding='utf-8', errors='ignore') as fl_in_tl:
    if args.debug:
      logfile.write("\n####################################### NEXT FILE ########################\n\nOPENING TL INPUT FILE FOR ALIGNMENT:\t%s\n\n" %(filename_in_tl))
    prev_line_tl = None
    do_extraction = False
    for line_tl in fl_in_tl:
      if not prev_line_tl == None:
        current_line_tl = prev_line_tl.strip()
        next_line_tl = line_tl.strip()
        
        # If regex matches speaker ID in current line create list that contains paragraph markers at beginning and end (<P>) and
        # the sentences of speaker turn (one sentence per list element).
        # All lines from speaker ID match until occurrence of a next XML metadata tag will be stored in list.
        if speakerID_pattern.search(current_line_tl):
          statementID = speakerID_pattern.search(current_line_tl).group(1)
          fname_out = filename_out_generic.replace('xIDx', statementID)
          
          sentences_tl[fname_out] = ['<P>', current_line_tl ,'<P>'] # ['<P>', '<END_TL>'] 
          do_extraction = True
          
        if do_extraction == True and not speakerID_pattern.search(current_line_tl):
          sentences_tl[fname_out].insert(-1, current_line_tl)
        if do_extraction == True and xmlTag.search(next_line_tl):
          do_extraction = False

      prev_line_tl = line_tl.strip()
    current_line_tl = prev_line_tl
    next_line_tl = ''
    if do_extraction == True:
      sentences_tl[fname_out].insert(-1, current_line_tl)
  fl_in_tl.close()
  ## Extraction of TL sentences to dictionary sentences_tl completed.

  # Perform sentence alignment:
  # Loop over dictionary of SL sentences (accessible via output file names) in order to:
  #    1)  remove adjacent paragraph markers in sentence lists (e.g. '<P>', '<P>')
  #    2)  remove segments (i.e. all sentences between two <P> marks) from both SL and TL sentence list if corresponding segments are disproportional in terms of nubers of sentences
  #        (This is needed to reduce number of alignment errors, if e.g. the SL segment consists of 1 sentence and the corresponding TL segment of 5 sentences).
  #    3)  Align SL with TL segments using Gale-Church algorithm
  #    4) Post-process resulting alignments by merging empty alignments at segment beginning or end.
  for fn in sentences_sl.keys():

    if not (fn in sentences_tl.keys() and len(sentences_sl[fn]) > 3 and len(sentences_tl[fn]) > 3):
      continue
    if args.debug:
      logfile.write("OUTPUT FILE:\t%s\n\n> SL Segments Unprocessed:\n%s\n\n" %(fn, sentences_sl[fn]))

    # Retrieve metadata about speaker turn and pop it from list of sentences 
    metadata = sentences_sl[fn].pop(1)
    sentences_tl[fn].pop(1)
    
    # Make sure there are no multiple adjacent <P> marks in the SL/TL sentence lists
    sentences_sl[fn] = [a for a,b in zip(sentences_sl[fn], sentences_sl[fn][1:]+[not sentences_sl[fn][-1]]) if a != b or a != "<P>"]
    sentences_tl[fn] = [a for a,b in zip(sentences_tl[fn], sentences_tl[fn][1:]+[not sentences_tl[fn][-1]]) if a != b or a != "<P>"]
      
    # Continue with next iteration (i.e. next file) if number of paragraphs in speaker turn differs across SL and TL
    if sentences_sl[fn].count("<P>") != sentences_tl[fn].count("<P>"):
      continue
    
    sentences_sl[fn], sentences_tl[fn] = remove_unevenly_long_segments(sentences_sl[fn], sentences_tl[fn])
    
    # Continue with next iteration (i.e. file) if sentence list consists only of one beginning and one end paragraph mark (i.e. if length of sentene list < 3)
    if len(sentences_sl[fn]) < 3:
      continue

    # Run Gale-Church alignment algorithm to align SL sentences with TL sentences
    sl_sents, tl_sents = gale_church_alignment(sentences_sl[fn], sentences_tl[fn])
    # Merge adjacent empty alignments at segment beginning/end to avoid zero-alignments
    sl_sents, tl_sents = postprocess_alignments(sl_sents, tl_sents)
    
    sl_sents = sl_sents[1:-1] # Remove first and last element, i.e. <P> marks
    tl_sents = tl_sents[1:-1] # Remove first and last element, i.e. <P> marks
    
    if isCleanOutput:
      for i in range(len(sl_sents)):
        sl_sents[i] = clean_line(sl_sents[i])
        tl_sents[i] = clean_line(tl_sents[i])
    
    if outputToTab:
      write_to_tab(fn, metadata, sl_sents, tl_sents)  
    if outputToTmx:
      write_to_tmx(fn, sl, tl, sl_sents, tl_sents)
##### END OF DECLARATION OF FUNCTION align_statements()


def write_to_tab(fn, metadata, sl_sents, tl_sents):
  """ Write aligned sentences to output file (aligned SL and TL sentences separated by tabulator, one alignment per line).
  
  Arguments:
    fn (str) -- Generic placeholder name of aligned output file (e.g. out/parallel/PL-ES/xyz/07-11-14-013_395_pl-es.xyz)
    metadata (str) -- Metadata XML tag containing speaker and language information
    sl_sents (list) -- SL sentences, equal in length as tl_sents; aligned SL/TL sentences are matched by list index.
    tl_sents (list) -- TL sentences, equal in length as sl_sents; aligned SL/TL sentences are matched by list index.

  Returns:
    Nothing; instead, it writes sentence-aligned output files in tab-separated output format.
  """
  fn_tab = fn.replace("xyz", "tab") # Replace generic output name with output name for tab format
  open(fn_tab, mode='w').close() # make sure output file exists
  with open(fn_tab, mode='a', encoding='utf-8') as fl_out_tab:
    if not (isCleanOutput == "speaker" or isCleanOutput == "both"):
      fl_out_tab.write("%s\n" %(metadata))
    for i in range(len(sl_sents)):
      if sl_sents[i] == "<P>":
        fl_out_tab.write("<P>\n")
      else:
        # Do not output 1:0 or 0:1 alignments , i.e. if aligned segment is empty in either SL or TL
        if len(sl_sents[i]) > 0 and len(tl_sents[i]) > 0:
          fl_out_tab.write("%s\t%s\n" %(sl_sents[i], tl_sents[i]))
##### END OF FUNCTION DECLARATION



def write_to_tmx(fn, sl, tl, sl_sents, tl_sents):
  """ Write aligned sentences to TMX output file.
  
  Arguments:
    fn (str) -- Generic placeholder name of aligned output file (e.g. out/parallel/PL-ES/xyz/07-11-14-013_395_pl-es.xyz)
    sl (str) -- Two-character source language code.
    tl (str) -- Two-character target language code.
    sl_sents (list) -- SL sentences, equal in length as tl_sents; aligned SL/TL sentences are matched by list index.
    tl_sents (list) -- TL sentences, equal in length as sl_sents; aligned SL/TL sentences are matched by list index.

  Returns:
    Nothing; instead, it writes sentence-aligned output files in tab-separated output format.
  """
  fn_tmx = fn.replace("xyz", "tmx")
  date = datetime.now().isoformat()
  open(fn_tmx, mode='w').close() # make sure outputfile exists
  with open(fn_tmx, mode='a', encoding='utf-8') as fl_out_tmx:
    fl_out_tmx.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n"\
                     "<tmx version=\"1.4\">\n"\
                     " <header creationtool=\"EuroParlExtract\" creationtoolversion=\"1.0\" creationdate=\"%s\" segtype=\"sentence\" "\
                     "adminlang=\"en-GB\" srclang=\"%s\" datatype=\"plaintext\">\n"\
                     " </header>\n"\
                     " <body>\n"\
                     %(date, sl.lower()))
    for i in range(len(sl_sents)):

      # Continue with next iteration (i.e. next sentence) if:
      #    - the sentence == <P>, or
      #    - either of SL or TL sentences is empty (i.e. if we have a zero alignment)
      if sl_sents[i] == "<P>" or len(sl_sents[i]) == 0 or len(tl_sents[i]) == 0:
        continue
   
      fl_out_tmx.write("  <tu>\n"\
                       "   <tuv xml:lang=\"%s\"><seg>%s</seg></tuv>\n"\
                       "   <tuv xml:lang=\"%s\"><seg>%s</seg></tuv>\n"\
                       "  </tu>\n"\
                       %(sl.lower(), sl_sents[i], tl.lower(), tl_sents[i]))
    # Close body and tmx tags upon loop over entire file.
    fl_out_tmx.write(" </body>\n"\
                     "</tmx>")
##### END OF FUNCTION DECLARATION



def postprocess_alignments(sl_sents, tl_sents):
  """ Merge adjacent sentences at beginning/end of paragraph if corresponding aligned counterpart is empty.
  The two input lists must be equal in length and have paragraph marks (<P>) in exactly the same positions.
    
  Arguments:
    sl_sents (list) -- Source language sentences, including, paragraph markers.
    tl_sents (list) -- Source language sentences, including, paragraph markers.

  Returns:
    sl_sents (list) -- Postprecessed list of source language sentences, including paragraph markers.
    tl_sents (list) -- Postprecessed list of target language sentences, including paragraph markers.

  """
  # Iterate over list of source language sentences using while; for each SL sentence check if corresponding TL sentence
  # at same position is empty. If either SL or corresponding TL sentence at given position is empty AND the SL-TL sentence pair is at paragraph BEGINNING (i.e. if previous list item == "<P>")
  # then concatenate current sentence with next sentence in both SL and TL as well as remove the next sentence from the list. Subsequently, go back two positions in list and continue iteration.
  # Example:
  # SL = ['<P>', 'a', 'b', 'c', 'd', '<P>'] => becomes    ['<P>', 'a b c', 'd', <P>]
  # TL = ['<P>', 'A B C', '', '', 'D', '<P>'] => becomes  ['<P>', 'A B C', 'd', <P>]
  i = 0
  while i < len(sl_sents)-1:
    if (len(sl_sents[i]) == 0 or len(tl_sents[i]) == 0) and prevIsParagraph == True:
      sl_sents[i] = (sl_sents[i] + " " + sl_sents[i+1]).strip()
      sl_sents.pop(i+1)
      tl_sents[i] = (tl_sents[i] + " " + tl_sents[i+1]).strip()
      tl_sents.pop(i+1)
      i -= 1
    if sl_sents[i] == "<P>":
      lastparindex = i
      prevIsParagraph = True
    else:
      prevIsParagraph = False
    i += 1

  # Now the same for sentences directly BEFORE paragraph ends:
  # Iterate over list of source language sentences using while and for each SL sentence check if corresponding TL sentence
  # at same position is empty. If either SL or corresponding TL sentence at given position is empty AND the SL-TL sentence pair is at paragraph END (i.e. if previous list item == "<P>")
  # then concatenate previous sentence with current sentence in both SL and TL as well as remove the current sentence from the list. Subsequently, go back two positions in list and continue iteration over list.
  # Example:
  # SL = ['<P>', 'a', 'b', 'c', '<P>'] => becomes    ['<P>', 'a', 'b c', <P>]
  # TL = ['<P>', 'A', 'B C', '', '<P>'] => becomes   ['<P>', 'A', 'B C', <P>]
  i = 0
  while i < len(sl_sents) - 1:
    if sl_sents[i+1] == "<P>":
      nextIsParagraph = True
    else:
      nextIsParagraph = False
    if (len(sl_sents[i]) == 0 or len(tl_sents[i]) == 0) and nextIsParagraph == True:
      sl_sents[i-1] = (sl_sents[i-1] + " " + sl_sents[i]).strip()
      sl_sents.pop(i)
      tl_sents[i-1] = (tl_sents[i-1] + " " + tl_sents[i]).strip()
      tl_sents.pop(i)
      i -= 2
    i += 1
  return sl_sents, tl_sents
##### END OF FUNCTION DECLARATION



def remove_unevenly_long_segments(sl_sents, tl_sents):
  """Remove entire segment between two <P> markers if segment length difference across SL/TL above certain threshold,
  i.e. if either the SL or TL segment consists of much more sentences than its counterpart in the other language.  
  
  Arguments:
    sl_sents (dict) -- Source language sentences, represented as strings.
      Keys: names of output file
      Values: List of the sentences
    tl_sents (dict) -- Target language sentences, represented as strings.
      Keys: names of output file
      Values: List of the sentences

  Returns:
    sl_sents (dict) -- SL sentences, with unevenly long segments removed.
    tl_sents (dict) -- TL sentences, with unevenly long segments removed.

  """
  p_positions_sl = [i for i, n in enumerate(sl_sents) if n == "<P>"] # Determine index positions of <P> markers
  p_positions_tl = [i for i, n in enumerate(tl_sents) if n == "<P>"] # Determine index positions of <P> markers

  for i in reversed(range(len(p_positions_sl)-1)): # Iterate by index over reversed list of <P> indices, i.e. from last segment to 1st    
    segmentStart_sl = p_positions_sl[i] # Determine start index of given SL segment
    segmentEnd_sl = p_positions_sl[i+1] # Determine end index of given SL segment

    segmentStart_tl = p_positions_tl[i] # Determine start index of given TL segment
    segmentEnd_tl = p_positions_tl[i+1] # Determine end index of given TL segment

    segmentLength_sl = abs(segmentStart_sl - segmentEnd_sl) - 1 # Get SL segment length (nr. of sentences) from start/end positions of segment
    segmentLength_tl = abs(segmentStart_tl - segmentEnd_tl) - 1 # Get TL segment length (nr. of sentences) from start/end positions of segment

    lengthRatio_sl_tl = max(segmentLength_sl, segmentLength_tl) / min(segmentLength_sl, segmentLength_tl) # Calculate ratio of length of SL segment to length of TL segment irrespective of which segment is longer

    if lengthRatio_sl_tl > 2: # If SL segment has at least 3x more sentences than TL segment, or vice versa:
      del sl_sents[segmentStart_sl : segmentEnd_sl] # Delete entire segment from list of SL segments
      del tl_sents[segmentStart_tl : segmentEnd_tl] # Delete entire segment from list of TL segments

  if len(sl_sents) == 1 and sl_sents[0] == "<P>": # If SL segment has no sentences, i.e. only one <P> mark:
    sl_sents.append("<P>") # Append final <P> mark
  if len(tl_sents) == 1 and tl_sents[0] == "<P>": # If TL segment has no sentences, i.e. only one <P> mark:
      tl_sents.append("<P>") # Append final <P> mark

  return sl_sents, tl_sents
##### END OF FUNCTION DECLARATION






def clean_parallel_texts(sl, dirname_sl, tl, dirname_tl):
  """ Delete monolingual files from parallel corpus if either SL or TL language file is missing for a given translation pair
  (e.g. remove 01_de.txt from folder DE_sl if no corresponding translation 01_it.txt is found in folder IT_tl).
    
  Arguments:
    sl (str) -- Two-letter source language identifier.
    dirname_sl (str) -- Path to source language folder of given language pair.
    tl (str) -- Two-letter target language identifier.
    dirname_tl (str) -- Path to target language folder of given language pair.

  Returns:
    Nothing; instead, it removes all files that have no corresponding file in other language of given language pair.
  
  """
  files_sl = []
  files_tl = []
  
  for root, dirs, files in os.walk(dirname_sl):
    for fn in files:
      if fn.endswith('.txt'):
        files_sl.append(re.sub("_" + sl + ".txt", "", fn))

  for root, dirs, files in os.walk(dirname_tl):
    for fn in files:
      if fn.endswith('.txt'):
        files_tl.append(re.sub("_" + tl + ".txt", "", fn))

  delete_from_dirname_sl = set(files_sl) - set(files_tl)
  delete_from_dirname_tl = set(files_tl) - set(files_sl)
  
  for i in delete_from_dirname_sl:
    fn = (dirname_sl + "/" + i + "_" + sl + ".txt").replace('//', '/')
    os.remove(fn)

  for i in delete_from_dirname_tl:
    fn = (dirname_tl + "/" + i + "_" + tl + ".txt").replace('//', '/')
    os.remove(fn)
##### END OF FUNCTION DECLARATION 







####################################################################################
#                                                                                  #
#                              M A I N   P R O G R A M                             #
#                                                                                  #
####################################################################################


##############################################
########## DEFINE GLOBALLY-USED REGEX PATTERNS
# Language abbreviation codes, grouped for retrieval: language code in parenthesis
# with optional space between code and parenthesis
langcode = re.compile (r"\( ?(BG|CS|DA|DE|EL|EN|ES|ET|FI|FR|GA|\
                        HU|IT|LT|LV|MT|NL|PL|PT|RO|SK|SV|SL) ?\)")
# In some Slavic languages, "ES" followed by certain pattern is abbreviation of "European Union"
# rather than Spanish language code. These exceptions are defined in langcode_exception 
langcode_exception = re.compile(r'(\( ?ES ?\)( št\.? | \d{1,4} ?/| ?,? \(? ?č| Nr))')

chapterTag = re.compile(r'<CHAPTER ID="?([\d_]+)"?')
speakerTag = re.compile(r'<SPEAKER ID="?(x?\d+(_\d{3})?)"?') #?x greps optional x to capture inserted language IDs - original RegEx was: (r'<SPEAKER ID="?(\d+(_\d{3})?)"?')
languageTag = re.compile(r'LANGUAGE="(\w{2})"')
nameTag = re.compile(r'NAME="([^"]*)"')
president = re.compile(r'(Πρόεδρ|Président|Formand|Președin|Elnök|Przewodnicz|\
                              |Presid|Juhataja|Pirminink|Talman|Председа|Voorzitter|Předsed|\
                              |Puhemies|Puheenjoh|Präsident|Priekš|Přesed|Prieks|Prési|Predsed|Preisdente|\
                              |Preşdinte|Προεδρ|Preşedi|Представ|Ordförand|Preseda)', re.I)
exceptions_nonroman = re.compile(r'(|Барозу|Малмстрьом|Κυριάκος|Аштън|Мишел|Гюнтер|Йоханес|Хоакин|\
                                    |Хосе|Σπύρος|Щефан|Συλβάνα|Ευαγγελία|Оли Рен|Δημητρακόπουλος|\
                                    |Δημήτριος|Жак|Джо|Ян|Μπ|Χρ|Χαρ)')
xmlTag_all = re.compile(r'^<.+>$')
xmlTag = re.compile(r'^<[^P].*>$')
##### DEFINITION OF REGEX-PATTERNS COMPLETED
############################################



#############################################################
##########  DEFINE COMMAND LINE ARGUMENTS AND ARGUMENT PARSER
choices_sl = ['all', 'BG', 'CS', 'DA', 'DE', 'EL', 'EN', 'ES', 'ET', 'FI', 'FR', 'GA', 'HU','IT',
             'LT', 'LV', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SL', 'SV']
choices_tl = ['all', 'BG', 'CS', 'DA', 'DE', 'EL', 'EN', 'ES', 'ET', 'FI', 'FR', 'HU', 'IT',
              'LT', 'LV', 'NL', 'PL', 'PT', 'RO', 'SK', 'SL', 'SV']

parser = argparse.ArgumentParser(description="Extraction of Comparable or Parallel Corpora from EuroParl")
subparsers = parser.add_subparsers(dest="subcommand")

# Subparser for Comparable Corpora
parser_comparable = subparsers.add_parser("comparable", description="Extraction of comparable corpora from EuroParl")

langs_comparable = parser_comparable.add_argument_group("LANGUAGES")
langs_comparable.add_argument("-sl", metavar ="SOURCE LANGUAGE(S)", nargs='+', choices=choices_sl, required=True, help='Choose from {%(choices)s}')
langs_comparable.add_argument("-tl", metavar ="TARGET LANGUAGE(S)", nargs='+', choices=choices_tl, required=True, help='Choose from {%(choices)s}')

paths_comparable = parser_comparable.add_argument_group('PATHS')
paths_comparable.add_argument("-i", "--inputFolder", required=True, help="Path to file to be processed or directory that contains files to be processed")
paths_comparable.add_argument("-o", "--outputFolder", required=True, help="Output folder for storage of extracted corpus files")

iooptions_comparable = parser_comparable.add_argument_group("INPUT-/OUTPUT OPTIONS")
iooptions_comparable.add_argument("-d", "--debug", required=False, action= "store_true",
                    help="Create a log file for debugging")
iooptions_comparable.add_argument("-s", "--statementList", nargs=1, required=False,
                    help="Supply External Statement List in CSV Format")
iooptions_comparable.add_argument("-al", "--additionalLanguageTags", action="store_true", required=False, help="Disseminate additional language tags to increase recall of segments")
iooptions_comparable.add_argument("-c", "--cleanOutput", nargs=1,
                                  choices=['lang', 'speaker', 'both'], required=False, help='Clean output from speaker tags and/or additional language tags')

# Subparser for Parallel Corpora
parser_parallel = subparsers.add_parser("parallel", description="Extraction of parallel corpora from EuroParl")

langs_parallel = parser_parallel.add_argument_group("LANGUAGES")
langs_parallel.add_argument("-sl", metavar ="SOURCE LANGUAGE(S)", nargs='+', choices=choices_sl, required=True, help='Choose from {%(choices)s}')
langs_parallel.add_argument("-tl", metavar ="TARGET LANGUAGE(S)", nargs='+', choices=choices_tl, required=True, help='Choose from {%(choices)s}')

paths_parallel = parser_parallel.add_argument_group('PATHS')
paths_parallel.add_argument("-i", "--inputFolder", required=True, help="Path to file to be processed or directory that contains files to be processed")
paths_parallel.add_argument("-o", "--outputFolder", required=True, help="Output folder for storage of extracted corpus files")

iooptions_parallel = parser_parallel.add_argument_group("INPUT-/OUTPUT OPTIONS")
iooptions_parallel.add_argument("-f", "--outputFormat", required=True, nargs='+',
                                choices=['txt', 'tab', 'tmx'],
                                help='Choose one or more output formats from {txt, tab, tmx}\n'\
                                'TXT: non-aligned plain text files (SL/TL separately)\n'\
                                'TAB: tabulator-separated sentence-aligned file format\n'\
                                'TMX: sentence-alignd TMX files', metavar='\a') # '\a' is potential source for bugs - replace metavar='\a' with metavar='OUTPUT FORMAT(s)' if assertion error arises in CLI parsing
iooptions_parallel.add_argument("-d", "--debug", required=False, action= "store_true",
                    help="Create a log file to for debugging")
iooptions_parallel.add_argument("-s", "--statementList", nargs=1, required=False,
                    help="Supply External Statement List in CSV Format")
iooptions_parallel.add_argument("-al", "--additionalLanguageTags", action="store_true", required=False, help="Disseminate additional language tags to increase number of statements")
iooptions_parallel.add_argument("-c", "--cleanOutput", nargs=1,
                                choices=['langs', 'xml', 'both'], required=False, help='Clean output from XML for paragraphs, speaker turns or both')
##### DEFINITION OF CLI PARSER COMPLETED
########################################



###################################
########## PARSE COMMAND LINE INPUT
args = parser.parse_args()

corpustype = args.subcommand
  
inDir = args.inputFolder
outDir = args.outputFolder

# Get list of input file(s) from input folder specified in CLI arguments
europarl_sourcefiles = get_sourcefiles_from_folder(inDir)

'''
# Get list of input file(s) from single file rather than entire input folder
# Deprecated function
if args.file:
  get_sourcefile(inDir)
else:
'''

sourceLanguages = args.sl
if 'all' in sourceLanguages:
  choices_sl.remove('all')
  sourceLanguages = choices_sl
  
targetLanguages = args.tl
if 'all' in targetLanguages:
  choices_tl.remove('all')
  targetLanguages = choices_tl

# Initialise log file for debugging if CLI argument set accordingly
if args.debug:
  open(outDir + '/log_extraction.txt', 'w').close()
  logfile = open(outDir + '/log_extraction.txt', mode='a')
  logfile_header = ("EuroParlExtract Logfile (Creation Date: %s)" %(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
  logfile.write("=" * len(logfile_header) + "\n"\
                + logfile_header + "\n" +\
                 "=" * len(logfile_header) + "\n")
  logfile.write("\nCLI ARGS: \n" + str(args) + "\n\n\n")

if args.statementList:
  statementList_path = args.statementList[0]

if args.cleanOutput:
  isCleanOutput = args.cleanOutput[0]
  if isCleanOutput != "lang":
    min_lines_per_file = 1
  else:
    min_lines_per_file = 2
else:
  isCleanOutput = False
  min_lines_per_file = 2
##### PARSING OF COMMAND LINE INPUT COMPLETED
#############################################



################################################################################
########## GENERATE LIST OF SPEAKER TURNS OR LOAD EXISTING LIST OF SPEAKER TURNS
# If no external CSV list of statements is supplied then generate it from EuroParl source files
if args.statementList:
  print("\n>> Reading list of speaker turns from pre-compiled CSV file %s" %(statementList_path))
  speaker_list = pd.read_csv(statementList_path, sep='\t', dtype=str, index_col=0)
  print("\n   CSV file loaded into memory!")
else:
  '''
  # List generation from single input file rather than from input folder disabled in this version
  if args.file:
    print("\nProcessing file %s \n" %(inDir))
  else:
  '''
  print("\n>> GENERATING LIST OF SPEAKER TURNS FROM INPUT FILES:\n")
  print("   Processing %s EuroParl source files in input folder %s\n" %(len(europarl_sourcefiles), inDir))
  speaker_list = pd.DataFrame(columns= ('NAMES_FULL_COUNT', 'NAMES_NORMALISED_SUMMARY', 'NAMES_MATCHING', 'ORIGINAL_LANGUAGE', 'SL', 'ADDITIONAL_LANGUAGE')) 
  speaker_list.index.name = 'UNIQUE_ID'
  
#  Loop over input files to generate list of speaker turns
  if args.debug:
    logfile.write("######################## STARTING GENERATION OF SPEAKER TURNS LIST ######################### \n\n")
  counter = 1 # Initialise counter for progress bar
  for inputfile in europarl_sourcefiles:
    if args.debug:
      logfile.write("Retrieving metadata from input file:\t" + inputfile + "\n")
    analyse_sourcefile(inputfile)
  
    progress = int((counter/len(europarl_sourcefiles))*100)
    statusbar = int(progress/2)
    sys.stdout.write("\r")
    sys.stdout.write("\t["+"="*statusbar+" "*(50-statusbar)+"]"+"\t"+str(progress)+" %")
    counter +=1
  print("\n\n   %s speaker turns identified in source files.\n" %len(speaker_list))
  # Finished looping over input files

  #  Post-process generated list of statements:\
  #  1) Disambiguate speakers by calling match_speakers() \
  #  2) Determine source language from XML language tags (SL) and alternative parenthesis () language tags (SL2) \
  #     by calling language_vote()
  print("   Post-processing list, please wait.\n")
  if args.debug:
    logfile.write("\n\n######################## POST-PROCESSING SPEAKER TURNS LIST #########################\n\n")
  for index, row in speaker_list.iterrows(): # Index is equivalent to column unique_file_id
    if args.debug:
      logfile.write(index + "\n")
    row['NAMES_NORMALISED_SUMMARY'] = group_speakers(row['NAMES_FULL_COUNT'])
    row['NAMES_MATCHING'] = match_speakers(row['NAMES_NORMALISED_SUMMARY'])
    
    # Determine source language of each speaker turn by voting procedure
    sourceLanguage = language_vote(row['ORIGINAL_LANGUAGE'], row['ADDITIONAL_LANGUAGE'])
    row['SL'] = sourceLanguage
    ##  Post-Processing of speaker_list completed
  
  # Export list to CSV file
  speaker_list.to_csv(outDir + 'europarl_statements.csv', sep='\t', header=True, encoding='UTF-8')
  print("   DONE! Statements list successfully exported to CSV as " + outDir.replace("/", "") + "/europarl_statements.csv !\n")
##### GENERATING OR LOADING LIST OF SPEAKER TURNS COMPLETED
###########################################################



################################################################################
#                                                                              #
#                    C O R P U S  E X T R A C T I O N                          #
#                                                                              #
################################################################################



###############################################################################
########## COMPARABLE CORPUS

if corpustype == "comparable":
  print("\n>> STARTING EXTRACTION OF COMPARABLE CORPORA ...\n")
  print("   NON-TRANSLATED COMPARABLE SUBCORPORA:")

#####  EXTRACT NON-TRANSLATED COMPARABLE SUBCORPORA
  if args.debug:
    logfile.write("############################  START EXTRACTION OF NON-TRANSLATED COMPARABLE CORPORA  #############################\n")
  for tl in targetLanguages:
    if os.path.exists((inDir + "/" + tl.lower()).replace('//', '/')):
      print("     Extracting non-translated text in language\t%s" %(tl))

    # Filter speaker_list to find statements originally uttered in given language and with unambiguous speaker
    unambiguous_statemens_nontranslated = speaker_list[(speaker_list['SL'] == tl) & (speaker_list['NAMES_MATCHING'] != "xAMB")].index
    # Put all non-translated statements for given language in dictionary statements_nontranslated
    # Keys:    Filenames of source files containing the statements
    # Values:  Speaker IDs of each non-translated statement
    statements_nontranslated = {}
    for usn in unambiguous_statemens_nontranslated: # usn = unambiguous_statement_nontranslated
      fname_out = usn.split("|")[0]
      id = usn.split("|")[1]
      if fname_out not in statements_nontranslated:
        statements_nontranslated[fname_out] = [id]
      else:
        statements_nontranslated[fname_out].append(id)
    extract_comparable_nontranslated(statements_nontranslated, tl)
#####  EXTRACTION OF NON-TRANSLATED COMPARABLE CORPORA COMPLETED



##### EXTRACT TRANSLATED COMPARABLE SUBCORPORA
  if args.debug:
    logfile.write("\n\n############################  START EXTRACTION OF TRANSLATED COMPARABLE CORPORA  #############################\n\n")
  print("\n   TRANSLATED COMPARABLE SUBCORPORA:")
  for sl in sourceLanguages:
    
    unambiguous_statemens_in_sourcelanguage = speaker_list[(speaker_list['SL'] == sl) & (speaker_list['NAMES_MATCHING'] != "xAMB")].index
    # Put all source language statements for given language in dictionary statements_sourcelanguage:
    # Keys: filenames of files containing the statements, values: speaker IDs pointing to source language statement 
    statements_sourcelanguage = {}
    for uss in unambiguous_statemens_in_sourcelanguage:
      fname = uss.split("|")[0]
      id = uss.split("|")[1]
      if fname not in statements_sourcelanguage:
        statements_sourcelanguage[fname] = [id]
      else:
        statements_sourcelanguage[fname].append(id)
    for tl in targetLanguages:
      if sl != tl: # Avoid pairs of type BG-BG, which are equivalent to non-translated statements
        if os.path.exists((inDir + "/" + tl.lower()).replace('//', '/')):
          print("     %s > %s" %(sl, tl))
        extract_comparable_translated(statements_sourcelanguage, sl, tl)
    print("")
  print("DONE! Extraction of Comparable Corpora Completed!\n\n")
##### EXTRACTION OF COMPARABLE CORPORA COMPLETED
###############################################################################



###############################################################################
############# EXTRACT PARALLEL CORPORA
else: # if corpustype != "comparable":
  print("\n>> STARTING EXTRACTION OF PARALLEL CORPORA ...\n")
  # Determine output format specified in CLI arguments
  outputToTxt, outputToTab, outputToTmx = None, None, None
  if "txt" in args.outputFormat:
    outputToTxt = True
  if "tab" in args.outputFormat:
    outputToTab = True
  if "tmx" in args.outputFormat:
    outputToTmx = True

  for sl in sourceLanguages:
    unambiguous_statemens_in_sourcelanguage = speaker_list[(speaker_list['SL'] == sl) & (speaker_list['NAMES_MATCHING'] != "xAMB")].index
    # Put all source language statements for given language in dictionary statements_sourcelanguage
    # Keys: Filenames of files containing the statements
    # Values: Speaker IDs pointing to source language statements 
    statements_sourcelanguage = {}
    for uss in unambiguous_statemens_in_sourcelanguage: # uss = "unambiguous statements in SL"
      fname = uss.split("|")[0]
      id = uss.split("|")[1]
      if fname not in statements_sourcelanguage:
        statements_sourcelanguage[fname] = [id]
      else:
        statements_sourcelanguage[fname].append(id)
    for tl in targetLanguages:
      if os.path.exists(inDir + "/" + sl.lower()) and tl != sl and os.path.exists(inDir + "/" + tl.lower()): #avoid pairs of type BG-BG, which are equivalent to non-translated statements as well as pairs like MT>BG, for which no source files exist
        print("   %s > %s" %(sl, tl))
        extract_parallel(statements_sourcelanguage, sl, tl)
  print("\nDONE! Extraction of Parallel Corpora Completed!\n\n")

############# EXTRACTION OF PARALLEL CORPORA COMPLETED
###############################################################################



###################### CORPUS EXTRACTION COMPLETED #############################

if args.debug:
  logfile.close()
