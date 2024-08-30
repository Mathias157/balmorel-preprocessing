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
from Modules.Submodules.municipal_template import DataContainer

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###        1. Varmeplan 2021        ###
### ------------------------------- ###

class VPDK21:
    
    def __init__(self, scenario: str = 'SUM_GWh_uden_besp') -> None:    
        files = os.listdir('Data/AAU Kommuneplan')
        self.DH = pd.DataFrame()
        
        # Correcting Municipal Names
        correct_names = {'Aarhus' : 'Århus',
                         'HøjeTaastrup' : 'Høje Taastrup',
                         'Vesthimmerlands' : 'Vesthimmerland'}
        
        # Read varmeplan data
        for file in files:
            f = pd.read_excel(f'Data/AAU Kommuneplan/{file}/{file}_opsummering.xls')

            if file in correct_names.keys():
                file = correct_names[file]
            
            # Put municipality in index as multiindex
            f.index = pd.MultiIndex.from_product([[file], np.arange(len(f))],
                                                    names=['municipality', 'original'])
            
            # Categorise District Heating and Individual Heating
            f['user'] = (
                f.Forsyning.str
                .replace('Andet', 'individual')
                .replace('Biomasse', 'individual')
                .replace('Elvarme', 'individual')
                .replace('Naturgas', 'individual')
                .replace('Olie', 'individual')
                .replace('Varmepumpe', 'individual')
                .replace('Fjernvarme', 'district_heating')
                .astype('category')
            )
            
            # Store year of data collected
            f['year'] = 2019
            
            # Sum to scenario
            f = f.pivot_table(index=['year', 'municipality', 'user'], values=scenario, 
                              aggfunc='sum')
            
            self.DH = pd.concat((self.DH, f))
                
        # Convert to xarray
        self.DH = self.DH.to_xarray()
        self.DH = self.DH.rename({scenario : 'heat_demand_gwh'})
        
       

if __name__ == '__main__':
    data = DataContainer()
    VP = VPDK21()
    data.muni = data.muni.merge(VP.DH)

    # Plotting geometry
    geo = data.get_polygons('muni')
    for user in data.muni.user.data:
        geo[user] = data.muni.heat_demand_gwh.sel(user=user,
                                                  year=2019).data
        geo.plot(
                    column=user,
                    cmap='coolwarm',  # Add the cmap parameter here
                    legend=True  # Add the legend parameter here
                ).set_title(user + ' Heat Demand (GWh)')
