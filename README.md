## Required packages 
pip install pandas as pd

pip install gamsapi[transfer]

See more here
https://www.gams.com/latest/docs/API_PY_GETTING_STARTED.html

### Processing Existing .inc Files
The idea behind the dataprocessing.py script in this folder is to run the part of Balmorel that does not include, 
  1) compiling the model
  2) solving the model
  3) post-processing results
I.e.: Only load inc-files.

Balmorel_ReadData.gms and Balmorelbb4_ReadData.inc are, therefore, alterations to a recent (as of 1.3.2024) Balmorel version, where all code that relates to compiling, solving or post-processing has been deleted  

dataprocessing.py will copy+paste these files into the Balmorel/base/model (or whatever scenario you want to read data from) folder that you specify in line 18 of dataprocessing.py 
It will then use the gams API to execute Balmorel_ReadData.gms and obtain the GDX database from it, from which all included data can be accessed as a pandas dataframe through the symbol_to_df function

An example of converting a pandas dataframe into an .inc file using the IncFile class is also included, which can be used to alter data or create scenarios


### Raw Data Processing
Will create Balmorel data from raw data
Scripts are not finished, and raw data not included in this repository
