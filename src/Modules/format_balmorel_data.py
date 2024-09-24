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

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

def get_all_data(balmorel_model_path: str, scenario: str):
    balm = Balmorel(balmorel_model_path)
    print('Loaded scenarios: %s'%balm.scenarios)
    balm.load_incfiles(scenario)
    
@click.command()
@click.option("--model-path", type=str, required=True, help="Path of the Balmorel model")
@click.option("--scenario", type=str, required=True, help="Scenario to load results from")
def main(model_path: str, scenario: str):
    get_all_data(model_path, scenario)
        
if __name__ == '__main__':
    main()