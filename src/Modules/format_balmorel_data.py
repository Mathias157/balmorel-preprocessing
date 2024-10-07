"""
TITLE

Description

Created on 24.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

from Submodules.municipal_template import DataContainer
from clustering import convert_municipal_code_to_name
from geofiles import prepared_geofiles
from Submodules.utils import store_balmorel_input, join_to_gpd
from onshore_vre_func import onshore_vre_func
from heat_profiles_func import heat_profiles_func
import numpy as np
import xarray as xr
import pandas as pd
from pybalmorel import IncFile
import click
import os

#%% ------------------------------- ###
###      1. Utility Functions       ###
### ------------------------------- ###


#%% ------------------------------- ###
###            1. Main              ###
### ------------------------------- ###
    
@click.group()
@click.pass_context
@click.option("--model-path", type=str, required=True, help="Path of the Balmorel model")
@click.option("--scenario", type=str, required=True, help="Scenario to load results from")
@click.option("--load-again", type=bool, required=False, help="Load scenario results again and overwrite previously loaded .gdx?")
def main(ctx, model_path: str, scenario: str, load_again: bool = False):
    
    # Load Geodataframe with municipal codes and names
    ind, mun, country = prepared_geofiles('DK Municipalities')
    
    ## Convert æ, ø, å
    mun['NAME_2'] = (
        mun.NAME_2
        .str.replace('Æ', 'Ae')
        .str.replace('Ø', 'Oe')
        .str.replace('Å', 'Aa')
        .str.replace('æ', 'ae')
        .str.replace('ø', 'oe')
        .str.replace('å', 'aa') 
    )
    
    # Store globals     
    ctx.ensure_object(dict)
    ctx.obj['model_path'] = model_path
    ctx.obj['scenario'] = scenario
    ctx.obj['load_again'] = load_again
    ctx.obj['mun'] = mun
     
    

    
    
@main.command()
@click.pass_context
def heat_profiles(ctx):
    return heat_profiles_func(ctx)
    
    
@main.command()
@click.pass_context
def onshore_vre(ctx):
    return onshore_vre_func(ctx)

@main.command()
@click.pass_context
def grids(ctx):
    """A different way to merge the names through xarray

    Args:
        balmorel_model_path (str): _description_
        scenario (str): _description_
        load_again (bool): _description_
    """
        
    # Load Model
    file = 'Data/BalmorelData/municipal_connectivity.nc'
    if os.path.exists(file):
        y = xr.load_dataset(file)
    else:
        XINVCOST = store_balmorel_input('XINVCOST',
                            ['Y', 'RE', 'RI', 'connection'],
                            ctx.obj['balmorel_model_path'], ctx.obj['scenario'], ctx.obj['load_again'],
                            lambda x: x.query("Y == '2050' and (RE.str.contains('DK_') and RI.str.contains('DK_'))"), # Hardcoded for old database
                            False)

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
        y.connection.to_netcdf('Data/BalmorelData/municipal_connectivity.nc')    



@main.command()
@click.pass_context
def biomass_availability(ctx):
    
    # File from Bramstoft et al 2020
    f = pd.read_excel('Data/BalmorelData/DKBiomassAvailability.xlsx')
    # print(f)

if __name__ == '__main__':
    main()
    