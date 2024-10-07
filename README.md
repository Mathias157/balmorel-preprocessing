# Balmorel Pre-Processing

These scripts process raw data into Balmorel input for a 2050 brownfield model of the Danish energy system at municipal spatial resolution (99 nodes). The data is processed for the [following branch of Balmorel](https://github.com/balmorelcommunity/Balmorel/tree/mberos-spatialaggregation), with [this input data repository](https://github.com/balmorelcommunity/Balmorel_data/tree/mberos-spatialaggregation).

An application presented at the EGU24 conference is illustrated in the poster below (check Zenodo link below for a high-res pdf). For more info, read README in the src folder.
![Application example](https://github.com/Mathias157/balmorel-preprocessing/blob/master/Raw%20Data%20Processing/Conference%20Poster%20for%20Analysis%20of%20Spatial%20Resolutions%20for%20Modelling%20Sector-Coupled%20Energy%20Systems.png)

Data can be downloaded in the Zenodo link below and should be placed in src/

https://zenodo.org/records/10960910

## Installation

The necessary python packages can be installed in a virtual environment by following the command below:

```` 
conda env create -f environment.yaml
````

This requires [anaconda](https://www.anaconda.com/download?utm_source=anacondadoc&utm_medium=documentation&utm_campaign=download&utm_content=topnavalldocs) (or the more lightweight [miniconda](https://docs.anaconda.com/miniconda/#miniconda-latest-installer-links)) installs an environment with the following packages:
````
name: spatialstudy
channels:
  - conda-forge
  - bioconda
dependencies:
  - Cartopy=0.23.0
  - geopandas=1.0.1
  - matplotlib=3.9.2
  - ipywidgets=8.1.3
  - nbformat=5.9.2
  - numpy=1.26.2
  - openpyxl=3.1.2
  - pandas=2.1.4
  - plotly=5.16.1
  - pyarrow=15.0.1
  - pyproj=3.6.1
  - scipy=1.11.2
  - shapely=2.0.2
  - atlite=0.2.12
  - xarray=2024.2.0
  - xlrd=2.0.1
  - graphviz
  - python-graphviz
  - click
  - snakemake-minimal
  - pip
  - pip:
    - gamsapi[transfer]==45.7.0
    - pybalmorel==0.3.10
````

## Get Started

The processing is initiated through a snakemake command in a command-line interface in the src directory. If using windows, the pre-processing can be run by calling `preprocessing` and the clustering through `clustering`. If on other systems, do either of the following commands:
```
snakemake -s workflow/preprocessing
snakemake -s workflow/clustering
```
A plot of the processes can be found [here](src/Analysis/preprocessing_dag.pdf). Note that vre_profiles.py and existing_powerplants is currently not part of the snakemake process, but the output from vre_profiles.py is used in the offshore_wind process. 