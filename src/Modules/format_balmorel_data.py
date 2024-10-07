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
        balm_input_path1 = os.path.join(balm.path, scenario, 'model', '%s_input_data.gdx'%scenario)
        balm_input_path2 = os.path.join('Data', 'BalmorelData', '%s_input_data.gdx'%scenario)
        if (not(os.path.exists(balm_input_path1)) and not(os.path.exists(balm_input_path2))) or load_again == True:      
            print('\nLoading results into %s_input_data.gdx...\n'%scenario)
            balm.load_incfiles(scenario)
        else:
            if os.path.exists(balm_input_path2):
                balm_input_path = balm_input_path2
            else:
                balm_input_path = balm_input_path1
                
            print('\n%s_input_data.gdx already loaded!'%scenario)
            print('Loading %s...\n'%(balm_input_path))
            
            # Load the input
            ws = GamsWorkspace()
            balm.input_data[scenario] = ws.add_database_from_gdx(os.path.abspath(balm_input_path))

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
        df[left_col] = df[left_col].str.replace(suffix, '')
    df.index = df[left_col]
    df = df.join(gpd[right_col])
    df.columns = new_col
    df.index = range(len(df))
    if suffix != None:
        df[left_col] = df[left_col] + suffix
    
    return df 


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

    # Load DH_VAR_T
    df = store_balmorel_input('DH_VAR_T', ['A', 'DHUSER', 'S', 'T', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')].query("DHUSER == 'RESH'"))
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
                    ['A_old', 'DHUSER', 'S', 'T', 'Value', 'A'], '_A')
        
    ### Save DH_VAR_T.inc
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
    
    ### Save INDIVUSERS_DH_VAR_T
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
    
    
@main.command()
@click.pass_context
def onshore_vre(ctx):
    
    # 1.3 Load and Save WND_VAR_T
    df = store_balmorel_input('WND_VAR_T', ['A', 'S', 'T', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
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
                    "WND_VAR_T('Frederiksberg_A',SSS,TTT) = WND_VAR_T('Koebenhavn_A',SSS,TTT);",
                    "$onmulti",
                    "$if     EXIST '../data/OFFSHORE_WND_VAR_T.inc'      $INCLUDE '../data/OFFSHORE_WND_VAR_T.inc';",
                    "$if not EXIST '../data/OFFSHORE_WND_VAR_T.inc'      $INCLUDE '../../base/data/OFFSHORE_WND_VAR_T.inc';",
                    "$offmulti"
                ]))
    incfile.body_prepare(['S', 'T'],
                        ['A'])
    incfile.save()
    
    
    # 1.4 Load and Save SOLE_VAR_T
    df = store_balmorel_input('SOLE_VAR_T', ['A', 'S', 'T', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
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
                    "SOLE_VAR_T('Frederiksberg_A',SSS,TTT) = SOLE_VAR_T('Koebenhavn_A',SSS,TTT);"
                ]))
    incfile.body_prepare(['S', 'T'],
                        ['A'])
    incfile.save()
    
    # 1.5 Load and save WNDFLH
    df = store_balmorel_input('WNDFLH', ['A', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
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
                    "$onmulti",
                    "$if     EXIST '../data/OFFSHORE_WNDFLH.inc' $INCLUDE '../data/OFFSHORE_WNDFLH.inc';",
                    "$if not EXIST '../data/OFFSHORE_WNDFLH.inc' $INCLUDE '../../base/data/OFFSHORE_WNDFLH.inc';",
                    "$offmulti"
                ]))
    incfile.body = incfile.body.pivot_table(index='A', values='Value', aggfunc='sum')
    
    # Hard-coded assumption on Frederiksberg 
    incfile.body.loc['Frederiksberg_A', 'Value'] = incfile.body.loc['Koebenhavn_A', 'Value']
    
    incfile.body.index.name = ''
    incfile.body.columns = ['']
    incfile.save()
    
    # 1.6 Load and save SOLEFLH
    df = store_balmorel_input('SOLEFLH', ['A', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')])
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
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
                    ";"
                ]))
    incfile.body = incfile.body.pivot_table(index='A', values='Value', aggfunc='sum')
    
    # Hard-coded assumption on Frederiksberg 
    incfile.body.loc['Frederiksberg_A', 'Value'] = incfile.body.loc['Koebenhavn_A', 'Value']
    
    incfile.body.index.name = ''
    incfile.body.columns = ['']
    incfile.save()
    
    # 1.8 Get VRE Potentials
    df = store_balmorel_input('SUBTECHGROUPKPOT', ['CRA', 'TECH_GROUP', 'SUBTECH_GROUP', 'Value'],
                            ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                            lambda x: x.loc[x.CRA.str.contains('DK_')])
        
    ## Join municipal codes ('CRA') to names ('NAME_2')
    df = join_to_gpd(df, 'CRA', ctx.obj['mun'], 'NAME_2', 
                      ['CRA', 'TECH_GROUP', 'SUBTECH_GROUP', 'Value', 'A'], '_A')
    df['A'] = df.A + '_A'
    
    
    # Convert very small numbers to EPS
    idx = df.Value < 1e-10
    df.loc[idx, 'Value'] = 'EPS'
    
    incfile = IncFile(name='SUBTECHGROUPKPOT', path='Output',
                prefix='\n'.join([
                    "TABLE SUBTECHGROUPKPOT(CCCRRRAAA, TECH_GROUP, SUBTECH_GROUP)  'Subtechnology group capacity restriction by geography (MW)'",
                    ""  
                ]),
                body=df,
                suffix='\n'.join([
                    "",
                    ";",
                    "$onmulti",
                    "$if     EXIST '../data/OFFSHORE_SUBTECHGROUPKPOT.inc' $INCLUDE '../data/OFFSHORE_SUBTECHGROUPKPOT.inc';",
                    "$if not EXIST '../data/OFFSHORE_SUBTECHGROUPKPOT.inc' $INCLUDE '../../base/data/OFFSHORE_SUBTECHGROUPKPOT.inc';",
                    "$offmulti"
                ]))
    incfile.body_prepare(['A', 'TECH_GROUP'], 'SUBTECH_GROUP', values='Value')
    # incfile.body.index.names = ['', '']
    # incfile.body.columns.name = ''
    incfile.save()
    

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
def biomass(ctx):
    pass

if __name__ == '__main__':
    main()
    