# Balmorel Pre-Processing

These scripts process raw data into Balmorel input for a 2050 brownfield model of the Danish energy system at municipal spatial resolution (99 nodes). The data is processed for the [following branch of Balmorel](https://github.com/balmorelcommunity/Balmorel/tree/dk-highspatialres), with [this input data repository](https://github.com/balmorelcommunity/Balmorel_data/tree/dk-highspatialres).

An application presented at the EGU24 conference is illustrated in the poster below (check Zenodo link below for a high-res pdf and [this tag](https://github.com/Mathias157/balmorel-preprocessing/tree/egu24-poster)). For more info, read README in the src folder.
![Application example](https://github.com/Mathias157/balmorel-preprocessing/blob/egu24-poster/Raw%20Data%20Processing/Conference%20Poster%20for%20Analysis%20of%20Spatial%20Resolutions%20for%20Modelling%20Sector-Coupled%20Energy%20Systems.png)

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
snakemake -s preprocessing
snakemake -s clustering
```
A plot of the process workflow can be found [here](src/Analysis/preprocessing_dag.pdf).
Remember to examine the `assumptions.yaml` used for pre-processing data and the `clustering.yaml` for clustering configurations, e.g. assumptions on grid investment costs and cluster size, respectively. Clustering assumes that a functioning Balmorel model is placed in the model_path written in `clustering.yaml`, as data from a Balmorel scenario needs to be read. 

### Hierarchical Clustering

It is possible to do hierarchical clustering by running the `clustering` command (or in Linux/Mac: `snakemake -s clustering`) twice with different configurations and some copying of files in between. Follow this procedure:
1) Run the clustering command with `second_order: False` of your 'base' scenario at a desired cluster size X.
2) Copy (don't remove yet!) the produced .inc files in ClusterOutput to the data of a new scenario in Balmorel, check [this guide](https://balmorelcommunity.github.io/Balmorel/get_started/scenario_setup.html) on how to setup Balmorel scenarios.
3) Run the clustering command with `second_order: True` of the new scenario at a new cluster size Y that is less than X from step 1. 
4) Only some .inc files in ClusterOutput was replaced in the second order clustering. Once again copy all of the .inc files in ClusterOutput to another new scenario in Balmorel (including the .inc files that was not overwritten and remains from step 1)

This procedure will have generated two new scenarios, one with X clusters for all carriers and investment options (step 2), and one with X clusters for heat and investment options linked to Y clusters for electricity and hydrogen.  