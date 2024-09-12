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
import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
from Modules.geofiles import prepared_geofiles
from scipy.sparse import csr_matrix
from Modules.Submodules.municipal_template import DataContainer
from Modules.createFLEXDEM import distribute_road_flex_electricity_demand
from Modules.createDH import DistrictHeatAAU
from Modules.Submodules.energinet_electricity import energinet_el
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import kneighbors_graph

style = 'report'

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

#%%
if __name__ == '__main__':

    # 1.1 Collect Data
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

    #%% Plot CF
    fig, ax = plt.subplots()
    con.get_polygons().plot(
        ax=ax,
        column=con.muni.solar_cf.data,
        legend=True,
        vmin=0,
        vmax=0.175
    )

    #%% 1.2 Cluster

    # Clustering
    ## Coordinates for clustering
    X = np.vstack((
        # con.muni.coords['lat'].data,
        # con.muni.coords['lon'].data,
        con.muni.electricity_demand_mwh.sum(dim=['year', 'user']),
        con.muni.heat_demand_mwh.sum(dim=['year', 'user']),
        # con.muni.wind_cf.data,
        # con.muni.solar_cf.data,
    )).T
    
    ## General cluster parameters
    n_clusters = 4

    ## K-Means Clustering
    # est = KMeans(n_clusters=n_clusters)
    # est.fit(X)

    ## Agglomorative clustering
    linkage = 'ward'

    X = StandardScaler().fit_transform(X) # Normalise dataset
    ## Make higher weighting of coordinates
    # X[:,0] = X[:,0]*10000
    # X[:,1] = X[:,1]*10000


    ## Connectivity
    # ### Using knegihbours_graph
    # knn_graph = kneighbors_graph(X, 4, include_self=True)
    knn_graph = None
    knn_graph = pd.DataFrame(index=x.get_polygons().index,
             columns=x.get_polygons().index)
    knn_graph.loc[:] = 1
    ### Disallow connection between Favrskov and Aarhus
    knn_graph.loc['Favrskov', 'Aarhus'] = 0
    knn_graph.loc['Aarhus', 'Favrskov'] = 0

    ### Make it symmetric
    knn_graph = np.array(knn_graph).astype(int)
    # knn_graph = csr_matrix((knn_graph + knn_graph.T)/2)


    agg = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage,
                                connectivity=knn_graph)
    agg.fit(X)
    
    
    # Plot the different clustering techniques
    geos = con.get_polygons()
    for name, labelling in [(linkage, agg.labels_)]:
        fig, ax = plt.subplots()
        geos[name] = labelling
        geos.plot(column=name, ax=ax)
        ax.set_title(name + ' - clusters: %d'%n_clusters)
        