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
from pytz import timezone
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

@click.command()
@click.option("--conversion-file", type=str, required=True, help="The conversion dictionary")
@click.option("--el-dataset", type=str, required=True, help="The xarray electricity dataset")
def convert_names(conversion_file, el_dataset):
    # Load dataset
    dataset = xr.load_dataset(el_dataset)
    
    # Load conversion dictionaries
    with open(conversion_file, 'rb') as f:
        converter = pickle.load(f)
        
    # Convert weeks and hours
    new_dataset = dataset.assign_coords(week=converter['week_to_seasons'])
    new_dataset = new_dataset.assign_coords(hour=converter['hour_to_terms'])
        
    assert np.all(new_dataset.electricity_demand_mwh.data == dataset.electricity_demand_mwh.data), 'Values are not the same after conversion!'
        
        
    return convert_coordname_elements(new_dataset, 'electricity_demand_mwh',
                               converter['coord_names'], converter['coord_element_names'],
                               True)   


if __name__ == '__main__':
    dataset = convert_names()
    print(dataset)