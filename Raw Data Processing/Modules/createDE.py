"""
Create electricity demand profiles for Denmark
Use Energinet data for municipalities:
https://www.energidataservice.dk/tso-electricity/consumptionindustry
Convert LAU code to municipality name with: 
LAU – NUTS 2021, EU-27 and EFTA / available candidate countries
https://ec.europa.eu/eurostat/web/nuts/local-administrative-units
Note: The dataset above also contains population

Created on 22.08.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import click
import pickle
import xarray as xr
from typing import Tuple
from pybalmorel import IncFile
from Submodules.municipal_template import DataContainer
from Submodules.utils import convert_coordname_elements
import matplotlib
try:
    import cmcrameri
    cmap = cmcrameri.cm.cmaps['roma_r']
    cmap = cmcrameri.cm.cmaps['vik']
    colors = [cmap(i) for i in range(256)]
except ModuleNotFoundError:
    print('cmrameri package not installed, using default colourmaps')
    cmap = matplotlib.colormaps['viridis']
    colors = [cmap(i) for i in range(256)]


style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###      1. Make .inc Files         ###
### ------------------------------- ###

def convert_names(conversion_file: str, el_dataset: str):
    # Load dataset
    dataset = xr.load_dataset(el_dataset)
    
    # Load conversion dictionaries
    with open(conversion_file, 'rb') as f:
        converter = pickle.load(f)
        
    # Convert
    new_dataset = convert_coordname_elements(dataset, 
                                             converter['coord_names'], 
                                             converter['coord_element_names'],
                                            False)   
        
    # Convert weeks and hours
    new_dataset = (
        new_dataset
        .assign_coords(S=converter['week_to_seasons'])
        .assign_coords(T=converter['hour_to_terms'])
    )
        
    # Test that we did not mess something up
    before = np.nan_to_num(dataset.electricity_demand_mwh.data)
    after = np.nan_to_num(new_dataset.electricity_demand_mwh.data)
    assert np.all(after == before), 'Values are not the same after conversion!'
        
    return dataset, new_dataset

def make_inc_file(xarray: xr.Dataset,
                  data_variable: str,
                  selection: Tuple[dict, None] = None,
                  sets_to_sum: Tuple[str, list, None] = None):

    output = xarray
    if sets_to_sum != None:
        output = (
            output
            .get(data_variable)
            .sum(sets_to_sum)
        )

    if selection != None:
        output = output.sel(selection)
    
    print(output)

# Main function
@click.command()
@click.option("--conversion-file", type=str, required=True, help="The conversion dictionary")
@click.option("--el-dataset", type=str, required=True, help="The xarray electricity dataset")
@click.option("--show-difference", type=bool, required=False, help="Show dataset before and after conversion")
def main(conversion_file: str, el_dataset: str, show_difference: bool = False):
    
    # 1.1 Format Dataset
    dataset, new_dataset = convert_names(conversion_file, el_dataset)
    
    if show_difference:
        print('Before: \n', dataset, '\n\n')
        print('After: \n', new_dataset, '\n\n')
        
    # 1.2 Make .inc-files
    ## 1.2.1 DE
    make_inc_file(new_dataset,
                  'electricity_demand_mwh',
                  sets_to_sum=['S', 'T'])

if __name__ == '__main__':
    main()