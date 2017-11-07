# EuroParlExtract

EuroParlExtract is a user-friendly corpus processing toolkit for the compilation of directional sub-corpora, both comparable and parallel ones, from the original release of the European Parliament Proceedings Parallel Corpus (EuroParl) by Philipp Koehn (2005). It therefore aims to maximise the utility of the EuroParl corpus, which in its original release does not provide support to compile directional subcorpora (i.e. corpora where the source and target language are made explicit for each language pair) and is therefore of limited use for linguistic translation research.

The motivation behind the project is to make the wealth of linguistic data contained in the EuroParl corpus easily available to researchers and students in the field of translation studies and contrastive linguistics, even if they lack advanced scripting/programming skills. EuroParlExtract is therefore conceived as an addition to EuroParl aiming to lower the barrier to corpus-driven contrastive research.

## Getting Started

These step-by-step instructions will guide you through all steps of the corpus extraction process. Since EuroParlExtract does not contain any corpus data, you will need to donload the original EuroParl release and apply to it the scripts provided in EuroParlExtract.

### 1. Install EuroParlExtract

To run EuroParlExtract, you will need to install Python as well as a series of Python packages (to do). Once your Python environment has been set up accordingly, you just need to download and unpack EuroParlExtract.

````shell
wget https://github.com/mustaszewski/europarl-extract/archive/v0.9.tar.gz
tar xzf v0.9.tar.gz
cd europarl-extract-0.9
````
### 2. Get EuroParl Source Files

If you have not yet downloaded the EuroParl corpus from http://www.statmt.org/europarl/ and placed it in the EuroParlExtract folder, do the following:

```shell
wget http://www.statmt.org/europarl/v7/europarl.tgz
tar xzf europarl.tgz
```
### Preprocess Source Files

```shell
./preprocess/cleanSourceFiles.sh txt/
tar xzf europarl.tgz
```

### Installing

A step by step series of examples that tell you have to get a development env running

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

