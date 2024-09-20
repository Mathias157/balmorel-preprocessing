"""
Utility Functions

Created on 19.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import pandas as pd
import xarray as xr
from typing import Union


#%% ------------------------------- ###
###     1. Conversion Functions     ###
### ------------------------------- ###

# 1. Convert coord names and elements
def convert_coordname_elements(dataset: Union[xr.Dataset, pd.DataFrame],
                          dimension_map: dict,
                          element_map: dict,
                          print_before_and_after: bool = False
                          ):
    
    # Change coordinate names
    new_dataset = (
        dataset.copy()
        .rename(dimension_map)
    ) 
    
    # Change coordinate element names
    for coord_name in dimension_map.keys():
        new_coord_name = dimension_map[coord_name]
        if coord_name in element_map:
            old_elements = pd.Series(
                new_dataset.coords[new_coord_name].data
            )
            for old_element in element_map[coord_name].keys():
                old_elements = old_elements.astype(str).str.replace(old_element,
                                                        element_map[coord_name][old_element])
            
            ## old_elements now contain the new ones
            new_dataset = new_dataset.assign_coords(
                {new_coord_name : old_elements}
            )
    
    if print_before_and_after:
        print('Before: \n', dataset, '\n\n')
        print('After: \n', new_dataset, '\n\n')

    return new_dataset

