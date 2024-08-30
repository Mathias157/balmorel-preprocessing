"""
Pre-Processing of the Varmeplan 2021 dataset

Aalborg dataset, can be used to get individual and district heat gross supply:
https://vbn.aau.dk/da/datasets/kommunepakker-varmeplan-danmark-2021
- Note that heat demand should be combined wrt. the s1-s5 scenarios (sums to 53.95 TWh without heat efficiency investments)

Assumption for distribution of low-, mid- and high temperatures should probably come from:
Viegand Maagø and Energistyrelsen. ‘Kortlægning Af Energiforbrug Og Opgørelse Af Energisparepotentialer i Produktionserhvervene’, 2022.
See page 8:
“
- Omkring 45% af forbruget ligger ved temperaturer under 100 ºC – totalt 26.798 TJ/år 
- Godt 40% ligger ved temperaturer over 200 ºC – totalt 23.774 TJ/år 
- Resten, altså ca. 15%, ligger i intervallet 100 – 200 ºC eller derover
”, Viegand Maagø and Energistyrelsen, 2022, p. 8

One simple, first assumption could be to say that 40-55% is high temperature, 
and use that amount of TJ to distribute the sum of TJ in the "over 80C" category
of Aalborg data into high and middle temperature (middle temperature is the remaining over 80C)  

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
        
        # Loop through varmeplan data
        for file in files:
            ## Get summary data
            f = pd.read_excel(f'Data/AAU Kommuneplan/{file}/{file}_opsummering.xls')

            if file in correct_names.keys():
                file = correct_names[file]
            
            ## Get industry surplus heat supply
            f2 = gpd.read_file(f'Data/AAU Kommuneplan/{file}/gis_data/{file}_industri.shp')
            print(f2.to_string())
            
            ## Put municipality in index as multiindex
            f.index = pd.MultiIndex.from_product([[file], np.arange(len(f))],
                                                    names=['municipality', 'original'])
            
            ## Categorise District Heating and Individual Heating
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
            
            ## Store Industry

            
            ## Store year of data collected
            f['year'] = 2019
            
            ## Sum to scenario
            f = f.pivot_table(index=['year', 'municipality', 'user'], values=scenario, 
                              aggfunc=lambda x: np.sum(x)*1e3) # To MWh
            
            self.DH = pd.concat((self.DH, f))
                
        # Convert to xarray
        self.DH = self.DH.to_xarray()
        self.DH = self.DH.rename({scenario : 'heat_demand_mwh'})
        
       

if __name__ == '__main__':
    data = DataContainer()
    VP = VPDK21()
    data.muni = data.muni.merge(VP.DH)

    # Plotting geometry
    geo = data.get_polygons('muni')
    for user in data.muni.user.data:
        geo[user] = data.muni.heat_demand_mwh.sel(user=user,
                                                  year=2019).data
        geo.plot(
                    column=user,
                    cmap='coolwarm',  # Add the cmap parameter here
                    legend=True       # Add the legend parameter here
                ).set_title(user + ' Heat Demand (MWh)')
