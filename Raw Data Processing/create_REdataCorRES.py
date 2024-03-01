"""
Created on 31.10.2023

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

# import netCDF4

style = 'report'
if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###        1. Exclusion Zones       ###
### ------------------------------- ###

### 1.1 Open .nc file with Xarray
path = r'C:\Users\mberos\OneDrive - Danmarks Tekniske Universitet\Work\Balmorel Automation\VRE Update\Shapefiles\Exclusion Zones\EMODnet_bathymetry_2022.nc'
nc = xr.open_dataset(path)

### 1.2 Open Exclusion Grid
path = r'C:\Users\mberos\OneDrive - Danmarks Tekniske Universitet\Work\Balmorel Automation\VRE Update\Shapefiles\Exclusion Zones\BalmGrid-Urb-GLWD123fix-WDPA012-MTabove1km.gpkg'
grid = gpd.read_file(path)
grid = grid.set_crs('EPSG:4326')
# grid.plot(markersize=.03) # Plot

#%% 1.3 Deleting Grid Points (Matrix Slice Method)

# # European cross-section
# lon0 = [-25, 42]
# lat0 = [33, 73]
# dlon = lon0[1] - lon0[0]
# dlat = lat0[1] - lat0[0]

# slices = 10
# for slice_x in range(2, 3):
#     for slice_y in range(5,6): 
    
#         fig, ax = plt.subplots()
#         lo0 = lon0[0] + slice_x*dlon/slices
#         la0 = lat0[0] + slice_y*dlat/slices
        
#         # Get elevation
#         idx_lon = (nc.elevation.lon >= lo0) & (nc.elevation.lon < lo0 + dlon/slices)
#         idx_lat = (nc.elevation.lat >= la0) & (nc.elevation.lat < la0 + dlat/slices)

#         nc.elevation[idx_lat, idx_lon].plot(ax=ax)

#         # idx_depth = nc.elevation[idx_lat, idx_lon].values > -50
#         # nc.elevation[idx_lat, idx_lon]

#         # Get points
#         idx = (grid.geometry.x >= lo0) & (grid.geometry.x < lo0 + dlon/slices) & (grid.geometry.y >= la0) & (grid.geometry.y < la0 + dlat/slices)
#         grid[idx].plot(ax=ax, color='k')
        
#         for i, point in grid[idx].iterrows():
#             lo0 = point.geometry.x
#             la0 = point.geometry.y

#             idx_lon = (nc.elevation.lon >= lo0) & (nc.elevation.lon < lo0 + 0.001)
#             idx_lat = (nc.elevation.lat >= la0) & (nc.elevation.lat < la0 + 0.001)

#             depth = np.mean(nc.elevation[idx_lat, idx_lon].fillna(0).values)

#             if not(pd.isna(depth)) & (depth < -50):
#                 # print('Depth: %0.02f'%(depth))
#                 print(grid.loc[i])
                        
#         grid[idx].plot(ax=ax, color='r', markersize=.8)
#         # Delete those that are below 50 meters

#%% 1.3 Deleting Grid Points

for i, point in grid.iterrows():

    lo0 = point.geometry.x
    la0 = point.geometry.y
    delta = 0.002

    idx_lon = (nc.elevation.lon >= lo0 - delta) & (nc.elevation.lon < lo0 + delta)
    idx_lat = (nc.elevation.lat >= la0 - delta) & (nc.elevation.lat < la0 + delta)

    if not(np.all(~idx_lon.values) | np.all(~idx_lat.values)):
        
        depth = np.mean(nc.elevation[idx_lat, idx_lon].fillna(0).values)

        # if depth < 0:
        #     # print(depth)

        #     fig, ax = plt.subplots()
        #     ax.plot([point.geometry.x], [point.geometry.y], 'ko')
        #     nc.elevation[idx_lat, idx_lon].plot(ax=ax)
        #     ax.set_title('i: %d, Depth: %0.2f'%(i, depth))

        if depth < -50:
            # ax.plot(point.geometry.x, point.geometry.y, 'r|')
            grid.loc[i] = None

grid2 = grid.dropna()
grid2.to_file('BalmGrid-Urb-GLWD123fix-WDPA012-MTabove1km-over50mSea2.gpkg')


#%%
# lo0 = -5
# la0 = 54.25
# delta0 = 7.5
# delta1 = 5.75


# idx_lon = (nc.elevation.lon >= lo0 - delta0) & (nc.elevation.lon < lo0 + delta0)
# idx_lat = (nc.elevation.lat >= la0 - delta1) & (nc.elevation.lat < la0 + delta1)
# idx = (grid.geometry.x >= lo0 - delta0) & (grid.geometry.x < lo0 + delta0) & (grid.geometry.y >= la0 - delta1) & (grid.geometry.y < la0 + delta1)
   

# fig, ax = plt.subplots()
# nc.elevation[idx_lat, idx_lon].plot(ax=ax)
# grid[idx].plot(ax=ax, markersize=.5, color='k')
