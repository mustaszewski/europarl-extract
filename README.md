 [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

# EuroparlExtract

EuroparlExtract is a corpus processing toolkit for the compilation of directional sub-corpora, both bilingual parallel and monoloingual comparable ones, from the original release of the European Parliament Proceedings Parallel Corpus (Europarl) by Philipp Koehn (2005). It therefore aims to maximise the utility of the Europarl corpus, which in its original release does not provide tools to compile directional subcorpora (i.e. corpora where the source and target language are made explicit for each language pair) and is therefore of limited use for linguistic and translation research.

The motivation behind the project is to make the wealth of linguistic data contained in the Europarl corpus easily available to researchers and students in the field of translation studies and contrastive linguistics, even if they lack advanced scripting/programming skills. EuroparlExtract is therefore conceived as an addition to Europarl aiming to lower the barrier to corpus-driven contrastive research.

## Getting Started

EuroparlExtract comprises a number of scripts written in Python3 and Bash for Linux; Windows is not yet supported. Some parts of the package are based on third-party software.

The following step-by-step instructions will guide you through the corpus extraction process.

### 1. Install Required Python Packages

EuroparlExtract requires **Python 3** (you can download it from https://www.python.org/downloads) as well as the Python packages [**Pandas**](https://pandas.pydata.org/pandas-docs/stable/install.html) and [**Unidecode**](https://pypi.python.org/pypi/Unidecode). If they are not yet installed on your system, you can easily install them using pip (to install pip, execute `sudo apt-get install python3-pip` from your terminal):

```shell
# Install Pandas:
pip3 install pandas
```

```shell
# Install Unidecode:
pip3 install unidecode
```
### 2. Download EuroparlExtract

Once your Python environment has been set up properly, you need to download and unpack the EuroparlExtract scripts:

````shell
wget https://github.com/mustaszewski/europarl-extract/archive/v0.9.tar.gz
tar xzf v0.9.tar.gz
````

### 3. Get Europarl Source Files

Since EuroparlExtract itself does not contain any corpus data but only corpus extraction scripts, you first need to download the original Europarl release. If you have already downloaded the Europarl corpus from http://www.statmt.org/europarl and placed the source files in the EuroparlExtract folder, you can go to the [next step](#preprocess-europarl-source-files) . Otherwise, do the following:

```shell
cd europarl-extract-0.9
wget http://www.statmt.org/europarl/v7/europarl.tgz
tar xzf europarl.tgz
```
This will download and unpack the compressed corpus in the folder `europarl-extract-0.9/txt/`. **Attention:** Please retain the original directory structure and files names of the Europarl corpus, otherwise the extraction will fail!

## Preprocess Europarl Source Files

The original Europarl source files need to be cleaned and normalised before applying the corpus extraction scripts. To perform the required preprocessing steps, you can **either** follow the preprocessing steps 1 to 3 **or** execute `./preprocess/preprocess_batch.sh txt/` and then proceed directly to [Extract Corpora](#extract-corpora).

### 1. Remove XML Markup and Empty Lines

First, remove spurious XML markup, empty lines etc. with the supplied bash script `cleanSourceFiles.sh <input_folder>`, e.g.:

```shell
./preprocess/cleanSourceFiles.sh txt/
```

### 2. Disambiguate Statement IDs

Next, run the script `disambiguate_speaker_IDs.py <input_folder>` to ensure that no two statements are assigned the same ID within one source file. To do so, run:

```shell
python3 disambiguate_speaker_IDs.py txt/
```

### 3. Sentence Segmentation and Optional Tokenisation

For the extraction of **sentence-aligned parallel corpora, sentence segmentation is a required** pre-processing step, whereas in the case of comparable corpora sentence segmentation is not required (albeit useful for future analyses). Tokenisation is optional for both comparable and parallel corpora and therefore depends on end users' needs.

EuroparlExtract comes with **two different third-party tools** users can choose from: 1) *ixa-pipe-tok*, a sentence splitter and tokeniser implemented in Java; or 2) the sentence splitter and tokeniser of the *Europarl Preprocessing Tools* implemented in Perl. The former is more accurate but considerably slower that the latter, so users should choose one of the tools according to their own preferences.

To perform sentence segmentation without tokenisation using *Europarl Preprocessing Tools*, run:

```shell
./preprocess/segment_EuroParl.sh txt/
```

For segmentation and tokenisation using *Europarl Preprocessing Tools*, run:

```shell
./preprocess/segment-tokenise_EuroParl.sh txt/
```

For segmentation and subsequent tokenisation using *ixa-pipe-tok*, run:

```shell
./preprocess/segment-tokenise_ixaPipes.sh txt/
```

**Notes:**
- You only need to choose one of the three methods above!
- You may use your own/other tools for sentence segmentation and tokenisation. If you choose to do so, make sure that segmented/tokenised files are files of the type `.txt` and that XML markup is retained.
- When using *Europarl Preprocessing Tools*, you may first only segment the source files and tokenise them later.
- Running *ixa-pipe-tok* requires Java 1.7+ on your system. You can install it with `sudo apt-get install openjdk-8-jdk`.


## Extract Corpora

After preprocessing the Europarl source files, the extraction can be performed by calling the main script `extract.py` with either the `parallel` or `comparable` subcommand.

### a) Parallel Corpora
Parallel corpora consist of unidirectional pairs of source and target texts (= parallel texts, bitexts). For each of the selected language directions, the script extracts all available bitexts from the Europarl source files and saves them to a dedicated folder indicating the language direction. From the 21 Europarl languages, users may choose any language combination, including an option to extract all 420 parallel corpora in one go. To extract parallel corpora, the following arguments need to be specified (see also help message `python3 extract.py parallel --help`):

- `-sl [source_language ...]`: Choose one or more source language(s), separated by blanks. For a list of supported language codes, display the help message by calling `python3 extract.py parallel --help`. Note: you may also choose `all` source languages.
- `-tl [target_language ...]`: Choose one or more target language(s), separated by blanks. For a list of supported languages, display the help message by calling `python3 extract.py parallel --help`. Note: you may also choose `all` target languages.
- `-i <input_folder>`:  Path to input folder containing Europarl source files, usually txt/.
- `-o <output_folder>`: Path to output folder where subfolders for each language direction will be created.
- `-f [txt|tab|tmx ...]`: Choose one or more output format(s), separated by blanks. `txt` creates non-aligned separate source and target text files (see sample [source](https://github.com/mustaszewski/europarl-extract/blob/master/documentation/sample_outputfiles/parallel_en_sl.txt) and [target file](https://github.com/mustaszewski/europarl-extract/blob/master/documentation/sample_outputfiles/parallel_de_tl.txt)), `tab` creates sentence-aligned files where each line contains corrsponding source and target segments separated by tabulator (see [sample file](https://github.com/mustaszewski/europarl-extract/blob/master/documentation/sample_outputfiles/parallel_en-de.tab)), `tmx` creates sentence-aligned TMX files (see [sample file](https://github.com/mustaszewski/europarl-extract/blob/master/documentation/sample_outputfiles/parallel_en-de.tmx)).
- `-s <statement_file>`: Optional argument to supply a precompiled statement list (CSV format) rather than creating the list from Europarl source files from scratch (**recommended** - extremly speeds up the extraction process!) The list can be found in the folder [corpora/](https://github.com/mustaszewski/europarl-extract/tree/master/corpora) of the EuroparlExtract distribution.
- `-al`: Optional argument to disseminate parenthesised language tags across source files (**recommended** - largely increases number of extractable statements!)
- `-c {lang|speaker|both}`: Optional argument to remove parenthesised language identifiers and/or speaker metadata tags from output files.
- `-d`: Optional argument to create a log file for debugging (not recommended - use only in case of problems).

**Example:**

```shell
python3 extract.py parallel -sl PL BG -tl all -i txt/ -o corpora/ -f txt tab -s corpora/europarl_statements.csv -al -c both
# Extracts parallel texts from Polish to all other Europarl languages and from Bulgarian to all other Europarl languages,
# stores texts in sentence-aligned tab-separated files and non-aligned source and target files;
# speaker and language metadata markup removed from output files.
```

### b) Comparable Corpora

Contrary to parallel corpora, comparable corpora consist of individual monolingual files in the choosen language(s) rather than of bilingual source-target text pairs. In comparable corpora, two sections can be distinguished: one containing only texts originally produced in a given language (e.g. non-translated English), and one containing only texts that have been translated into a given language (e.g. translated English). The latter can be further subdivided according to source languages (e.g. English texts translated from Polish, English texts translated from German ...). Note that no source texts are stored in the translated section of comparable corpora, i.e. only the target side of each language combination is extracted, while source language information is only used as metadata. To extract comparable corpora, the following arguments need to be specified (see also help message `python3 extract.py comparable --help`):

- `-sl [source_language ...]`: Choose one or more source language(s), separated by blanks. For a list of supported language codes, display the help message by calling `python3 extract.py comparable --help`. Note: you may also choose `all` source languages.
- `-tl [target_language ...]`: Choose one or more target language(s), separated by blanks. For a list of supported languages, display the help message by calling `python3 extract.py comparable --help`. Note: you may also choose `all` target languages.
- `-i <input_folder>`:  Path to input folder containing Europarl source files, usually txt/.
- `-o <output_folder>`: Path to output folder where subfolders for each language pair will be created.
- `-s <statement_file>`: Optional argument to supply a precompiled statement list (CSV format) rather than creating the list from Europarl source files from scratch (**recommended** - extremly speeds up the extraction process!) The list can be found in the folder [corpora/](https://github.com/mustaszewski/europarl-extract/tree/master/corpora) of the EuroparlExtract distribution.
- `-al`: Optional argument to disseminate parenthesised language tags across source files (**recommended** - largely increases number of extractable statements!)
- `-c {lang|speaker|both}`: Optional argument to remove parenthesised language identifiers and/or speaker metadata tags from output files.
- `-d`: Optional argument to create a log file for debugging (not recommended - use only in case of problems).

**Example:**

```shell
python3 extract.py comparable -sl all -tl PL BG -i txt/ -o corpora/ -s corpora/europarl_statements.csv -al -c speaker
# Extracts texts originally written in Polish and texts originally written in Bulgarian
# as well as texts translated into these two languages from all other Europarl languages;
# speaker metadata markup removed from output files.
```



# Further information

## System Documentation and Evaluation
For a detailed description and evaluation of the extraction procedure, please refer to the [associated paper](#citation).


## Performance
The script extract.py is not speed-optimised. Therfore, the first part of the extraction step may take several hours, depending on the CPU used. However, the proces can be speeded up extremely if the precompiled list of Europarl statements (see corpora/ folder of this package) is provided to the script. To do so, specify the path of the list via the `-s` parameter. Using the precompiled list, the extraction of the corpora of your choice should take only between a few minutes and up to one hour, depending on your CPU and the amount of text to be extracted. 


## Breakdown of extracted corpora

The following numbers of subcorpora can be extracted from the entire Europarl corpus:
- 420 directional parallel corpora
- 462 comparable translated corpora
- 21 comparable non-translated corpora

A detailed breakdown of the number of tokens per corpus and language direction can be found in the folder [documentation/corpus_statistics](https://github.com/mustaszewski/europarl-extract/tree/master/documentation/corpus_statistics).


## Download of precomiled corpora

Instead of using EuroparlExtract scripts for the extraction of sub corpora on demand, precompiled versions of the entire [parallel](https://zenodo.org/record/1066474#.WoGMwnwiHct) and [comparable subcorpus](https://zenodo.org/record/1066472#.WoGM4XwiHcs) can be downloaded. Note, however, that the precompiled corpora are very large (2.6 GB and 1.5 GB in .tar.gz format) because they comprise **all** language combinations. If you find it impractical to work with such large data quantities or if you are not interested in all language combinations, it is recommended to extract your corpora of choice using the provided scripts. This has the additional advantage of being able to customise the data in terms of output formats.


## License

EuroparlExtract is free software licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

All extracted corpora are licensed unter the CC BY 4.0 license.


## Citation

If you use EuroparlExtract or the corpora derived from it in your work, please cite the following paper (open access):

>
>Ustaszewski, Michael (2018): Optimising the Europarl corpus for translation studies with the EuroparlExtract toolkit. In: *Perspectives - Studies in Translation Theory and Practice* 27:1, p. 107-123. DOI: [10.1080/0907676X.2018.1485716](https://doi.org/10.1080/0907676X.2018.1485716)
>

## Third-party software

EuroparlExtract uses the following third-party software:

* A customisation of [ixa-pipe-tok](https://github.com/ixa-ehu/ixa-pipe-tok) by Rodrigo Agerri for sentence splitting and tokenisation.
* The [Europarl Preprocessing Tools](http://www.statmt.org/europarl) by Philipp Koehn for sentence splitting and tokenisation.
* A customisation of [GaChalign](https://github.com/alvations/gachalign) by Liling Tan and Francis Bond for sentence alignment.


## Credits

* [Europarl-direct](http://www.idiap.ch/dataset/europarl-direct) is a similar project for the extraction of subcorpora from Europarl. I would like to thank one of its authors, Thomas Meyer, for providing me with insights into the underlying extraction method.


## Contact
````
Michael Ustaszewski
University of Innsbruck
Department for Translation Studies
A-6020 Innsbruck
Austria
````
