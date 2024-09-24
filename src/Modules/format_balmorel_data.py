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
from geofiles import prepared_geofiles
from typing import Tuple
import pandas as pd
from pybalmorel import IncFile
import click
import os

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

def store_balmorel_input(symbol: str,
                         columns: list,
                         balmorel_model_path: str, 
                         scenario: str,
                         load_again: bool = False,
                         filter_func: Tuple[None, callable] = None):
    
    balm = Balmorel(balmorel_model_path)
    
    # Check if the symbol.gzip exists
    if not('%s.gzip'%symbol in os.listdir('Data/BalmorelData')):
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
        f.to_parquet('Data/BalmorelData/%s.gzip'%symbol)
    
    else:
        print('\n%s.gzip already exists\n'%symbol)
        f = pd.read_parquet('Data/BalmorelData/%s.gzip'%symbol)
        
    return f

    
@click.command()
@click.option("--model-path", type=str, required=True, help="Path of the Balmorel model")
@click.option("--scenario", type=str, required=True, help="Scenario to load results from")
@click.option("--load-again", type=bool, required=False, help="Load scenario results again and overwrite previously loaded .gdx?")
def main(model_path: str, scenario: str, load_again: bool = False):
    # 1. Load DH_VAR_T
    df = store_balmorel_input('DH_VAR_T', ['A', 'DHUSER', 'S', 'T', 'Value'], 
                         model_path, scenario, load_again, 
                         lambda x: x.loc[x.A.str.contains('DK_')].query("DHUSER == 'RESH'"))
    
    # Check output
    f = pd.read_parquet('Data/BalmorelData/DH_VAR_T.gzip')
    
    # Convert municipal codes to names
    ind, mun, country = prepared_geofiles('DK Municipalities')
    
    ## Remove _A suffix and join name
    df['A'] = df.A.str.replace('_A', '')
    df.index = df.A
    df = df.join(mun.NAME_2)
    df.columns = ['A_old', 'DHUSER', 'S', 'T', 'Value', 'A']
    df.index = range(len(df))
    
    ## Replace æ, ø, å
    df['A'] = (
        df.A
        .str.replace('Æ', 'Ae')
        .str.replace('Ø', 'Oe')
        .str.replace('Å', 'Aa')
        .str.replace('æ', 'ae')
        .str.replace('ø', 'oe')
        .str.replace('å', 'aa')
        .add('_A')
    )
    
    ## 1.1 Save DH_VAR_T.inc
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
                            "DH_VAR_T(AAA,'RESH',SSS,TTT) = DH_VAR_T1(SSS,TTT,AAA,DHUSER);",
                            "DH_VAR_T1(SSS,TTT,AAA,DHUSER) = 0;",
                            "DH_VAR_T('Herlev_A','RESH',SSS,TTT) = DH_VAR_T('Ballerup_A','RESH',SSS,TTT);"
                      ]))
    incfile.body_prepare(['S', 'T'],
                         ['A', 'DHUSER'])
    incfile.save()
    
    ## 1.2 Save INDIVUSERS_DH_VAR_T
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

    
if __name__ == '__main__':
    main()