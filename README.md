# EuroParlExtract

EuroParlExtract is a corpus processing toolkit for the compilation of directional sub-corpora, both bilingual parallel and monoloingual comparable ones, from the original release of the European Parliament Proceedings Parallel Corpus (EuroParl) by Philipp Koehn (2005). It therefore aims to maximise the utility of the EuroParl corpus, which in its original release does not provide tools to compile directional subcorpora (i.e. corpora where the source and target language are made explicit for each language pair) and is therefore of limited use for linguistic translation research.

The motivation behind the project is to make the wealth of linguistic data contained in the EuroParl corpus easily available to researchers and students in the field of translation studies and contrastive linguistics, even if they lack advanced scripting/programming skills. EuroParlExtract is therefore conceived as an addition to EuroParl aiming to lower the barrier to corpus-driven contrastive research.

## Getting Started

EuroParlExtract comprises a number of scripts written in Python3 and Bash for Linux; Windows is not yet supported. Some parts of the package are based on third-party software.

The following step-by-step instructions will guide you through the corpus extraction process.

### 1. Install Required Python Packages

EuroParlExtract requires **Python 3** (you can download it from https://www.python.org/downloads) as well as the Python packages [**Pandas**](https://pandas.pydata.org/pandas-docs/stable/install.html) and [**Unidecode**](https://pypi.python.org/pypi/Unidecode). If they are not yet installed on your system, you can easily install them using pip (to install pip, execute `sudo apt-get install python3-pip` from your terminal):

```shell
# Install Pandas:
pip3 install pandas
```

```shell
# Install Unidecode:
pip3 install unidecode
```
### 2. Download EuroParlExtract

Once your Python environment has been set up properly, you need to download and unpack the EuroParlExtract scripts:

````shell
wget https://github.com/mustaszewski/europarl-extract/archive/v0.9.tar.gz
tar xzf v0.9.tar.gz
````
You are now ready to use EuroParlExtract to extract the desired corpora form EuroParl source files!

## Extracting Corpora

### 1. Get EuroParl Source Files

Since EuroParlExtract itself does not contain any corpus data but only corpus extraction scripts, you first need to download the original EuroParl release. If you have already downloaded the EuroParl corpus from http://www.statmt.org/europarl and placed the source files in the EuroParlExtract folder, you can go directly to step 2. Otherwise, do the following:

```shell
cd europarl-extract-0.9
wget http://www.statmt.org/europarl/v7/europarl.tgz
tar xzf europarl.tgz
```
This will download and unpack the compressed corpus in the folder `europarl-extract-0.9/txt/`. **Attention:** Please retain the original directory structure and files names of the EuroParl corpus, otherwise the extraction will fail!

### 2. Remove XML Markup and Empty Lines

The original EuroParl source files need to be prepared for the use with EuroParlExtract. First, remove spurious XML markup, empty lines etc. with the supplied bash script `cleanSourceFiles.sh <input_folder>`, e.g.:

```shell
./preprocess/cleanSourceFiles.sh txt/
```

### 3. Disambiguate Statement IDs

Next, run the script `disambiguate_speaker_IDs.py <input_folder>` to ensure that no two statements are assigned the same ID within one source file. To do so, run:

```shell
python3 disambiguate_speaker_IDs.py txt/
```

### 4. Sentence Segmentation and Optional Tokenisation

For the extraction of **sentence-aligned parallel corpora, sentence segmentation is a required** pre-processing step, whereas in the case of comparable corpora sentence segmentation is not required (albeit useful for future analyses). Tokenisation is optional for both comparable and parallel corpora and therefore depends on end users' needs.

EuroParlExtract supports **two different third-party tools** users can choose from 1) *ixa-pipe-tok*, a sentence splitter and tokeniser implemented in Java by Rodrigo Agerri (see http://ixa2.si.ehu.es/ixa-pipes); or 2) the sentence splitter and tokeniser of the *Europarl Preprocessing Tools* implemented in Perl by Philipp Koehn (see http://www.statmt.org/europarl). The former is more accurate but considerably slower that the latter, so users should choose one of the tools according to their own preferences.

To perform sentence segmentation without tokenisation using *EuroParl Preprocessing Tools*, run:

```shell
./preprocess/segment_EuroParl.sh txt/
```

For segmentation and tokenisation using *EuroParl Preprocessing Tools*, run:

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
- When using *EuroParl Preprocessing Tools*, you may first only segment the source files and tokenise them later.
- Running *ixa-pipe-tok* requires Java 1.7+ on your system. You can install it with `sudo apt-get install openjdk-8-jdk`.


### 5. Run Extraction Scripts

After the preliminary steps 1 to 4, the EuroParl source files are ready for the extraction process calling the main script `extract.py` with either the `parallel` or `comparable` subcommand.

**Parallel corpora**

Parallel corpora consist of unidirectional pairs of source and target texts (= parallel texts, bitexts). For each of the selected language pairs, the script extracts all available bitexts from the EuroParl source files and saves them to a dedicated folder indicating the language pair. From the 21 EuroParl languages, users may choose any language pair, including an option to extract all 420 language pairs in one go. To extract parallel corpora, the following arguments need to be specified (see also help message `python3 extract.py parallel --help`):

- `-sl [source_language ...]`: Choose one or more source language(s), separated by blanks. For a list of supported language codes, display the help message by calling `python3 extract.py parallel --help`. Note: you may also choose all source languages.
- `-tl [target_language ...]`: Choose one or more target language(s), separated by blanks. For a list of supported languages, display the help message by calling `python3 extract.py parallel --help`. Note: you may also choose all target languages.
- `-i <input_folder>`:  Path to input folder containing EuroParl source files, usually txt/.
- `-o <output_folder>`: Path to output folder where subfolders for each language pair will be created.
- `-f [txt|tab|tmx ...]`: Choose one or more output format(s), separated by blanks. `txt` creates non-aligned separate source and target text files (see sample [source](https://github.com/mustaszewski/europarl-extract/blob/master/documentation/sample_outputfiles/parallel_en_sl.txt) and [target file](https://github.com/mustaszewski/europarl-extract/blob/master/documentation/sample_outputfiles/parallel_de_tl.txt)), `tab` creates sentence-aligned files where each line contains corrsponding source and target segments separated by tabulator (see [sample file](https://github.com/mustaszewski/europarl-extract/blob/master/documentation/sample_outputfiles/parallel_en-de.tab)), `tmx` creates sentence-aligned TMX files (see [sample file](https://github.com/mustaszewski/europarl-extract/blob/master/documentation/sample_outputfiles/parallel_en-de.tmx)).
- `-s <statement_file>`: Optional argument to supply a precompiled statement list (CSV format) rather than creating the list from EuroParl source files from scratch (**recommended** - extremly speeds up the extraction process!) The list can be found in the folder [corpora/](https://github.com/mustaszewski/europarl-extract/tree/master/corpora) of the EuroParlExtract distribution.
- `-al`: Optional argument to disseminate additional language tags across source files (**recommended** - largely increases number of statements!)
- `-c {lang|speaker|both}`: Optional argument to remove language identifier and/or speaker metadata tags from output files.
- `-d`: Optional argument to create a log file for debugging (not recommended - use only in case of problems).

Example:

```shell
python3 extract.py parallel -sl PL BG -tl all -i txt/ -o corpora/ -f txt tab -s corpora/europarl_statements.csv -al -c both
# Extracts parallel texts from Polish to all other EuroParl languages and from Bulgarian to all other EuroParl languages,
# stores texts in sentence-aligned tab-separated files and non-aligned source and target files;
# speaker and language metadata markup removed from output files.
```

**Comparable corpora**

Contrary to parallel corpora, comparable corpora consist of single monolingual files in the choosen language(s) rather than of bilingual source-target text pairs. In comparable corpora, two sections can be distinguished: one containing only texts originally produced in a given language (e.g. non-translated English), and one containing only texts that have been translated into a given language (e.g. translated English). The latter can be further subdivided according to source languages (e.g. English texts translated from Polish, English texts translated from German ...). Note that no source texts are stored in the translated section of comparable corpora, i.e. only the target side of each language combination is extracted, while information about the source language is only used as metadata. To extract comparable corpora, the following arguments need to be specified (see also help message `python3 extract.py comparable --help`):

- `-sl [source_language ...]`: Choose one or more source language(s), separated by blanks. For a list of supported language codes, display the help message by calling `python3 extract.py comparable --help`. Note: you may also choose all source languages.
- `-tl [target_language ...]`: Choose one or more target language(s), separated by blanks. For a list of supported languages, display the help message by calling `python3 extract.py comparable --help`. Note: you may also choose all target languages.
- `-i <input_folder>`:  Path to input folder containing EuroParl source files, usually txt/.
- `-o <output_folder>`: Path to output folder where subfolders for each language pair will be created.
- `-s <statement_file>`: Optional argument to supply a precompiled statement list (CSV format) rather than creating the list from EuroParl source files from scratch (**recommended** - extremly speeds up the extraction process!) The list can be found in the folder [corpora/](https://github.com/mustaszewski/europarl-extract/tree/master/corpora) of the EuroParlExtract distribution.
- `-al`: Optional argument to disseminate additional language tags across source files (**recommended** - largely increases number of statements!)
- `-c {lang|speaker|both}`: Optional argument to remove language identifier and/or speaker metadata tags from output files.
- `-d`: Optional argument to create a log file for debugging (not recommended - use only in case of problems).

Example:

```shell
python3 extract.py comparable -sl all -tl PL BG -i txt/ -o corpora/ -s corpora/europarl_statements.csv -al -c speaker
# Extracts texts originally written in Polish and texts originally written in Bulgarian
# as well as texts translated into these two languages from all other EuroParl languages;
# speaker metadata markup removed from output files.
```

# TO DO REST

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc

