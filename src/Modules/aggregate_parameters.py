"""
Spatial Aggregation of Balmorel

Loads Balmorel input and aggregates them based on a gis file that includes cluster categories for each of the old region names 

Created on 01.10.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import os 
import pandas as pd
import numpy as np
import geopandas as gpd
import click
from pybalmorel import Balmorel, IncFile
from pybalmorel.utils import symbol_to_df
import gams
from typing import Tuple

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

def get_symbols_to_aggregate(incfile_folder: str,
                             exceptions: str,
                             mean_aggfuncs: str,
                             median_aggfuncs: str,
                             zero_fillnas: str): 

    incfiles = pd.DataFrame({'files' : os.listdir(incfile_folder)}).query('files.str.contains(".inc")')
    ## Get unique symbols (i.e., remove addon prefix from symbol names)
    symbols = (
        incfiles.files
        .str.replace('INDUSTRY_', '')
        .str.replace('HYDROGEN_', '')
        .str.replace('INDIVUSERS_', '')
        .str.replace('TRANSPORT_', '')
        .str.replace('OFFSHORE_', '')
        .str.replace('FLEXDEM_', '')
        .str.replace('.inc', '')
        .unique()
    )
    ## Remove exceptions
    symbols = [symbol for symbol in symbols if symbol not in exceptions]
    
    ## Determine aggregation functions
    aggfuncs = {symbol : 'mean' if symbol in mean_aggfuncs else 'median' if symbol in median_aggfuncs else 'sum' for symbol in symbols}
        
    ## Determine fillna types
    fillnas = {symbol : 0 if symbol in zero_fillnas else 'EPS' for symbol in symbols}
        
    return symbols, aggfuncs, fillnas

def merge_RRR_names(df: pd.DataFrame,
                    clustering: gpd.GeoDataFrame):
    
    old_column = 'RRR'
    new_column = 'RRR_new'

    clustering.columns = [old_column, new_column]

    df = (
        df
        .merge(clustering, on=old_column, how='outer')
        .drop(columns=old_column)
        .rename(columns={new_column : old_column})
    )

    return df

def merge_IRRRI_names(df: pd.DataFrame,
                    clustering: gpd.GeoDataFrame):
    
    old_columns = ['IRRRI', 'IRRRE']
    new_columns = ['IRRRI_new', 'IRRRE_new']

    for i in range(2):
        
        old_column = old_columns[i]
        new_column = new_columns[i]
        
        clustering.columns = [old_column, new_column]

        df = (
            df
            .merge(clustering, on=old_column, how='outer')
            .drop(columns=old_column)
            .rename(columns={new_column : old_column})
        )
        
    # Make sure that there are no connections to itself
    idx = df.query('IRRRI == IRRRE').index
    df.loc[idx, 'Value'] = np.NaN

    return df

def merge_AAA_names(df: pd.DataFrame,
                    clustering: gpd.GeoDataFrame):
    
    old_column = 'AAA'
    new_column = 'AAA_new'
    clustering.columns = [old_column, new_column]
    
    # Get amount of suffix'es
    suffixes = (
        df.AAA
        .str.split('_', expand=True)[1]
        .unique()
    )
    
    new_cluster_df = clustering.copy()
    new_cluster_df['AAA'] = new_cluster_df.AAA + '_' + suffixes[0]
    new_cluster_df['AAA_new'] = new_cluster_df.AAA_new + '_' + suffixes[0]
    if len(suffixes) > 1:
        for suffix in suffixes[1:]:
            if suffix != None:
                temp = clustering.copy()
                temp['AAA'] = temp.AAA + '_' + suffix
                temp['AAA_new'] = temp.AAA_new + '_' + suffix
                new_cluster_df = pd.concat((new_cluster_df, temp))
                
    df = (
        df
        .merge(new_cluster_df, on=old_column, how='outer')
        .drop(columns=old_column)
        .rename(columns={new_column : old_column})
    )
    
    return df

def aggregate_parameter(db: gams.GamsDatabase, 
                      symbol: str,
                      clustering: gpd.GeoDataFrame,
                      aggfunc: str,
                      fillna: Tuple[float, int, str] = 'EPS'):
    
    # Load dataframe
    df = symbol_to_df(db, symbol)
    symbol_columns = list(df.columns)

    # How to define this? Search for _, if that exists then its areas otherwise regions assumed? What about CCCRRRAAA
    if 'RRR' in symbol_columns:
        df = merge_RRR_names(df, clustering)
    elif 'IRRRE' in symbol_columns:
        df = merge_IRRRI_names(df, clustering)
    elif 'CCCRRRAAA' in symbol_columns:
        print("Passed %s, need to handle the fact that this might be areas or countries"%symbol)
        return
    elif 'AAA' in symbol_columns:
        df = merge_AAA_names(df, clustering)
    else:
        print("No geographic data in here", "\nPassed %s"%symbol)
        return
    
    if type(db[symbol]) == gams.GamsSet:
        print('Passed %s, this is a set, use another function'%symbol)
        return

    # Aggregate and convert names
    df = (
        df
        .groupby(symbol_columns[:-1])
        .aggregate({'Value' : aggfunc})
        .fillna(fillna)
    )
    
    # Make IncFile
    prefix = '\n'.join([
        "TABLE %s(%s) '%s'"%(symbol, ", ".join(symbol_columns[:-1]), db[symbol].text),
        ""
    ])
    suffix = '\n;'
    f = IncFile(name=symbol, path='ClusterOutput',
                prefix=prefix, suffix=suffix)
    f.body = df
    
    # Use N-1 sets as index, and the last as columns, where N = length of columns without 'Value' column
    if len(symbol_columns) > 2:
        index = symbol_columns[:-2]
        columns = symbol_columns[-2]
        f.body_prepare(index=index, columns=columns, values='Value')
    else:
        f.body.columns = ['']
        f.body.index.name = ''
        f.body = f.body.to_string()
    
    f.save()
    
    

#%% ------------------------------- ###
###            X. Main              ###
### ------------------------------- ###

@click.command()
@click.option('--model-path', type=str, required=True, help='Balmorel model path')
@click.option('--scenario', type=str, required=True, help='Balmorel scenario')
@click.option('--exceptions', type=str, required=False, help='.inc files that should NOT be generated')
@click.option('--mean-aggfuncs', type=str, required=False, help='Parameters that should be aggregated with an average')
@click.option('--median-aggfuncs', type=str, required=False, help='Parameters that should be aggregated using the median value')
@click.option('--zero-fillnas', type=str, required=False, help='NaN values that should be converted to zero instead of EPS')
def main(model_path: str, scenario: str, exceptions: str = '', 
         mean_aggfuncs: str = '', median_aggfuncs: str = '', 
         zero_fillnas: str = '', incfile_folder: str = 'Output'):
    
    # Load files
    m = Balmorel(model_path)
    m.load_incfiles(scenario)

    # Naming of clusters - SHOULD BE AN INPUT?
    clusters = gpd.read_file('ClusterOutput/clustering.gpkg')
    clusters['cluster_name'] = ''
    for cluster in clusters.cluster_group.unique():
        idx = clusters.query('cluster_group == @cluster').index 
        clusters.loc[idx, 'cluster_name'] = 'CL%d'%cluster
        
    # Get which .inc-files and how to aggregate based on folder content and configurations
    symbols, aggfuncs, fillnas = get_symbols_to_aggregate(incfile_folder, exceptions, mean_aggfuncs, median_aggfuncs, zero_fillnas)

    # Converting parameters
    print('Will attempt to aggregate..\n%s\n'%(','.join(symbols)))
    for symbol in symbols:
        aggregate_parameter(m.input_data[scenario],
                        symbol, 
                        clusters[['index', 'cluster_name']],
                        aggfunc=aggfuncs[symbol],
                        fillna=fillnas[symbol])
    
if __name__ == '__main__':
    main()
