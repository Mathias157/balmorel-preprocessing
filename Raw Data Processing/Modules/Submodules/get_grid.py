"""
Get Grid 2D Array

Loads a grid from Balmorel using XINVCOST and a predefined shapefile

Created on 12.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###  1. Collect Grid from Balmorel  ### 
### ------------------------------- ###

# 1.1 Load Model
x = Balmorel(r'C:\Users\mberos\gitRepos\Balmorel')
x.load_incfiles('muni')

## Load transmission investment costs
XINVCOST = (
    symbol_to_df(x.input_data['muni'], 'XINVCOST', ['Y', 'RE', 'RI', 'connection'])
    .query('Y == "2050"')
    .query('RE.str.contains("DK_") and RI.str.contains("DK_")')
)

## Convert names and get 0/1 2D array
connectivity = (
    # Convert from muni code to name
    convert_municipal_code_to_name(
        convert_municipal_code_to_name(XINVCOST, 
                                    'RI', exclude_regions=[]), 
        'RE', exclude_regions=[])
    
    # Count connections (i.e.: is there a connection or not)    
    .pivot_table(index=['RE', 'RI'],  
                 values='connection', 
                 aggfunc='count', 
                 fill_value=0)
)
connectivity.index.names = ['municipality', 'municipality_to']

# 1.2 Merge to shapefile to include islands
x = DataContainer()
y = x.muni.merge(connectivity.to_xarray())

## Merge again
y = y.connection
y = y.rename({'municipality' : 'municipality_from',
          'municipality_to' : 'municipality'})
y = x.muni.merge(y)
y = y.rename({'municipality' : 'municipality_to'}).fillna(0)
y.connection.data = y.connection.data.astype(int)


## Check for islands with no connections
for i,row in y.connection.to_pandas().iterrows():
    if np.all(row == 0):
        print('No connections to %s'%i)


## Save
y.connection.to_netcdf('Data/Power Grid/municipal_connectivity.nc')