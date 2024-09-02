"""
Processing data from Danmarks Statistik

Industriforbrug per Municipality:
https://www.statistikbanken.dk/statbank5a/SelectVarVal/saveselections.asp


Created on 30.08.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import xarray as xr
from Modules.Submodules.municipal_template import DataContainer

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###       1. Danmarks Statistik     ###
### ------------------------------- ###


class DKSTAT():
    
    def __init__(self) -> None:
        # Energy per Type
        f2 = pd.read_excel(r'Data\Danmarks Statistik\Industriforbrug Type.xlsx',
                             header=2, index_col=1).T
        f2 = f2.drop(index='Unnamed: 0')
        
        ## Aggregate everything else than electricity and district heating
        f2.index = (
            f2.index
            .str.replace('El', 'electricity')
            .str.replace('Fjernvarme', 'district_heating')
            .str.replace('LPG inkl. raffinaderigas', 'other')
            .str.replace('Natur-, bio- og bygas', 'other')
            .str.replace('Flydende brændsel', 'other')
            .str.replace('Kul og koks', 'other')
            .str.replace('Træ og affald', 'other')
        )
        f2.index.name = 'user'
        f2 = f2.groupby('user').sum()
        
        self.IND = xr.Dataset(
            {
                "energy_demand_type_mwh" : (
                    ('year', 'user'),
                    f2.T * 277.77777777777777
                )
            },
            coords={'year' : [2018],
                    'user' : f2.index}
        )
        
        # Energy per Municipality
        f1 = pd.read_excel(r'Data\Danmarks Statistik\Industriforbrug Kommuner.xlsx',
                             skiprows=2, index_col=0)
        
        
        ## Correcting Municipal Names
        correct_names = {'Aarhus' : 'Århus',
                         'Høje-Taastrup' : 'Høje Taastrup',
                         'Vesthimmerlands' : 'Vesthimmerland'}
        for error_name in correct_names.keys():
            f1.index = f1.index.str.replace(error_name, correct_names[error_name])
            
        ## Conver to xarray
        f1 = xr.Dataset(
            {
                "energy_demand_mun_mwh" : (
                    ('year', 'municipality'),
                    f1.T * 277.77777777777777
                ) 
            },
            coords={'year' : [2018],
                    'municipality' : f1.index}
        )
        self.IND = self.IND.merge(f1)
        

        
if __name__ == '__main__':
    ind = DKSTAT()
    ind.IND
