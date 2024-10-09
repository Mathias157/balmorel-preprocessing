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
from Submodules.utils import store_balmorel_input
from onshore_vre_func import onshore_vre_func
from heat_profiles_func import heat_profiles_func
import numpy as np
from pybalmorel import IncFile
import pandas as pd
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
@click.option("--model-path", type=str, required=False, default='.', help="Path of the Balmorel model")
@click.option("--scenario", type=str, required=False, default='base', help="Scenario to load results from")
@click.option("--load-again", type=bool, required=False, help="Load scenario results again and overwrite previously loaded .gdx?")
def main(ctx, model_path: str, scenario: str, load_again: bool = False):
    """CLI to convert Balmorel data from previous studies"""
    
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
    """Get heat profiles from Bramstoft, Rasmus, Amalia Pizarro-Alonso, Ida Græsted Jensen, Hans Ravn, and Marie Münster. “Modelling of Renewable Gas and Renewable Liquid Fuels in Future Integrated Energy Systems.” Applied Energy 268 (June 15, 2020): 114869. https://doi.org/10.1016/j.apenergy.2020.114869."""
    return heat_profiles_func(ctx)
    
    
@main.command()
@click.pass_context
def onshore_vre(ctx):
    """Get onshore VRE profiles from previous study presented at EGU24, https://github.com/Mathias157/balmorel-preprocessing/releases/tag/egu24-poster"""
    return onshore_vre_func(ctx)

@main.command()
@click.pass_context
def grids(ctx):
    """Create the connectivity matrix from previous Balmorel run"""
        
    # Load Model
    file = 'Data/BalmorelData/municipal_connectivity.nc'
    if not(os.path.exists(file)):
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
@click.option('--woodpot', type=float, required=True, help="Domestic potential of woody biomass")
@click.option('--strawpot', type=float, required=True, help="Domestic potential of agricultural biomass")
@click.option('--biogaspot', type=float, required=True, help="Domestic potential of biogas")
@click.option('--woodimport', type=bool, required=True, help="Allow import of woodpellets to large cities?")
@click.pass_context
def biomass_availability(ctx, woodpot: float, strawpot: float, biogaspot: float, woodimport: bool):
    """Get biomass distribution key from Bramstoft et al 2020, assume total availability.
    
    Distribution potentials:
    Bramstoft, Rasmus, Amalia Pizarro-Alonso, Ida Græsted Jensen, Hans Ravn, and Marie Münster. “Modelling of Renewable Gas and Renewable Liquid Fuels in Future Integrated Energy Systems.” Applied Energy 268 (June 15, 2020): 114869. https://doi.org/10.1016/j.apenergy.2020.114869.
    """
    
    # File from Bramstoft et al 2020
    df = pd.read_excel('Data/BalmorelData/DKBiomassAvailability.xlsx').drop(columns='Flow')
    df.columns = ['Y', 'CRA', 'F', 'Value']
    
    ## Format
    df['Y'] = (
        df.Y
        .astype(str)
        .str.replace('2020', '2050')
    )
    df['CRA'] = (
        df.CRA
        .str.replace('Hoeje_Taastrup', 'Hoeje-Taastrup')
    )
    df['F'] = (
        df.F
        .str.replace('_Gen', '')
        .str.replace('WOOD_PELLETS', 'WOODPELLETS')
    ) 
    df['Value'] = (
        df.Value
        .astype(str)
        .str.replace('EPS', '0')
        .astype(float)
    )
    
    # Make .inc-file
    f = IncFile(name='GMAXF', path='Output',
                prefix="TABLE GMAXF(YYY, CCCRRRAAA, FFF) 'Maximum fuel use (GJ) per year'\n",
                suffix='\n;\n', 
                body=df)
    
    ## Set national levels
    f.suffix += "\n".join([
        "GMAXF('2050', 'DENMARK', 'BIOGAS') = %0.2f;"%(biogaspot*1e6),
        "GMAXF('2050', 'DENMARK', 'WOODCHIPS') = EPS;",
        "GMAXF('2050', 'DENMARK', 'WOODWASTE') = EPS;",
        "GMAXF('2050', 'DENMARK', 'STRAW') = %0.2f;"%(df.query('CRA != "DENMARK" and F == "STRAW"')['Value'].sum()),
        "GMAXF('2050', 'DENMARK', 'WOOD') = %0.2f;"%(df.query('CRA != "DENMARK" and F == "WOOD"')['Value'].sum()),
        "* Use existing potentials as distribution key for input potentials for straw and wood, defined below",
        "GMAXF('2050', CCCRRRAAA, 'STRAW') = GMAXF('2050', CCCRRRAAA, 'STRAW') / GMAXF('2050', 'DENMARK', 'STRAW') * %0.2f;"%(strawpot*1e6), # From PJ to GJ
        "GMAXF('2050', CCCRRRAAA, 'WOOD') = GMAXF('2050', CCCRRRAAA, 'WOOD') / GMAXF('2050', 'DENMARK', 'WOOD') * %0.2f;"%(woodpot*1e6), # From PJ to GJ
    ])
    
    if not(woodimport):
        f.suffix += "\n* Disallow import of woodpellets\nGMAXF('2050', 'DENMARK', 'WOODPELLETS') = EPS;"
    else:
        f.suffix += "\n* Allow import of woodpellets\nGMAXF('2050', 'DENMARK', 'WOODPELLETS') = %0.2f;"%(df.query('CRA != "DENMARK" and F == "WOODPELLETS"')['Value'].sum())
    
    # Municipal waste
    f.suffix += "\nGMAXF(Y,'DENMARK','MUNIWASTE') = 763308;"
    
    f.body_prepare(index=['Y', 'CRA'], columns='F', values='Value')
    
    ## Zeros have to be EPS
    idx = f.body.values == 0
    f.body[idx] = 'EPS'
    f.save()

if __name__ == '__main__':
    main()
    