"""
TITLE

Description

Created on 24.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

from gams import GamsWorkspace
from pybalmorel import Balmorel
from pybalmorel.utils import symbol_to_df
from Submodules.municipal_template import DataContainer
from clustering import convert_municipal_code_to_name
import geopandas as gpd
from geofiles import prepared_geofiles
import numpy as np
import xarray as xr
from typing import Tuple
import pandas as pd
from pybalmorel import IncFile
import click
import os

#%% ------------------------------- ###
###      1. Utility Functions       ###
### ------------------------------- ###

def store_balmorel_input(symbol: str,
                         columns: list,
                         balmorel_model_path: str, 
                         scenario: str,
                         load_again: bool = False,
                         filter_func: Tuple[None, callable] = None,
                         save: bool = True):
    
    balm = Balmorel(balmorel_model_path)
    
    # Check if the symbol.gzip exists
    if '%s.gzip'%symbol in os.listdir('Data/BalmorelData'):
        print('\n%s.gzip already exists\n'%symbol)
        f = pd.read_parquet('Data/BalmorelData/%s.gzip'%symbol)
    else:
        # Check Balmorel input has been loaded
        if not('muni_input_data.gdx' in os.listdir(os.path.join(balm.path, 'muni', 'model'))) or load_again == True:      
            print('\nLoading results into %s_input_data.gdx...\n'%scenario)
            balm.load_incfiles(scenario)
        else:
            print('\n%s_input_data.gdx already loaded!'%scenario)
            print('Loading %s_input_data.gdx...\n'%(os.path.join(balm.path, 'muni', 'model', scenario)))
            
            # Load the input
            ws = GamsWorkspace()
            balm.input_data[scenario] = ws.add_database_from_gdx(os.path.join(balm.path, 'muni', 'model', '%s_input_data.gdx'%scenario))

        # Get symbol
        f = symbol_to_df(balm.input_data[scenario], symbol, columns)
        if filter_func != None:
            f = filter_func(f)
            
        if save:
            f.to_parquet('Data/BalmorelData/%s.gzip'%symbol)
        
    return f

def join_to_gpd(df: pd.DataFrame,
                left_col: str,
                gpd: gpd.GeoDataFrame,
                right_col: str,
                new_col: list, 
                suffix: Tuple[None, str] = None):
    if suffix != None:
        df[left_col] = df.A.str.replace(suffix, '')
    df.index = df[left_col]
    df = df.join(gpd[right_col])
    df.columns = new_col
    df.index = range(len(df))
    if suffix != None:
        df[left_col] = df[left_col] + suffix
    
    return df 

def get_grid(balmorel_model_path: str,
             scenario: str, load_again: bool):
    """A different way to merge the names through xarray

    Args:
        balmorel_model_path (str): _description_
        scenario (str): _description_
        load_again (bool): _description_
    """
        
    # 1.1 Load Model
    file = 'Data/BalmorelData/municipal_connectivity.nc'
    if os.path.exists(file):
        y = xr.load_dataset(file)
    else:
        XINVCOST = store_balmorel_input('XINVCOST',
                            ['Y', 'RE', 'RI', 'connection'],
                            balmorel_model_path, scenario, load_again,
                            lambda x: x.query("Y == '2050' and (RE.str.contains('DK_') and RI.str.contains('DK_'))"),
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
    
    return y

#%% ------------------------------- ###
###            1. Main              ###
### ------------------------------- ###
    
@click.command()
@click.option("--model-path", type=str, required=True, help="Path of the Balmorel model")
@click.option("--scenario", type=str, required=True, help="Scenario to load results from")
@click.option("--load-again", type=bool, required=False, help="Load scenario results again and overwrite previously loaded .gdx?")
def main(model_path: str, scenario: str, load_again: bool = False):
    # 1.1 Load Geodataframe with municipal codes and names
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
    
    # 1.2 Load DH_VAR_T
    df = store_balmorel_input('DH_VAR_T', ['A', 'DHUSER', 'S', 'T', 'Value'], 
                         model_path, scenario, load_again, 
                         lambda x: x.loc[x.A.str.contains('DK_')].query("DHUSER == 'RESH'"))
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', mun, 'NAME_2', 
                     ['A_old', 'DHUSER', 'S', 'T', 'Value', 'A'], '_A')
        
    ### 1.2.1 Save DH_VAR_T.inc
    incfile = IncFile(name='DH_VAR_T', path='Output',
                      prefix='\n'.join([
                            "PARAMETER DH_VAR_T(AAA,DHUSER,SSS,TTT) 'Variation in heat demand';",
                            "TABLE DH_VAR_T1(SSS,TTT,AAA,DHUSER)",
                            ""
                      ]),
                      body=df,
                      suffix='\n'.join([
                            "",
                            ";",
                            "DH_VAR_T(AAA,'RESH',SSS,TTT) = DH_VAR_T1(SSS,TTT,AAA,'RESH');",
                            "DH_VAR_T1(SSS,TTT,AAA,DHUSER) = 0;",
                            "DH_VAR_T('Herlev_A','RESH',SSS,TTT) = DH_VAR_T('Ballerup_A','RESH',SSS,TTT);"
                      ]))
    incfile.body_prepare(['S', 'T'],
                         ['A', 'DHUSER'])
    incfile.save()
    
    ### 1.2.2 Save INDIVUSERS_DH_VAR_T
    df['A'] = df.A.str.replace('_A', '_IDVU-SPACEHEAT')
    df['DHUSER'] = 'RESIDENTIAL'
    incfile = IncFile(name='INDIVUSERS_DH_VAR_T', path='Output',
                    prefix='\n'.join([
                    "TABLE DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER)",
                    ""
                    ]),
                    body=df,
                    suffix='\n'.join([
                        "",
                        ";",
                        "DH_VAR_T(AAA,DHUSER,SSS,TTT)$(SUM((S,T), DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER))) = DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER);",
                        "DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER) = 0;",
                        "DH_VAR_T('Herlev_A','RESIDENTIAL',SSS,TTT) = DH_VAR_T('Ballerup_A','RESIDENTIAL',SSS,TTT);"
                    ]))
    incfile.body_prepare(['S', 'T'],
                         ['A', 'DHUSER'])
    incfile.save()
    
    # 1.3 Load and Save WND_VAR_T
    df = store_balmorel_input('WND_VAR_T', ['A', 'S', 'T', 'Value'], 
                         model_path, scenario, load_again, 
                         lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', mun, 'NAME_2', 
                     ['A_old', 'S', 'T', 'Value', 'A'], '_A')
    
    incfile = IncFile(name='WND_VAR_T', path='Output',
                prefix='\n'.join([
                    "TABLE WND_VAR_T1(SSS,TTT,AAA) 'Variation of the wind generation'",
                    ""
                ]),
                body=df,
                suffix='\n'.join([
                    "",
                    ";",
                    "WND_VAR_T(AAA,SSS,TTT) = WND_VAR_T1(SSS,TTT,AAA);",
                    "WND_VAR_T1(SSS,TTT,AAA) = 0;",
                ]))
    incfile.body_prepare(['S', 'T'],
                         ['A'])
    incfile.save()
    
    
    # 1.4 Load and Save SOLE_VAR_T
    df = store_balmorel_input('SOLE_VAR_T', ['A', 'S', 'T', 'Value'], 
                         model_path, scenario, load_again, 
                         lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', mun, 'NAME_2', 
                     ['A_old', 'S', 'T', 'Value', 'A'], '_A')
    
    incfile = IncFile(name='SOLE_VAR_T', path='Output',
                prefix='\n'.join([
                    "TABLE SOLE_VAR_T1(SSS,TTT,AAA) 'Variation of the solar generation'",
                    ""
                ]),
                body=df,
                suffix='\n'.join([
                    "",
                    ";",
                    "SOLE_VAR_T(AAA,SSS,TTT) = SOLE_VAR_T1(SSS,TTT,AAA);",
                    "SOLE_VAR_T1(SSS,TTT,AAA) = 0;",
                ]))
    incfile.body_prepare(['S', 'T'],
                         ['A'])
    incfile.save()
    
    # 1.5 Load and save WNDFLH
    df = store_balmorel_input('WNDFLH', ['A', 'Value'], 
                         model_path, scenario, load_again, 
                         lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', mun, 'NAME_2', 
                     ['A_old', 'Value', 'A'], '_A')
    
    incfile = IncFile(name='WNDFLH', path='Output',
                prefix='\n'.join([
                    "PARAMETER WNDFLH(AAA)  'Full load hours for solar power'",
                    "/"  
                ]),
                body=df,
                suffix='\n'.join([
                    "",
                    "/",
                    ";",
                ]))
    incfile.body = incfile.body.pivot_table(index='A', values='Value', aggfunc='sum')
    incfile.body.index.name = ''
    incfile.body.columns = ['']
    incfile.save()
    
    # 1.6 Load and save SOLEFLH
    df = store_balmorel_input('SOLEFLH', ['A', 'Value'], 
                         model_path, scenario, load_again, 
                         lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', mun, 'NAME_2', 
                     ['A_old', 'Value', 'A'], '_A')
    
    incfile = IncFile(name='SOLEFLH', path='Output',
                prefix='\n'.join([
                    "PARAMETER SOLEFLH(AAA)  'Full load hours for solar power'",
                    "/"  
                ]),
                body=df,
                suffix='\n'.join([
                    "",
                    "/",
                    ";",
                ]))
    incfile.body = incfile.body.pivot_table(index='A', values='Value', aggfunc='sum')
    incfile.body.index.name = ''
    incfile.body.columns = ['']
    incfile.save()
    
    # 1.7 Get Connection 
    y = get_grid(model_path, scenario, load_again)
    
    
if __name__ == '__main__':
    main()
    