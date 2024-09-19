"""
Utility Functions

Created on 19.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import xarray as xr

style = 'report'

#%% ------------------------------- ###
###     1. Conversion Functions     ###
### ------------------------------- ###

# 1. Convert coord names and elements
def convert_coordname_elements(dataset: (xr.Dataset, pd.DataFrame),
                          data_name: str,
                          dimension_map: dict,
                          element_map: dict,
                          print_before_and_after: bool = False
                          ):
    
    if print_before_and_after:
        print('Before: \n', dataset, '\n\n')
    # Change coordinate names
    dataset = dataset.rename(dimension_map)
    
    # Change coordinate element names
    for coord_name in dimension_map.keys():
        new_coord_name = dimension_map[coord_name]
        if coord_name in element_map:
            old_elements = pd.Series(
                dataset.coords[new_coord_name].data
            )
            for old_element in element_map[coord_name].keys():
                old_elements = old_elements.astype(str).str.replace(old_element,
                                                        element_map[coord_name][old_element])
            
            ## old_elements now contain the new ones
            dataset = dataset.assign_coords(
                {new_coord_name : old_elements}
            )
    
    if print_before_and_after:
        print('After: \n', dataset, '\n\n')

    return dataset

