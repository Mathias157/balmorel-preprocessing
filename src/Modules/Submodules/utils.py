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
from typing import Tuple
import pickle
import numpy as np
from matplotlib import colormaps
from pybalmorel import Balmorel
from pybalmorel.utils import symbol_to_df
import geopandas as gpd
from gams import GamsWorkspace
import os
try:
    import cmcrameri
    cmap = cmcrameri.cm.cmaps['batlowK']
    colors = [cmap(i) for i in range(256)]
except ModuleNotFoundError:
    print('cmrameri package not installed, using default colourmaps')
    cmap = colormaps['viridis']
    colors = [cmap(i) for i in range(256)]
    
#%% ------------------------------- ###
###     1. Conversion Functions     ###
### ------------------------------- ###

# 1. Convert coord names and elements
def convert_coordname_elements(dataset: Tuple[xr.Dataset, pd.DataFrame],
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


def convert_names(conversion_file: str, 
                  dataset: xr.Dataset,
                  data_variable: str,
                  convert_seasons_and_terms: bool = False):
    
    # Load conversion dictionaries
    with open(conversion_file, 'rb') as f:
        converter = pickle.load(f)
        
    # Convert
    new_dataset = convert_coordname_elements(dataset, 
                                             converter['coord_names'], 
                                             converter['coord_element_names'],
                                            False)   
        
    # Convert weeks and hours
    if convert_seasons_and_terms:
        new_dataset = (
            new_dataset
            .assign_coords(S=converter['week_to_seasons'])
            .assign_coords(T=converter['hour_to_terms'])
        )
        
    # Test that we did not mess something up
    before = np.nan_to_num(dataset.get(data_variable).data)
    after = np.nan_to_num(new_dataset.get(data_variable).data)
    assert np.all(after == before), 'Values are not the same after conversion!'
        
    return dataset, new_dataset

def transform_xrdata(xarray: xr.Dataset,
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
    
    return output


def store_balmorel_input(symbol: str,
                         columns: list,
                         balmorel_model_path: str, 
                         scenario: str,
                         load_again: bool = False,
                         filter_func: Tuple[None, callable] = None,
                         save: bool = True,
                         gams_system_directory: str = '/opt/gams/48.5'):
    
    balm = Balmorel(balmorel_model_path, gams_system_directory=gams_system_directory)
    
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
            ws = GamsWorkspace(system_directory=gams_system_directory)
            balm.input_data[scenario] = ws.add_database_from_gdx(os.path.abspath(balm_input_path))

        # Get symbol
        f = symbol_to_df(balm.input_data[scenario], symbol, columns)
        if filter_func != None:
            f = filter_func(f)
            
        if save:
            f.to_parquet('Data/BalmorelData/%s.gzip'%symbol)
        
    return f


#%% ------------------------------- ###
###     2. DataFrames and Dicts     ###
### ------------------------------- ###

def df_set_to_dictionary(df: pd.DataFrame, 
                column: str, 
                suffix: Tuple[str, None] = None, 
                parent_column: Tuple[str, None] = None) -> dict:
    # Get set
    sets = pd.DataFrame({column : df[column].unique()})
    
    # Connect area to region by suffix, if there is a suffix
    if suffix != None:
        sets[parent_column] = sets.loc[:, column].str.replace(suffix, '') 
        sets = sets.pivot_table(index=parent_column, aggfunc='sum')

    return sets.to_dict()

def save_dict_set(save_path: str,
                  df: pd.DataFrame, 
                column: str, 
                suffix: Tuple[str, None] = None, 
                parent_column: Tuple[str, None] = None,
                ):
    # Save df set to dictionary
    set = df_set_to_dictionary(df, column, suffix, parent_column)
    with open(save_path, 'wb') as f:
        pickle.dump(set[column], f)

def combine_dicts(dict_list: list):
    combined = {}
    # Assuming dictionaries have identical keys 
    for key in dict_list[0]:
        combined[key] = [dict0[key] for dict0 in dict_list]
    return combined


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
