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
import click
from Submodules.municipal_template import DataContainer

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
        

def load_transport_demand(include_bunkering: bool = False):
    """Loads Danish transport fuel demand in TWh

    Args:
        include_bunkering (bool, optional): Include bunkering demand or not. Defaults to False.

    Returns:
        pd.DataFrame: Most important fuel demands from 2000 to 2023
    """
    f = pd.read_excel('Data/Danmarks Statistik/Transportforbrug Type.xlsx', skiprows=2).iloc[:9,1:]
    f = (
        f
        .rename(columns={'Unnamed: 1': 'Fuel'})
        .pivot_table(index='Fuel')
        .pipe(lambda df: df.query('Fuel != "Fuelolie, bunkring af dansk opererede skibe i udlandet"\
                and Fuel != "Jetpetroleum, bunkring af dansk opererede fly i udlandet"\
                and Fuel != "Diesel, bunkring af danske opererede køretøjer i udlandet"') if not include_bunkering else df)
        # Remove negligible demand
        .query('Fuel != "Motorbenzin, farvet (ophørt fra 2016)"\
            and Fuel != "Motorbenzin, blyholdig"')
        # Convert to TWh
        .div(1e6)
        .mul(0.277777777)
    )
    return f

@click.command()
@click.option("--get-transport-demand", is_flag=True, help="Format transport demand")
@click.option("--include-bunkering", type=bool, required=False, help="Include bunkering in transport demand?")
@click.option("--get-industry-demand", is_flag=True, help="Format industry demand")
def main(get_transport_demand: bool = False,
         include_bunkering: bool = False,
         get_industry_demand: bool = False):
    if get_transport_demand:
        f = load_transport_demand(include_bunkering)
        f.to_csv('Data/Danmarks Statistik/transport_demand.csv', index=False)
    
    if get_industry_demand:
        ind = DKSTAT()
        ind.IND.to_netcdf('Data/Danmarks Statistik/industry_demand.nc')
        
if __name__ == '__main__':
    main()