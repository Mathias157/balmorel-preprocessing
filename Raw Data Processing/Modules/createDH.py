"""
Created on 11.03.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from Modules.geofiles import preprocess_geofiles

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'
preprocess_geofiles()
#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

class DistrictHeat:
    
    def __init__(self) -> None:
        # Load data
        self.DH = pd.read_parquet('Data/Timeseries/DKMUNI36_DH.gzip')
        self.DHT = pd.read_parquet('Data/Timeseries/DKMUNI36_DH_VAR_T.gzip')
        self.geo = gpd.read_file('Data/Shapefiles/Balmorel Areas/Balmorel_areas.shp')
