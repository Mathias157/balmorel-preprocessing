"""
Created on 01.03.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import pandas as pd
import gams
import os
import shutil
from functions import symbol_to_df, IncFile, ReadIncFilePrefix

# Path to the GAMS system directory
project_dir = r'path\to\Balmorel\base\model' # <--- CHANGE THIS !!

# Copy Balmorel_ReadData and Balmorelbb4_ReadData into the model folder
shutil.copyfile('Balmorel_ReadData.gms', project_dir + '/Balmorel_ReadData.gms')
shutil.copyfile('Balmorelbb4_ReadData.inc', project_dir + '/Balmorelbb4_ReadData.inc')


#%% ------------------------------- ###
###      1. Reading .inc-files      ###
### ------------------------------- ###

# Initialize GAMS Workspace
ws = gams.GamsWorkspace(working_directory=project_dir)

# Load the GAMS model
model_db = ws.add_job_from_file(project_dir + '/Balmorel_ReadData')

# Run the GAMS file
model_db.run()

# Get the database
out_db = model_db.get_out_db()

#%% 1.1 Read the specific symbol

# In this example, hydrogen demand is read (assuming the addon is activated!)
df = symbol_to_df(out_db, 'HYDROGEN_DH2', ['Y', 'R', 'Value'])


# Or something larger, like renewable generation profiles 
#df = symbol_to_df(out_db, 'SOLH_VAR_T')


### 1.2 Do your data manipulation
df['Value'] = df['Value'] * 1.2 # 20% more demand everywhere, in all years


#%% 1.2 Create .inc file using the IncFile class in functions.py

incfile_path = r'C:\path\to\Balmorel\base\data' # <--- CHANGE THIS !!

# Define class and where to put the incfile relative to the project directory
DH2 = IncFile(name='HYDROGEN_DH2_test',
              path=incfile_path)


# Define the first lines of the incfile, end with a space
DH2.prefix ="""PARAMETER HYDROGEN_DH2(YYY,CCCRRRAAA)  'Yearly demand for hydrogen at a Regional level(MWh of H2)';                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
TABLE HYDROGEN_DH22(CCCRRRAAA,YYY)
"""

# Define the actual table, by pivoting to get the actual format required 
# (YYY set in index, CCCRRRAAA set in columns)
df_for_export = df.pivot_table(index=['R'], columns=['Y'], values='Value').fillna('')

# Make sure 'R' and 'Y' (names of the index and columns) won't be exported 
df_for_export.index.name = ''
df_for_export.columns.name = ''

# Place this table in the body of the class
DH2.body = df_for_export.to_string()


# Define the last lines, start with a space 
DH2.suffix="""
;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
HYDROGEN_DH2(YYY,CCCRRRAAA) = HYDROGEN_DH22(CCCRRRAAA,YYY);                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 
HYDROGEN_DH22(CCCRRRAAA,YYY)=0; 
"""

# Save (will save to incfile_path)
DH2.save()
