# Balmorel Pre-Processing

This repository contains two tools for pre-processing Balmorel data, which are described below.

The necessary python packages can be installed in a virtual environment by following the commands below:


````
# Creating environment
python -m venv .new_env

# Activating environment
.new_env\Scripts\activate

# Installing packages
pip install -r requirements.txt
````

Or by using conda:
```` 
conda env create --name .new_env -f environment.yaml
````
conda requires an extra pip command to install the pybalmorel library:
```` 
pip install pybalmorel
````

See more here
https://www.gams.com/latest/docs/API_PY_GETTING_STARTED.html

## Raw Data Processing
These scripts process raw data into Balmorel input. An application is illustrated below (check zenodo link below for a high-res pdf). For more info, read README in the Raw Data Processing folder.

Data can be downloaded here, and should be placed in Raw Data Processing/
https://zenodo.org/records/10960910/files/Poster.pdf?download=1


## Processing Existing .inc Files
The idea behind the dataprocessing.py script in this folder is to run the part of Balmorel that does not include, 
  1) compiling the model
  2) solving the model
  3) post-processing results

I.e.: This will only load data (the inc-files)

Balmorel_ReadData.gms and Balmorelbb4_ReadData.inc are, therefore, alterations to a recent (as of 1.3.2024) Balmorel version, where all code that relates to compiling, solving or post-processing has been deleted  

dataprocessing.py will copy+paste these files into the Balmorel/base/model folder (or whatever scenario you want to read data from) that you specify in line 17 of dataprocessing.py.

It will then use the GAMS API to execute Balmorel_ReadData.gms and obtain the GDX database from it, from which all included data can be accessed as a pandas dataframe through the symbol_to_df function

An example of converting a pandas dataframe into an .inc file using the IncFile class is also included, which can be used to alter data or create scenarios
