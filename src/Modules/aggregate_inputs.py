"""
Spatial Aggregation of Balmorel

Loads Balmorel input and aggregates them based on a gis file that includes cluster categories for each of the old region names 

Created on 01.10.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt 
import os 
import pandas as pd
import numpy as np
import geopandas as gpd
import click
from typing import Union
from pybalmorel import Balmorel, IncFile
from pybalmorel.utils import symbol_to_df
import gams
from typing import Tuple
import time

#%% ------------------------------- ###
###          1. Functions           ###
### ------------------------------- ###

def get_symbols_to_aggregate(symbols: list,
                             exceptions: str,
                             mean_aggfuncs: str,
                             median_aggfuncs: str,
                             zero_fillnas: str): 

    ## Get unique symbols (i.e., remove addon prefix from symbol names)
    symbols = (
        pd.Series(symbols)
        .str.replace('INDUSTRY_', '')
        .str.replace('HYDROGEN_', '')
        .str.replace('DH2', 'HYDROGEN_DH2')
        .str.replace('INDIVUSERS_', '')
        .str.replace('TRANSPORT_', '')
        .str.replace('FUELCOST', 'FUELTRANSPORT_COST')
        .str.replace('OFFSHORE_', '')
        .str.replace('FLEXDEM_', '')
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

def loop_and_replace_names(df: pd.DataFrame,
                    clustering: gpd.GeoDataFrame,
                    old_column: str):
    
    new_column = '%s_new'%old_column # The column containing the new cluster names
    clustering.columns = [old_column, new_column] # old_column: name to be replaced by cluster name, new_column: cluster name
    clustering = clustering.set_index(old_column)
    
    for area in df[old_column].unique():
        if area == 'DENMARK':
            continue
        
        try:
            suffix = '_' + area.split('_')[1]
            region = area.split('_')[0]
        except IndexError:
            suffix = ''
            region = area
            
        new_name = clustering.loc[region, new_column]
        
        # Make sure to aggregate offshore regions (otherwise, some with same OFF-numbers will be aggregated, while others won't)
        if 'OFF' in suffix:
            suffix = '_OFF'
        
        # Replace names
        idx = df[old_column] == area 
        df.loc[idx, old_column] = new_name + suffix

    return df

def aggregate_parameter(db: gams.GamsDatabase, 
                      symbol: str,
                      clustering: gpd.GeoDataFrame,
                      aggfunc: str,
                      unique_names: dict,
                      second_order: bool,
                      fillna: Tuple[float, int, str] = 'EPS'):
    
    # Load dataframe
    df = symbol_to_df(db, symbol)
    symbol_columns = list(df.columns)
    value_sum_before = df.Value.sum()
    
    # How to define this? Search for _, if that exists then its areas otherwise regions assumed? What about CCCRRRAAA
    if 'RRR' in symbol_columns:
        df = merge_RRR_names(df, clustering)
    elif 'IRRRE' in symbol_columns:
        df = merge_IRRRI_names(df, clustering)
    elif 'CCCRRRAAA' in symbol_columns:
        df = loop_and_replace_names(df, clustering, 'CCCRRRAAA')
    elif 'AAA' in symbol_columns:
        df = loop_and_replace_names(df, clustering, 'AAA')
    else:
        print("No geographic data in here", "\nPassed %s"%symbol)
        return

    # Aggregate and convert names
    df = (
        df
        .groupby(symbol_columns[:-1])
        .aggregate({'Value' : aggfunc})
        .fillna(fillna)
    )
    
    # Writing eps if fillna == EPS
    # if fillna == 'EPS':
    #     idx = df.query('Value <= 1e-9').index
    #     df = df.astype('object')
    #     df.loc[idx, 'Value'] = 'EPS'
    value_sum_after = df.query('Value != "EPS"').Value.sum()
    
    if not(np.isclose(value_sum_after, value_sum_before, rtol=0.01)) and aggfunc == 'sum':
        print('Sum of value before (%0.2f) is not equal to the sum of value after (%0.2f) for symbol %s'%(value_sum_before, value_sum_after, symbol))
        raise('Error in aggregation')
    
    # Make IncFile
    prefix = "TABLE %s(%s) '%s'\n"%(symbol, ", ".join(symbol_columns[:-1]), db[symbol].text)
    suffix = '\n;'
    
    if symbol in unique_names:
        symbol_name = unique_names[symbol]
    else:
        symbol_name = symbol
    
    f = IncFile(name=symbol_name, path='ClusterOutput',
                prefix=prefix, suffix=suffix)
    f.body = df
    
    # Plot connection costs in case it is a connection parameter
    if 'INVCOST' in symbol:
        plot_transmission_invcost(symbol, df, second_order)
    
    # Use N-1 sets as index, and the last as columns, where N = length of columns without 'Value' column
    if len(symbol_columns) > 2:
        index = symbol_columns[:-2]
        columns = symbol_columns[-2]
        f.body_prepare(index=index, columns=columns, values='Value')
    else:
        f.prefix = f.prefix.replace('TABLE', 'PARAMETER')
        f.prefix += '\n/\n'
        f.suffix = f.suffix.replace(';', '/;\n')
        f.body.columns = ['']
        f.body.index.name = ''
        f.body = f.body.to_string()
        
    f.save()
    
def aggregate_sets(db: gams.GamsDatabase, 
                   symbol: str,
                   clustering: gpd.GeoDataFrame,):
     
    # Load dataframe
    df = symbol_to_df(db, symbol)
    symbol_columns = list(df.columns)

    # Convert old names to new cluster names
    for column in symbol_columns:
        if column in ['CCCRRRAAA', 'RRR', 'AAA']:
            df = loop_and_replace_names(df, clustering, column)
    
    # Make IncFile
    prefix = '\n'.join([
        "SET %s(%s) '%s'\n/"%(symbol, ", ".join(symbol_columns), db[symbol].text),
        ""
    ])
    suffix = '\n/\n;'
    f = IncFile(name=symbol, path='ClusterOutput',
                prefix=prefix, suffix=suffix)
    
    # Format input
    df = (
        df
        .apply(lambda row: ' . '.join(row.astype(str)), axis=1)
        .drop_duplicates()
        .sort_values()
    )
    f.body = "\n".join([value for value in df.values])
    
    f.save()
    
@click.pass_context
def plot_transmission_invcost(ctx, symbol: str,
                              df: pd.DataFrame,
                              second_order: bool,
                              year: int = 2050):
    print('Plotting connection costs for %s'%symbol)
    
    cluster_file = 'ClusterOutput/%s_%dcluster_geofile'%('-'.join(ctx.obj['cluster_params']), ctx.obj['cluster_size'])
    if second_order:
        cluster_file += '_2nd-order'
    
    geo_union = gpd.read_file(cluster_file + '.gpkg')
    geo_union['coord'] = geo_union.centroid
    
    fig, ax = plt.subplots()
    geo_union.plot(ax=ax)
    
    # lines = []
    exclusion = []
    for line, cap in df.loc[str(year)].iterrows():
        if line in exclusion or line[0] == line[1]:
            continue
        
        coords = geo_union.query('cluster_name == @line[0] or cluster_name == @line[1]')['coord']

        x1, x2 = coords.x
        y1, y2 = coords.y
        
        l, = ax.plot([x1,x2], [y1,y2], color = 'r', linewidth = cap['Value']*1e-5)
        # lines.append(l)
        
        exclusion.append((line[1], line[0]))
    # print(df.drop)
    
    fig.savefig('ClusterOutput/Figures/%s.png'%symbol)


#%% ------------------------------- ###
###            2. Main              ###
### ------------------------------- ###

@click.command()
@click.pass_context
@click.option('--model-path', type=str, required=True, help='Balmorel model path')
@click.option('--scenario', type=str, required=True, help='Balmorel scenario')
@click.option('--exceptions', type=str, required=False, default='', help='.inc files that should NOT be generated')
@click.option('--mean-aggfuncs', type=str, required=False, default='', help='Parameters that should be aggregated with an average')
@click.option('--median-aggfuncs', type=str, required=False, default='', help='Parameters that should be aggregated using the median value')
@click.option('--zero-fillnas', type=str, required=False, default='', help='NaN values that should be converted to zero instead of EPS')
@click.option('--only-symbols', type=str, required=False, default=None, help="Only aggregate the symbols, input as comma-separated string")
@click.option('--cluster-size', type=int, required=True, help='How many clusters?')
@click.option('--cluster-params', type=str, required=True, help='Comma-separated list of Balmorel input data to cluster (use the symbol names, e.g. DE for annual electricity demand)')
@click.option('--second-order', type=bool, required=True, help='Second order clustering or not?')
@click.option('--gams-sysdir', type=str, required=False, help='GAMS system directory')
def main(ctx, model_path: str, scenario: str, exceptions: str, 
         mean_aggfuncs: str, median_aggfuncs: str, 
         zero_fillnas: str, only_symbols: Union[str, None], 
         cluster_size: int,
         cluster_params: str,
         second_order: bool,
         gams_sysdir: str = '/opt/gams/48.5'):
    
    # only_symbols = 'DE'
    
    # Make configuration lists
    ctx.ensure_object(dict)
    ctx.obj['cluster_params'] = cluster_params.replace(' ', '').split(',')
    ctx.obj['cluster_size'] = cluster_size
    exceptions = exceptions.replace(' ', '').split(',') # Symbols not to aggregate
    mean_aggfuncs = mean_aggfuncs.replace(' ', '').split(',')
    median_aggfuncs = median_aggfuncs.replace(' ', '').split(',')
    zero_fillnas = zero_fillnas.replace(' ', '').split(',')
    unique_names = {'TRANSDEMAND_Y' : 'TRANSPORT_TRANSDEMAND_Y',
                    'XH2INVCOST' : 'HYDROGEN_XH2INVCOST',
                    'XH2COST' : 'HYDROGEN_XH2COST',
                    'XH2LOSS' : 'HYDROGEN_XH2LOSS', 
                    'FLEXMAXLIMIT' : 'FLEXDEM_FLEXMAXLIMIT',
                    'FLEXYDEMAND' : 'FLEXDEM_FLEXYDEMAND'} # Symbols that have a different incfile name
    
    # Load input data, cluster geofile and symbols to aggregate
    m = Balmorel(model_path,gams_system_directory=gams_sysdir)
    m.load_incfiles(scenario)
    if second_order:
        clusters = gpd.read_file('ClusterOutput/clustering_2nd-order.gpkg')
        symbols = open('Data/Configurations/2ndOrderClusteringFiles.txt', 'r').read().replace('.inc', '').replace('ClusterOutput/', '').splitlines()
    else:
        clusters = gpd.read_file('ClusterOutput/clustering.gpkg')
        symbols = open('Data/Configurations/1stOrderClusteringFiles.txt', 'r').read().replace('.inc', '').replace('ClusterOutput/', '').splitlines()
        
    # Filter out exceptions and get aggregation methods per symbol
    symbols, aggfuncs, fillnas = get_symbols_to_aggregate(symbols, exceptions, mean_aggfuncs, median_aggfuncs, zero_fillnas)
    
    if only_symbols != None:
        symbols = only_symbols.replace(' ', '').split(',')

    # Aggregating parameters and sets
    print('Will attempt to aggregate..\n%s\n'%(','.join(symbols)))
    for symbol in symbols:
        t0 = time.time()
        if type(m.input_data[scenario][symbol]) == gams.GamsParameter:
            aggregate_parameter(m.input_data[scenario],
                            symbol, 
                            clusters[['index', 'cluster_name']],
                            aggfunc=aggfuncs[symbol],
                            unique_names=unique_names,
                            second_order=second_order,
                            fillna=fillnas[symbol])
        elif type(m.input_data[scenario][symbol] == gams.GamsSet):
            aggregate_sets(m.input_data[scenario],
                           symbol,
                           clusters[['index', 'cluster_name']])   
        else:
            print('%s is not a set or a parameter, not aggregated'%symbol)
        t1 = time.time()
        if (t1 - t0) > 60:
            print('%s took %0.2f minutes!'%(symbol, (t1 - t0)/60))
        
if __name__ == '__main__':
    main()
