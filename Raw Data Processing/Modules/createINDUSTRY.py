"""
Created on 14.03.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)

Script for creating data for industry sector
 
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import os 
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import geopandas as gpd
from Modules.geofiles import prepared_geofiles
from shapely.geometry import Point

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

choice = 'NUTS3'
the_index, areas, c = prepared_geofiles(choice)


#%% 1.0 Assumptions
XHLOSS = 0.1        # MWh/Mwh
XHCOST = 0.001      # €/Mwh
XHINVCOST = 396000  # €/MW


### 1.1 Load 
class Industry:
    """Class for district heating data
    
    Existing datasets:
        - Denmark

    Args:
        dataset (str, optional): _description_. Defaults to 'DK'.
    """
    
    def __init__(self, dataset: str = 'EUBalmorel') -> None:
        if dataset.lower() == 'eubalmorel': 
            choice = 'NordpoolReal'
            the_index, self.geo, c = prepared_geofiles(choice)
            
            # Load data
            datasets = pd.Series([ds0 for ds0 in os.listdir('Data/BalmorelData') if 'INDUSTRY' in ds0])

            for ds in datasets:
                setattr(self, ds.replace('INDUSTRY_', '').replace('.gzip', ''), pd.read_parquet('Data/BalmorelData/' + ds))
            
        else:
            print("Dataset doesn't exist - this is an empty object\n")
            print("Available datasets:\n- EUBalmorel (default)")

        # Load high resolution dataset
        self.PS = pd.read_csv('Data/Gas, Transport and Industry Data/Industrial_Database.csv',
                              sep=';', encoding='UTF-8')
        self.PS['geometry'] = gpd.GeoSeries([Point(xy) for xy in zip(self.PS.Longtitude, self.PS.Latitude)])
        self.PS.geometry.crs = 'EPSG:4326'
        self.PS = gpd.GeoDataFrame(self.PS)


IND = Industry()

#%% 1.1 Take a look at DK
fig, ax = plt.subplots()
IND.geo.loc[['DK1', 'DK2']].plot(ax=ax)
IND.PS[IND.PS.Country == 'Denmark'].plot(ax=ax, marker='o', color='r',
                                         markersize=IND.PS.loc[IND.PS.Country == 'Denmark', 
                                                               'Emissions_ETS_2014']/1e4)

# Need to make incfiles:
# INDUSTRY_AGKN
# INDUSTRY_CCCRRRAAA
# INDUSTRY_RRRAAA
# INDUSTRY_AAA
# INDUSTRY_GKFX
# INDUSTRY_DH
# INDUSTRY_DH_VAR_T
# INDUSTRY_DE
# INDUSTRY_DE_VAR_T

# Later:
# INDUSTRY_XHMAXK
# INDUSTRY_XHKFX
# INDUSTRY_XHLOSS
# INDUSTRY_XHCOST
# INDUSTRY_XHINVCOST
