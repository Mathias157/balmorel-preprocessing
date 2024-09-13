"""
TITLE

Description

Created on 11.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import matplotlib.colors as mcol
import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
from Modules.geofiles import prepared_geofiles
from pybalmorel import Balmorel
from pybalmorel.utils import symbol_to_df
from scipy.sparse import csr_matrix
from Modules.Submodules.municipal_template import DataContainer
from Modules.createFLEXDEM import distribute_road_flex_electricity_demand
from Modules.createDH import DistrictHeatAAU
from Modules.Submodules.energinet_electricity import energinet_el
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
    
style = 'ppt'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

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
                                    column_to_convert: (str, int),
                                    pivot_table: bool = False,
                                    exclude_regions: list = ['Herlev', 'Christiansø'],
                                    muni_geofile_path: str = r'C:\Users\mberos\gitRepos\balmorel-preprocessing\Raw Data Processing\Data\Shapefiles\Denmark\Adm\gadm36_DNK_2.shp'):

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


def collect_clusterdata(energinet_el: pd.DataFrame,
                        plot_cf: bool = False):

    con = DataContainer()
    
    ## Annual Heat Demand
    temp = DistrictHeatAAU()
    temp.combine_data()
    con.muni = con.muni.merge(temp.data)
    
    ## Annual Electricity Demands - assume 2023 = 2019
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


def cluster(con: DataContainer,
            n_clusters: int,
            use_connectivity: bool = True,
            manual_corrections: list = [
                ['Bornholm', 'Christiansø', 1],
                ['Bornholm', 'Dragør', 1],
                ['Esbjerg', 'Fanø', 1],
                ['Rødovre', 'Frederiksberg', 1],
                ['Slagelse', 'Nyborg', 0],
                ['Samsø', 'Kalundborg', 0]
            ],
            connection_remark: str = 'connec. included + artifical',
            data_remark: str = 'all combined + xy coords'):
    
    # Stack data for clustering
    X = np.vstack((
        con.muni.coords['lat'].data,
        con.muni.coords['lon'].data,
        con.muni.electricity_demand_mwh.sum(dim=['year', 'user']),
        con.muni.heat_demand_mwh.sum(dim=['year', 'user']),
        con.muni.wind_cf.data,
        con.muni.solar_cf.data,
    )).T

    # K-Means Clustering
    # est = KMeans(n_clusters=n_clusters)
    # est.fit(X)

    # Agglomorative clustering
    linkage = 'Ward'

    X = StandardScaler().fit_transform(X) # Normalise dataset
    ## Make higher weighting of coordinates..?
    # X[:,0] = X[:,0]*10000
    # X[:,1] = X[:,1]*10000


    # Connectivity
    if use_connectivity:
        ## Use connectivity from Balmorel (Submodules/get_grid.py)
        connectivity = xr.load_dataset(r'Data\Power Grid\municipal_connectivity.nc')

        ## Manual Corrections
        for manual_connection in manual_corrections:
            connectivity.connection.loc[manual_connection[0], manual_connection[1]] = manual_connection[2]
            connectivity.connection.loc[manual_connection[1], manual_connection[0]] = manual_connection[2]
            
        knn_graph = connectivity.connection.data # get numpy array
        knn_graph = csr_matrix(knn_graph) # make dense format
    else:
        knn_graph = None # don't apply connectivity constraints

    # Perform Clustering
    agg = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage.lower(),
                                connectivity=knn_graph)
    agg.fit(X)
    
    
    # Plot the different clustering techniques
    clustering = con.get_polygons()
    for name, labelling in [(linkage, agg.labels_)]:
        
        # Set labels
        clustering['cluster_group'] = labelling

        # Plot clustering
        fig, ax = plt.subplots()
        clustering.plot(column='cluster_group', 
                  ax=ax, 
                #   legend=True,
                  cmap=truncate_colormap(cmap, 0.2, 1))
        
        if knn_graph == None:
            connection_remark = 'no connectivity'

        plot_title = '%s, %d clusters, %s\ndata: %s'%(name, 
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

if __name__ == '__main__':
    collected = collect_clusterdata(energinet_el)
    fig, ax, clustering = cluster(collected, 20)
