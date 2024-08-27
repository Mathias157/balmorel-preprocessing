"""
Pre-Processing of the Varmeplan 2021 dataset

Aalborg dataset, can be used to get individual and district heat gross supply:
https://vbn.aau.dk/da/datasets/kommunepakker-varmeplan-danmark-2021
- Note that heat demand should be combined wrt. the s1-s5 scenarios (sums to 53.95 TWh without heat efficiency investments)

Python package requirements:
- xlrd 

Created on 26.08.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import geopandas as gpd
import os

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

class VPDK21:
    
    def __init__(self, scenario: str = 'SUM_GWh_uden_besp') -> None:    
        files = os.listdir('Data/AAU Kommuneplan')
        self.DH = pd.DataFrame()
        
        # Correcting Municipal Names
        correct_names = {'Aarhus' : 'Århus',
                         'HøjeTaastrup' : 'Høje Taastrup',
                         'Vesthimmerland' : 'Vesthimmerlands'}
        
        # Read municipal data
        for file in files:
            f = pd.read_excel(f'Data/AAU Kommuneplan/{file}/{file}_opsummering.xls')

            if file in correct_names.keys():
                file = correct_names[file]
            
            # Put municipality in index as multiindex
            f.index = pd.MultiIndex.from_product([[file], np.arange(len(f))],
                                                    names=['Municipality', 'Original'])
            
            # Categorise District Heating and Individual Heating
            f.Forsyning = f.Forsyning.str.replace('Andet', 'Individuel').replace('Biomasse', 'Individuel').replace('Elvarme', 'Individuel').replace('Naturgas', 'Individuel').replace('Olie', 'Individuel').replace('Varmepumpe', 'Individuel')
            
            # Sum to scenario
            f = f.pivot_table(index=['Municipality', 'Forsyning'], values=scenario, 
                              aggfunc='sum')
            
            self.DH = pd.concat((self.DH, f))
        
        
        # Convert to xarray
        self.DH = self.DH.to_xarray()
        
        
        # Assign to shapefile
        muni_geofile = gpd.read_file(r'Data\Shapefiles\Denmark\Adm\gadm36_DNK_2.shp')
        muni_geofile = muni_geofile[muni_geofile.NAME_2 != 'Christiansø']
        temp = muni_geofile[['geometry']]
        temp.index = muni_geofile.NAME_2
        # temp.index = muni_geofile.NAME_2
        temp.index.name = 'Municipality'
        
        self.ind = temp
        self.DH['geo'] = temp 



VP = VPDK21()

# VP = VP.DH

