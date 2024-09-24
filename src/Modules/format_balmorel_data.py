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
import click
import os

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

def get_all_data(balmorel_model_path: str, scenario: str, load_again: bool = False):
    balm = Balmorel(balmorel_model_path)
    
    if not('muni_input_data.gdx' in os.listdir(os.path.join(balm.path, 'muni', 'model'))) or load_again == True:      
        print('\nLoading results into %s_input_data.gdx...\n'%scenario)
        balm.load_incfiles(scenario)
    else:
        print('\n%s_input_data.gdx already loaded!'%scenario)
        print('Loading %s_input_data.gdx...\n'%(os.path.join(balm.path, 'muni', 'model', scenario)))
        
        # Load the input
        ws = GamsWorkspace()
        balm.input_data[scenario] = ws.add_database_from_gdx(os.path.join(balm.path, 'muni', 'model', '%s_input_data.gdx'%scenario))

    return balm
    
@click.command()
@click.option("--model-path", type=str, required=True, help="Path of the Balmorel model")
@click.option("--scenario", type=str, required=True, help="Scenario to load results from")
@click.option("--load-again", type=bool, required=False, help="Load scenario results again and overwrite previously loaded .gdx?")
def main(model_path: str, scenario: str, load_again: bool = False):
    balm = get_all_data(model_path, scenario, load_again)
    # print(symbol_to_df(balm.input_data[scenario], 'DH_VAR_T').to_string()) # Prints A LOT!
    
        
if __name__ == '__main__':
    main()