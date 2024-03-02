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
from functions import symbol_to_df, IncFile, read_lines

# Path to the GAMS system directory
project_dir = r'C:\path\to\Balmorel\base\model' # <--- CHANGE THIS !!

# Copy Balmorel_ReadData and Balmorelbb4_ReadData 
# into the model folder if there isn't one already
for file in ['Balmorel_ReadData.gms', 'Balmorelbb4_ReadData.inc']:
    if not(os.path.exists(os.path.join(project_dir, file))):
        shutil.copyfile(file, os.path.join(project_dir, file))
        print(os.path.join(project_dir, file))
    

#%% ------------------------------- ###
###      1. Reading .inc-files      ###
### ------------------------------- ###

# Initialize GAMS Workspace
ws = gams.GamsWorkspace(working_directory=project_dir)

# Load the GAMS model
model_db = ws.add_job_from_file(project_dir + '/Balmorel_ReadData')

# Run the GAMS file
model_db.run()

# Get the database (will take some minutes, so run once as separate section with #%%)
out_db = model_db.get_out_db()

#%% 1.1 Read a specific symbol

# In this example, hydrogen demand is read (assuming the addon is activated!)
df = symbol_to_df(out_db, 'HYDROGEN_DH2', ['Y', 'R', 'Value'])

# Or something larger, like renewable generation profiles 
#df = symbol_to_df(out_db, 'SOLE_VAR_T')

# NOTE: The GAMS API converts string values to large integers (such as in GDATA,
# where GDFUEL can have the value NATGAS). 
# The Balmorelbb4_ReadData.inc therefore exports a csv of GDATA (as an example), 
# which can be loaded here to map the integer values to the actual strings  
GDATA_int = symbol_to_df(out_db, 'GDATA', ['G', 'Var', 'Value']) # <- contains large integer values instead of strings
GDATA_str = pd.read_csv(os.path.join(project_dir, 'GDATA.csv'))
# Get the integer value related to GDFUEL HYDROGEN:
H2_int = GDATA_str[(GDATA_str.GDATASET == 'GDFUEL') & (GDATA_str.Val == 'HYDROGEN')]
print(GDATA_int.loc[(GDATA_int.G == H2_int.GGG.iloc[0]) &\
                    (GDATA_int.Var == 'GDFUEL'), 'Value'])


#%% ------------------------------- ###
###     2. Manipulate and Save      ###
### ------------------------------- ###

### 2.1 Do your data manipulation
df['Value'] = df['Value'] * 1.2 # 20% more H2 demand everywhere, in all years


### 2.2 Create .inc file using the IncFile class in functions.py
incfile_path = r'C:\path\to\Balmorel\base\model' # <--- CHANGE THIS !!

# Define class and where to put the incfile relative to the project directory
DH2 = IncFile(name='HYDROGEN_DH2_test',
              path=incfile_path,
              prefix=read_lines('HYDROGEN_DH2_Prefix.inc', './'),
              suffix=read_lines('HYDROGEN_DH2_Suffix.inc', './'))

# Prefix and suffix could also be hardcoded like this:
# DH2.prefix = "line1\nline2\nline3"
# DH2.suffix = "line1\nline2\nline3"

# Define the actual table, by pivoting to get the actual format required 
# (YYY set in index, CCCRRRAAA set in columns)
df_for_export = df.pivot_table(index=['R'], columns=['Y'], values='Value').fillna('')

# Make sure 'R' and 'Y' (names of the index and columns) won't be exported 
df_for_export.index.name = ''
df_for_export.columns.name = ''

# Place this table in the body of the class
DH2.body = df_for_export.to_string()

# Save (will save to incfile_path)
DH2.save()
