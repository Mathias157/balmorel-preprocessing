"""
TITLE

Description

Created on 28.08.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import geopandas as gpd
import xarray as xr
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###  1. Template for Balmorel Input ###
### ------------------------------- ###

class DataContainer():
    def __init__(self) -> None:    

        # Load municipal shapefiles
        muni_geofile = gpd.read_file(r'Data\Shapefiles\Denmark\Adm\gadm36_DNK_2.shp')
        
        # Make xarray
        self.muni = xr.Dataset()
        
        # Get only municipal names and geometries
        temp = (
            muni_geofile.set_index('NAME_2')
            .copy()
            .geometry
        )
        temp.index.name = 'Municipality'
        temp.index = temp.index.astype('category')
        
        # Assign to xarray
        self.muni['Polygons'] = temp 
        self.muni['Polygons'] = self.muni.Polygons.assign_attrs({'geo_crs' : muni_geofile.crs})
        self.muni['Polygons'] = self.muni.Polygons.assign_attrs({'pro_crs' : 'EPSG:4093'})

        # Get lat and long of centroids as well
        centroids = self.get_polygons(coord_system='projected').centroid
        self.muni.coords['lon'] = centroids.x
        self.muni.coords['lat'] = centroids.y
        
    def get_polygons(self, resolution: str = 'muni',
                    coord_system: str = 'geographic'):
        geo = gpd.GeoDataFrame(geometry=getattr(self, resolution).Polygons.data,
                                crs=getattr(self, resolution).Polygons.geo_crs)
        
        if coord_system != 'geographic':
            geo = geo.to_crs(getattr(self, resolution).Polygons.pro_crs)
        
        return geo
        

x = DataContainer()


# Clustering
## Coordinates for clustering
X = np.vstack((
    x.muni.coords['lon'].data,
    x.muni.coords['lat'].data
)).T

## K-Means Clustering
n_clusters = 30
est = KMeans(n_clusters=n_clusters)
est.fit(X)

## Agglomorative clustering
linkage = 'ward'

X = StandardScaler().fit_transform(X) # Normalise dataset
agg = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
agg.fit(X)
    
# Plot the different clustering techniques
geos = x.get_polygons('muni')
for name, labelling in [('K-Means', est.labels_), 
                        (linkage, agg.labels_)]:
    fig, ax = plt.subplots()
    geos[name] = labelling
    geos.plot(column=name, ax=ax)
    ax.set_title(name + ' - clusters: %d'%n_clusters)
    
    
# Merge cluster to dataset
clustered_data = xr.Dataset(
    {
        "Cluster" : (
            # ('Municipality', 'lon', 'lat'),
            'Municipality',
            # np.vstack([labels]*3)
            labelling
        )
    },
    # coords={coord : x.muni.coords[coord].data for coord in x.muni.coords}
    coords={'Municipality' : x.muni.coords['Municipality']}
)

# Merge clustering to xarray
x.muni = x.muni.merge(clustered_data)

