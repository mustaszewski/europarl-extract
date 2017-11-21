# EuroParlExtract

EuroParlExtract is a corpus processing toolkit for the compilation of directional sub-corpora, both comparable and parallel ones, from the original release of the European Parliament Proceedings Parallel Corpus (EuroParl) by Philipp Koehn (2005). It therefore aims to maximise the utility of the EuroParl corpus, which in its original release does not provide support to compile directional subcorpora (i.e. corpora where the source and target language are made explicit for each language pair) and is therefore of limited use for linguistic translation research.

The motivation behind the project is to make the wealth of linguistic data contained in the EuroParl corpus easily available to researchers and students in the field of translation studies and contrastive linguistics, even if they lack advanced scripting/programming skills. EuroParlExtract is therefore conceived as an addition to EuroParl aiming to lower the barrier to corpus-driven contrastive research.

## Getting Started

EuroParlExtract comprises a number of scripts written in Python3 and Bash for Linux; Windows is not yet supported. Some parts of the package are based on third-party software.

The following step-by-step instructions will guide you through the corpus extraction process.

### 1. Install Required Python Packages

EuroParlExtract requires **Python 3** (you can download it from https://www.python.org/downloads/) as well as the Python packages **Pandas** and **Unidecode**. If they are not yet installed on your system, you can easily install them using pip (to install pip, execute `sudo apt-get install python3-pip` from your terminal):

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

Since EuroParlExtract itself does not contain any corpus data but only corpus extraction scripts, you first need to download the original EuroParl release. If you have already downloaded the EuroParl corpus from http://www.statmt.org/europarl/ and placed the source files in the EuroParlExtract folder, you can go directly to step 2. Otherwise, do the following:

```shell
cd europarl-extract-0.9
wget http://www.statmt.org/europarl/v7/europarl.tgz
tar xzf europarl.tgz
```
This will download and unpack the compressed corpus in the folder `europarl-extract-0.9/txt/`. **Attention:** Please retain the original directory structure and files names of the EuroParl corpus, otherwise the extraction will fail!

### 2. Remove XML Markup and Empty Lines

The original EuroParl source files need to be prepared for the use with EuroParlExtract. First, remove spurious XML markup, empty lines etc. with the supplied bash script `cleanSourceFiles.sh path_to_input_folder/`, e.g.:

```shell
./preprocess/cleanSourceFiles.sh txt/
```

### 3. Disambiguate Statement IDs

Next, run the script `disambiguate_speaker_IDs.py path_to_input_folder/` to avoid that two or more statements are assigned the same ID within one file. To do so, run:

```shell
python3 disambiguate_speaker_IDs.py txt/
```

### 4. Sentence Segmentation and Optional Tokenisation

For the extraction of **sentence-aligned parallel corpora, sentence segmentation is a required** pre-processing step, whereas in the case of comparable corpora sentence segmentation is not required (albeit useful for future analyses). Tokenisation is optional for both comparable and parallel corpora and therefore depends on end users' needs.

EuroParlExtract supports **two different third-party tools** users can choose from 1) *ixa-pipe-tok*, a sentence splitter and tokeniser implemented in Java by Rodrigo Agerri(see http://ixa2.si.ehu.es/ixa-pipes/); or 2) the sentence splitter and tokeniser of the *Europarl Preprocessing Tools* implemented in Perl by Philipp Koehn (see http://www.statmt.org/europarl/). The former is more accurate but considerably slower that the latter, so users should choose one of the tools according to their own preferences.

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

After the preliminary steps 1 to 4, the EuroParl source files are ready for the extraction process using the script `extract.py`.

**Comparable corpora**

To extract comparable corpora, the following arguements need to be provided:

- ` -sl {source language(s)}`: Choose one or more source language code(s) separated by blanks. To show a list of supported languages, do `python3 extract.py comparable --help`.
- `-tl {target language(s)}`: Choose one or more target language code(s) separated by blanks. To show a list of supported languages, do `python3 extract.py comparable --help`.
- `-i <input_folder>`:  Path to input folder containing EuroParl source files, usually txt/.
- `-o <output_folder>`: Path to output folder.
- `-s <statement_file>`: Optional argument to supply precompiled statement list (CSV format) rather than creating the list (recommended - this option extremly speeds up the extraction process!)
- `-al`: Optional argument to disseminate additional language tags acros source files (recommended - largely increases number of statements!)
- `-c {langs|xml|both}`: Optional argument to remove language identifier and/or speaker metadata from output files.

Fpr example:

```shell
$ python3 extract.py -sl PL SL BG -tl all -i txt/ -o corpora/ -s data/europarl_statements.csv -al -c both
# Extracts non-translated text in all EuroParl languages plus translation in all EuroParl languages from Polish, Slovene and Bulgarian 
```

To extract **parallel corpora**, do

```shell
./preprocess/segment-tokenise_EuroParl.sh txt/
```

For the extraction of **sentence-aligned parallel corpora, sentence segmentation is a required** pre-processing step, whereas in 

# TO DO REST
## Extract Comparable and/or Parallel Corpora


Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

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

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc

