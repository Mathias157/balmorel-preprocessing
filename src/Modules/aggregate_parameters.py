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

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

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

def convert_parameter(db: gams.GamsDatabase, 
                      symbol: str,
                      clustering: gpd.GeoDataFrame,
                      aggfunc: str):
    
    # Load dataframe
    df = symbol_to_df(db, symbol)
    symbol_columns = list(df.columns)

    # How to define this? Search for _, if that exists then its areas otherwise regions assumed? What about CCCRRRAAA
    if 'RRR' in symbol_columns:
        df = merge_RRR_names(df, clustering)
    elif 'IRRRE' in symbol_columns:
        df = merge_IRRRI_names(df, clustering)
    elif 'CCCRRRAAA' in symbol_columns:
        old_column = 'CCCRRRAAA'
        new_column = 'CCCRRRAAA_new'
        raise "Need to handle the fact that this might be areas or countries"
    elif 'AAA' in symbol_columns:
        old_column = 'AAA'
        new_column = 'AAA_new'
        raise "Need to make function that strips the _suffix'es, and add them back again after the merge (what if there are different suffix'?)"
    else:
        raise 'No geographic data in here'

    # Aggregate and convert names
    df = (
        df
        .groupby(symbol_columns[:-1])
        .aggregate({'Value' : aggfunc})
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
    index = symbol_columns[:-2]
    columns = symbol_columns[-2]
    f.body_prepare(index=index, columns=columns, values='Value')
    f.save()
    
    

#%% ------------------------------- ###
###            X. Main              ###
### ------------------------------- ###

@click.command()
@click.option('--model-path', type=str, required=True, help='Balmorel model path')
@click.option('--scenario', type=str, required=True, help='Balmorel scenario')
@click.option('--exceptions', type=str, required=False, help='.inc files that should NOT be generated')
def main(model_path: str, scenario: str, exceptions: str = '', incfile_folder: str = 'Output'):
    
    # Load files
    m = Balmorel(model_path)
    m.load_incfiles(scenario)

    # Naming of clusters - SHOULD BE AN INPUT?
    clusters = gpd.read_file('ClusterOutput/clustering.gpkg')
    clusters['cluster_name'] = ''
    for cluster in clusters.cluster_group.unique():
        idx = clusters.query('cluster_group == @cluster').index 
        clusters.loc[idx, 'cluster_name'] = 'CL%d'%cluster
        
    # Get .inc-files to regenerate based on folder content
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
        
    # Converting parameters
    param = 'TRANSDEMAND_Y'
    convert_parameter(m.input_data[scenario],
                      param, 
                      clusters[['index', 'cluster_name']],
                      aggfunc='sum')
    
    param = 'XH2INVCOST'
    convert_parameter(m.input_data[scenario],
                      param, 
                      clusters[['index', 'cluster_name']],
                      aggfunc='mean')

if __name__ == '__main__':
    main()
