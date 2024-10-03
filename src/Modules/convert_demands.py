
"""
TITLE

Description

Created on 01.10.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
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

def convert_parameter(db: gams.GamsDatabase, 
                      symbol: str,
                      clustering: gpd.GeoDataFrame):
    
    # Load dataframe
    df = symbol_to_df(db, symbol)
    symbol_columns = list(df.columns)

    # How to define this? Search for _, if that exists then its areas otherwise regions assumed? What about CCCRRRAAA
    old_column = 'RRR'
    new_column = 'RRR_new'
    aggfunc = 'sum'

    # Aggregate and convert names
    clustering.columns = [old_column, new_column]
    df = (
        df
        .merge(clustering, on=old_column, how='outer')
        .drop(columns=old_column)
        .rename(columns={new_column : old_column})
        .groupby(symbol_columns[:-1])
        .aggregate({'Value' : aggfunc})
    )
    
    # Make IncFile
    prefix = '\n'.join([
        "TABLE DE(RRR,YYY,DEUSER) '%s'"%db[symbol].text,
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
def main(model_path: str, scenario: str):
    
    # Load files
    m = Balmorel(model_path)
    m.load_incfiles(scenario)

    # Naming of clusters
    clusters = gpd.read_file('ClusterOutput/clustering.gpkg')
    clusters['cluster_name'] = ''
    for cluster in clusters.cluster_group.unique():
        idx = clusters.query('cluster_group == @cluster').index 
        clusters.loc[idx, 'cluster_name'] = 'CL%d'%cluster
        
    convert_parameter(m.input_data[scenario],
                      'DE', clusters[['index', 'cluster_name']])

if __name__ == '__main__':
    main()
