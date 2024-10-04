"""
TITLE

Description

Created on 11.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcol
from pybalmorel import Balmorel
from pybalmorel.utils import symbol_to_df
from Submodules.utils import convert_names
from typing import Tuple
import click
import pandas as pd
import numpy as np
import xarray as xr
import gams
import geopandas as gpd
from geofiles import prepared_geofiles
from scipy.sparse import csr_matrix
from Submodules.municipal_template import DataContainer
from exo_heat_demand import DistrictHeatAAU
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import kneighbors_graph
try:
    import cmcrameri
    cmap = cmcrameri.cm.cmaps['batlowK']
    colors = [cmap(i) for i in range(256)]
except ModuleNotFoundError:
    print('cmrameri package not installed, using default colourmaps')
    cmap = matplotlib.colormaps['viridis']
    colors = [cmap(i) for i in range(256)]

def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    new_cmap = mcol.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap
    

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

def correct_VRE_data(path_to_file, generation_name: str):
    vredata  = xr.load_dataset(path_to_file)
    vredata  = vredata.rename({'id': 'municipality',
                                'specific generation' : generation_name})
    
    # Rename municipalities 
    correct_names = {'Århus' : 'Aarhus',
                'Høje Taastrup' : 'Høje-Taastrup',
                'Vesthimmerland' : 'Vesthimmerlands'}

    vredata = vredata.to_dataframe().reset_index()
    vredata['municipality'] = vredata['municipality'].replace(correct_names)
    
    # Get dates
    vredata['week'] = vredata.time.dt.isocalendar()['week']
    vredata['day'] = vredata.time.dt.isocalendar()['day']
    vredata['hour'] = vredata.time.dt.hour + 1 + (vredata['day'] - 1)*24 
    
    date0 = pd.to_datetime("2012-01-02 00:00")
    date1 = pd.to_datetime("2012-12-31 00:00")
    vredata = (
        vredata
        .query('time >= @date0 and time < @date1')
        .pivot_table(index=['municipality', 'week', 'hour'],
                     values=generation_name)
        .to_xarray()
    )
    
    # Normalise
    vredata = vredata / vredata.max(dim=['week', 'hour'])
    
    return vredata
    
def convert_municipal_code_to_name(to_be_converted: pd.DataFrame,
                                    column_to_convert: Tuple[str, int],
                                    pivot_table: bool = False,
                                    exclude_regions: list = ['Herlev', 'Christiansø'],
                                    muni_geofile_path: str = r'C:\Users\mberos\gitRepos\balmorel-preprocessing\src\Data\Shapefiles\Denmark\Adm\gadm36_DNK_2.shp'):

    index, muni_geofile, country = prepared_geofiles('DK Municipalities')

    # Some data was missing for Herlev, DK_1_19_1 and Christiansø, DK_1_6_1 
    areas2 = muni_geofile.query("NAME_2 not in @exclude_regions")
    
    converter = dict(areas2.NAME_2)
    # print(converter)
    # Convert to municipality names
    if pivot_table:
        to_be_converted = to_be_converted.reset_index()
    to_be_converted[column_to_convert] = to_be_converted[column_to_convert].replace(converter)

    return to_be_converted


def collect_clusterdata(plot_cf: bool = False):

    con = DataContainer()
    
    ## Annual Heat Demand
    temp = DistrictHeatAAU()
    temp.combine_data()
    con.muni = con.muni.merge(temp.data)
    
    ## Annual Electricity Demands - assume 2023 = 2019
    energinet_el = xr.load_dataset('Data/Timeseries/energinet_eldem.nc')
    energinet_el = energinet_el.assign_coords(year=[2019])
    con.muni = con.muni.merge(energinet_el.sum(dim=['week', 'hour']))

    ## VRE CF's
    winddata = (
        correct_VRE_data(r'Output/VRE/2012_wind_DKMuniDESENO.nc',
                                    'wind_generation_mwh')
        .rename({'wind_generation_mwh' : 'wind_cf'})
        .sum(dim=['week', 'hour'])
        / 8736    
    )
    
    solardata = (
        correct_VRE_data(r'Output/VRE/2012_solar_DKMuniDESENO.nc',
                                 'solar_generation_mwh')
        .rename({'solar_generation_mwh' : 'solar_cf'})
        .sum(dim=['week', 'hour'])
        / 8736    
    )

    ## Only collect DK and onshore potentials
    con.muni = (
        con.muni
        .merge(winddata, join='left')
        .merge(solardata, join='left')
    )
    
    ### We set Frederiksberg to same CF as København as it otherwise drives the clustering hard
    con.muni.wind_cf.loc['Frederiksberg'] = con.muni.wind_cf.loc['København']
    con.muni.solar_cf.loc['Frederiksberg'] = con.muni.solar_cf.loc['København']

    ### Plot CF
    if plot_cf:
        fig, ax = plt.subplots()
        con.get_polygons().plot(
            ax=ax,
            column=con.muni.solar_cf.data,
            legend=True,
            vmin=0,
            vmax=0.175
        )

    return con


def apply_filters(df: pd.DataFrame, value_name: str, aggfunc: str = 'sum'):
    if 'A' in df.columns:
        df['R'] = df.A.str.split('_', expand=True)[0]
        
    df = df.pivot_table(index='R', values='Value', aggfunc=aggfunc)
    df.columns = [value_name]
    
    return df

columns = {'DE' : ['Y', 'R', 'DEUSER', 'Value'],
           'DH' : ['Y', 'A', 'DHUSER', 'Value'],
           'WNDFLH' : ['A', 'Value'],
           'SOLEFLH' : ['A', 'Value']}

def gather_data(db: gams.GamsDatabase,  
                cluster_params: list,
                aggfuncs: list):
    
    for i in range(len(cluster_params)):
        try:
            df = symbol_to_df(db, cluster_params[i], columns[cluster_params[i]])
        except KeyError:
            print('Column names not found for %s'%cluster_params[i])
            df = symbol_to_df(db, cluster_params[i])        
            
        if i == 0:
            collected_data = apply_filters(df, cluster_params[i], aggfunc=aggfuncs[i])
            continue
            
        collected_data = collected_data.join(
            apply_filters(df, cluster_params[i], aggfunc=aggfuncs[i]),
            how='outer'
        )
        
    return collected_data.to_xarray().rename({'R':'IRRRE'})

def cluster(collected_data: pd.DataFrame,
            n_clusters: int,
            use_connectivity: bool = True,
            manual_corrections: list = [
                ['Bornholm', 'Christiansoe', 1],
                ['Bornholm', 'Dragoer', 1],
                ['Esbjerg', 'Fanoe', 1],
                ['Roedovre', 'Frederiksberg', 1],
                ['Slagelse', 'Nyborg', 0],
                ['Samsoe', 'Kalundborg', 0]
            ],
            linkage: str = 'Ward',
            connection_remark: str = 'connec. included + artifical',
            data_remark: str = 'all combined + xy coords'):

    # collected_data = collected_data.drop_sel(IRRRE='Christiansoe')

    # Connectivity
    if use_connectivity:
        ## Use connectivity from Balmorel (Submodules/get_grid.py)
        connectivity = xr.load_dataset('Data/BalmorelData/municipal_connectivity.nc')
        connectivity_old, connectivity = convert_names('Modules/Submodules/exo_grid_conversion_dictionaries.pkl', connectivity, 'connection')

        ## Manual Corrections
        for manual_connection in manual_corrections:
            connectivity.connection.loc[manual_connection[0], manual_connection[1]] = manual_connection[2]
            connectivity.connection.loc[manual_connection[1], manual_connection[0]] = manual_connection[2]
            
        
        ## Make symmetric index, so the indices fit
        collected_data = collected_data.assign_coords(IRRRI=collected_data.coords['IRRRE'].data)
        
        ## Combine with data
        # connectivity = connectivity.drop_sel(IRRRE='Christiansoe', IRRRI='Christiansoe')
        X = collected_data.merge(connectivity)
        
        ## Make symmetric connectivity graph 
        knn_graph = X.connection.data # get numpy array
        knn_graph = csr_matrix(knn_graph) # make dense format
        
        ## Drop the connection variable again
        X = X.drop_vars('connection')
    else:
        knn_graph = None # don't apply connectivity constraints
        X = collected_data

    # Prepare data for clustering
    Y = np.vstack([X.get(variable).data for variable in X.data_vars]).T
    Y = np.nan_to_num(Y)
    Y = StandardScaler().fit_transform(Y) # Normalise dataset
    
    ## Make higher weighting of certain coordinates..?
    # X[:,0] = X[:,0]*10000
    # X[:,1] = X[:,1]*10000
    
    # Perform Clustering
    agg = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage.lower(),
                                connectivity=knn_graph)
    agg.fit(Y)
    
    # Merge labels to xarray
    X['cluster_groups'] = (['IRRRE'], agg.labels_)
    
    # Plot the different clustering techniques
    ## Get geofiles
    the_index, geofiles, c = prepared_geofiles('DKmunicipalities_names')
    geofiles.index.name = 'IRRRE'
    X = X.merge(geofiles['geometry'].to_xarray())
    

    # Plot clustering
    fig, ax = plt.subplots()
    
    clustering = gpd.GeoDataFrame({'cluster_group' : X.cluster_groups.data},
                                  index=X.coords['IRRRE'].data,
                            geometry=X.geometry.data,
                            crs='EPSG:4326')
    
    clustering.plot(ax=ax, column='cluster_group',
                    cmap=truncate_colormap(cmap, 0.2, 1))
            
    if knn_graph == None:
        connection_remark = 'no connectivity'

    plot_title = '%s, %d clusters, %s\ndata: %s'%(linkage, 
                                                n_clusters,
                                                connection_remark,
                                                data_remark) 
    ax.set_title(plot_title)
    # ax.set_title('%d clusters, %s linkage, %s'%(n_clusters, name, connection_remark))    
    
    ax.axes.axis('off')
    
    # fig.savefig(r'C:\Users\mberos\Danmarks Tekniske Universitet\PhD in Transmission and Sector Coupling - Dokumenter\Deliverables\Spatial Resolution\Investigations\240912 - Initial Clustering Method Tests'+'/'+plot_title.replace('data: ', '_').replace('\n', '').replace(' clusters', 'N').replace(' ', '_').replace(',', '') + '.png',
    #             transparent=True,
    #             bbox_inches='tight')
    
    ### Label municipalities
    # clustering.reset_index().apply(lambda x: ax.annotate(text=x['municipality'], xy=(x.geometry.centroid.x, x.geometry.centroid.y), ha='center'), axis=1)
    
    ### Look at specific coordinates    
    ## København region - Frederiksberg have 0 in both wind and solar cf, which may drive the clustering weirdly 
    # ax.set_xlim([12.3, 12.8])
    # ax.set_ylim([55.5, 55.8])
    ## Nordjylland region - Nær Læsø
    # ax.set_xlim([10, 11.3])
    # ax.set_ylim([57.0, 57.5])
    ## Vestjylland region - Nær Fanø
    # ax.set_xlim([8.2, 9])
    # ax.set_ylim([55.2, 55.7])
    ## Storebælt
    # ax.set_xlim([10.3, 11.6])
    # ax.set_ylim([55.0, 55.6])
    ## Samsø
    # ax.set_xlim([10, 11.5])
    # ax.set_ylim([55.4, 56.1])
    
    return fig, ax, clustering

@click.command()
@click.option('--model-path', type=str, required=True, help='Balmorel model path')
@click.option('--scenario', type=str, required=True, help='Balmorel scenario')
@click.option('--cluster-params', type=str, required=True, help='Comma-separated list of Balmorel input data to cluster (use the symbol names, e.g. DE for annual electricity demand)')
@click.option('--aggregation-functions', type=str, required=True, help='Comma-separated list of aggregation functions used for clustering (E.g. sum for annual electricity demand and mean for wind full-load hours)')
@click.option('--cluster-size', type=int, required=True, help='How many clusters?')
@click.option('--plot-style', type=str, required=False, help='Style of the plot. Options are "report" (bright background) or "ppt" (dark background)')
def main(model_path: str, 
         scenario: str, 
         cluster_params: str,
         aggregation_functions: str,
         cluster_size: int,
         plot_style: str = 'report'):

    # Convert comma-separated string to list
    cluster_params_list = cluster_params.replace(' ', '').split(',')
    aggfuncs = aggregation_functions.replace(' ', '').split(',')

    # Plot styles
    if plot_style == 'report':
        plt.style.use('default')
        fc = 'white'
    elif plot_style == 'ppt':
        plt.style.use('dark_background')
        fc = 'none'

    # Collect Balmorel input data from scenario
    model = Balmorel(model_path)
    model.load_incfiles(scenario)

    # Get parameters for clustering    
    collected = gather_data(model.input_data[scenario], 
                            cluster_params_list, aggfuncs)
    
    # Do clustering
    fig, ax, clustering = cluster(collected, cluster_size, connection_remark='', data_remark=cluster_params)
    fig.savefig('ClusterOutput/Figures/clustering.pdf', transparent=True, bbox_inches='tight')
    clustering.to_file('ClusterOutput/clustering.gpkg')

if __name__ == '__main__':
    main()