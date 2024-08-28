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
                         'Vesthimmerlands' : 'Vesthimmerland'}
        
        # Read municipal data
        for file in files:
            f = pd.read_excel(f'Data/AAU Kommuneplan/{file}/{file}_opsummering.xls')

            if file in correct_names.keys():
                file = correct_names[file]
            
            # Put municipality in index as multiindex
            f.index = pd.MultiIndex.from_product([[file], np.arange(len(f))],
                                                    names=['Municipality', 'Original'])
            
            # Categorise District Heating and Individual Heating
            f['User'] = (
                f.Forsyning.str
                .replace('Andet', 'Individual')
                .replace('Biomasse', 'Individual')
                .replace('Elvarme', 'Individual')
                .replace('Naturgas', 'Individual')
                .replace('Olie', 'Individual')
                .replace('Varmepumpe', 'Individual')
                .replace('Fjernvarme', 'District Heating')
                .astype('category')
            )
            
            # Sum to scenario
            f = f.pivot_table(index=['Municipality', 'User'], values=scenario, 
                              aggfunc='sum')
            
            self.DH = pd.concat((self.DH, f))
                
        # Convert to xarray
        self.DH = self.DH.to_xarray()
        self.DH = self.DH.rename({scenario : 'Heat_Demand_GWh'})
        
        
        # Assign to shapefile
        muni_geofile = gpd.read_file(r'Data\Shapefiles\Denmark\Adm\gadm36_DNK_2.shp')
        temp = (
            muni_geofile.set_index('NAME_2')
            .copy()
            ['geometry']
        )
        temp.index.name = 'Municipality'
        
        self.DH['Polygons'] = temp 
        self.DH['Polygons'] = self.DH.Polygons.assign_attrs({'crs' : muni_geofile.crs})



VP = VPDK21()
VP.DH

# Getting the geometry:
for user in VP.DH.User.data:
    gpd.GeoDataFrame(
        geometry=VP.DH.Polygons.data, 
        crs=VP.DH.Polygons.crs
        ).plot(
                column=VP.DH.Heat_Demand_GWh.sel(User=user).data,
                cmap='coolwarm',  # Add the cmap parameter here
                legend=True  # Add the legend parameter here
            ).set_title(user + ' Heat Demand (GWh)')


