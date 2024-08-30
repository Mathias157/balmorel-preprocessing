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
- E.g.: 
- 59496 TJ/år in total
- 32723 TJ/år for >100 C (55%)
AAU data:
GJ_over_80    17.1217 %       3369.050427 TJ
GJ_60_80C     12.1648 %       2393.687324 TJ
GJ_under_6    70.7135 %       13914.38463 TJ
..doesn't really fit - maybe the assumption that surplus heat above 80C comes from high, 60-80C from mid and below 60C from low is good enough?
for that to be true:
- 45% is low => 25.71% left from GJ under 60C
- 15% is mid => 10.71% left from GJ under 60C
- 40% is high => 10.71% of < 60C, 12.1648% of GJ_60_80C and 17.1217%

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
        self.IND = pd.DataFrame()
        
        # Correcting Municipal Names
        correct_names = {'Aarhus' : 'Århus',
                         'Høje_Taastrup' : 'Høje Taastrup',
                         'Vesthimmerlands' : 'Vesthimmerland'}
        
        # Loop through varmeplan data
        for file in files:
            ## Get summary data
            f = pd.read_excel(f'Data/AAU Kommuneplan/{file}/{file}_opsummering.xls')
            
            ## Get industry surplus heat supply
            f2 = gpd.read_file(f'Data/AAU Kommuneplan/{file}/gis_data/{file}_industri.shp')
            
            if file in correct_names.keys():
                file = correct_names[file]
                
                
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
            f2 = pd.DataFrame(
                f2[['GJ_over_80', 'GJ_60_80C', 'GJ_under_6']].sum()
            ).T
            f2.index = [file]
            f2.index.name = 'municipality'
            self.IND = pd.concat((self.IND, f2))

            
            ## Store year of data collected
            f['year'] = 2019
            
            ## Sum to scenario
            f = f.pivot_table(index=['year', 'municipality', 'user'], values=scenario, 
                              aggfunc=lambda x: np.sum(x)*1e3) # To MWh
            
            self.DH = pd.concat((self.DH, f))
                
        # Assign heat temperatures, based on surplus heat (read assumption in script description)
        self.IND['industry_phl'] = 0.45*self.IND.GJ_under_6 
        self.IND['industry_phm'] = 0.15*self.IND.GJ_under_6
        self.IND['industry_phh'] = (0.1071*self.IND.GJ_under_6 + self.IND.GJ_60_80C + self.IND.GJ_over_80) 
        
        ## Normalise to total surplus heat
        self.IND = self.IND.drop(columns=['GJ_over_80', 'GJ_60_80C', 'GJ_under_6'])
        total_surplus_heat = self.IND.sum().sum()
        self.IND['industry_phl'] = self.IND['industry_phl'] /  total_surplus_heat
        self.IND['industry_phm'] = self.IND['industry_phm'] /  total_surplus_heat
        self.IND['industry_phh'] = self.IND['industry_phh'] /  total_surplus_heat
        temp = pd.DataFrame(index=pd.MultiIndex.from_product(([2019], self.IND.index, ['industry_phl',
                                                                              'industry_phm',
                                                                              'industry_phh'])))
        temp.index.names = ['year', 'municipality', 'user']
        temp.loc[(2019, slice(None), 'industry_phl'), 'heat_demand_normalised'] = self.IND.industry_phl.values
        temp.loc[(2019, slice(None), 'industry_phm'), 'heat_demand_normalised'] = self.IND.industry_phm.values
        temp.loc[(2019, slice(None), 'industry_phh'), 'heat_demand_normalised'] = self.IND.industry_phh.values
                
        # Convert to xarray
        self.DH = self.DH.to_xarray()
        self.DH = self.DH.rename({scenario : 'heat_demand_mwh'})
        self.IND = temp.to_xarray()
       

if __name__ == '__main__':
    data = DataContainer()
    VP = VPDK21()
    data.muni = data.muni.merge(VP.DH)
    data.muni = data.muni.merge(VP.IND)

    # Plotting geometry
    geo = data.get_polygons('muni')
    for user in data.muni.user.data:
        if user == 'district_heating' or user == 'individual':
            geo[user] = data.muni.heat_demand_mwh.sel(user=user,
                                                    year=2019).data
            unit = 'MWh'
        else:
            geo[user] = data.muni.heat_demand_normalised.sel(user=user,
                                                    year=2019).data
            unit = 'normalised'
        
        geo.plot(
                    column=user,
                    cmap='coolwarm',  # Add the cmap parameter here
                    legend=True       # Add the legend parameter here
                ).set_title(user + f' Heat Demand ({unit})')
