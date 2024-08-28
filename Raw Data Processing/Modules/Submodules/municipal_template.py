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
from sklearn.cluster import KMeans

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
        self.muni['Polygons'] = self.muni.Polygons.assign_attrs({'crs' : muni_geofile.crs})

        # Get lat and long of centroids as well
        centroids = self.get_geodata().centroid
        self.muni.coords['lon'] = centroids.x
        self.muni.coords['lat'] = centroids.y
        
    def get_geodata(self, resolution: str = 'muni'):
        return gpd.GeoDataFrame(geometry=getattr(self, resolution).Polygons.data,
                                crs=getattr(self, resolution).Polygons.crs)
        

x = DataContainer()

#%%

# Coordinates for clustering
X = np.vstack((
    x.muni.coords['lon'].data,
    x.muni.coords['lat'].data
)).T

# K-Means Clustering
n_clusters = 3
est = KMeans(n_clusters=n_clusters)
est.fit(X)

labels = est.labels_
plt.scatter(X[:, 0].T, X[:, 1].T, c=labels, edgecolor="k")