"""
TITLE

Description

Created on 24.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

from pybalmorel import Balmorel
import click
import os

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

def get_all_data(balmorel_model_path: str, scenario: str, load_again: bool = False):
    balm = Balmorel(balmorel_model_path)
    
    if not('muni_input_data.gdx' in os.listdir(os.path.join(balm.path, 'muni/model'))) or load_again == True:      
        print('\nLoading results into %s_input_data.gdx...\n'%scenario)
        balm.load_incfiles(scenario)
    else:
        print('\n%s_input_data.gdx already loaded!\n'%scenario)
    
@click.command()
@click.option("--model-path", type=str, required=True, help="Path of the Balmorel model")
@click.option("--scenario", type=str, required=True, help="Scenario to load results from")
@click.option("--load-again", type=bool, required=False, help="Load scenario results again and overwrite previously loaded .gdx?")
def main(model_path: str, scenario: str, load_again: bool = False):
    get_all_data(model_path, scenario, load_again)
        
if __name__ == '__main__':
    main()