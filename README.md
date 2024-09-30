# Balmorel Pre-Processing

These scripts process raw data into Balmorel input for a 2050 greenfield model of the Danish energy system at municipal spatial resolution (99 nodes). 

An application presented at the EGU24 conference is illustrated in the poster below (check Zenodo link below for a high-res pdf). For more info, read README in the src folder.
![Application example](https://github.com/Mathias157/balmorel-preprocessing/blob/master/Raw%20Data%20Processing/Conference%20Poster%20for%20Analysis%20of%20Spatial%20Resolutions%20for%20Modelling%20Sector-Coupled%20Energy%20Systems.png)

Data can be downloaded in the Zenodo link below and should be placed in src/

https://zenodo.org/records/10960910

## Installation

The necessary python packages can be installed in a virtual environment by following the command below:

```` 
conda env create -f environment.yaml
````

## Get Started

The processing is initiated through a snakemake command in a command-line interface in the src directory.
A plot of the processes can be found [here](src/Analysis/snakemake_dag.pdf). Note that vre_profiles.py and existing_powerplants is currently not part of the snakemake process, but the output from vre_profiles.py is used in the offshore_wind process. 