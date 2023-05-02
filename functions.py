#%%
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  3 15:33:10 2022

@author: mathi

See the following documentation, for understanding how this script works:
    Cutouts: https://atlite.readthedocs.io/en/latest/examples/create_cutout.html
    Power potentials: https://atlite.readthedocs.io/en/latest/examples/landuse-availability.html

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc
from formplot import *
from scipy.optimize import curve_fit
import atlite
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import MultiPolygon
from pyproj import Proj, Transformer
from rasterio.plot import show
import xarray as xr
from atlite.gis import shape_availability, ExclusionContainer
import os

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'


### ------------------------------- ###
### 1. Load Geodata and Pre-process ###
### ------------------------------- ###
def PreProcessShapes(choice, plot='n'):
    """

    Parameters
    ----------
    choice : str
        Currently supports: 
            'DK Municipalities'
            'NUTS1'
            'NUTS2'
            'NUTS3' 
            'Nordpool'.
            'NordpoolReal'
            'BalmorelVREAreas'
            
    plot : str
        Chooses to plot or not

    Returns
    -------
    area_names : Array of str
        The region names.
        
    areas : GeoDataFrame
        The pre-processed shapefile, including all metadata.

    """

    ## Projections
    UTM32 = Proj(proj='utm', zone=32, ellps='WGS84', preserve_units=False)
    GM = Proj('EPSG:900913', preserve_units=False)
    # transformer = Transformer.from_crs('EPSG:900913', 'EPSG:4326')
    # out = Transformer(GM, UTM32, (11, 13), (43, 45), always_xy=True) 

    ## 1.1 Load geodata files
    # DKmunicipal 
    if choice.replace(' ','').lower() == 'dkmunicipalities':
    # Filter away unnescescary columns
    # areas = areas[['NAME_1', 'NAME_2', 'geometry']]
        areas = gpd.read_file(r'.\Data\Shapefiles\Denmark\Adm\gadm36_DNK_2.shp')
        # # Aggregate hovedstaden - MODIFY TO USE NUTS3 AREAS FOR CAPITAL REGION
        # idx = (areas.NAME_1 == 'Hovedstaden') & (areas.NAME_2 != 'Bornholm') & (areas.NAME_2 != 'Christiansø')
        # hovedstaden = MultiPolygon(areas[idx].geometry.cascaded_union)
        # areas = areas.drop(index=list(areas.index[idx]))
        # areas = pd.concat((areas, gpd.GeoDataFrame({'NAME_1' : 'Hovedstaden', 
        #                       'NAME_2' : 'København',
        #                       'GID_2' : 'DNK.5.23_1',
        #                       'geometry' : [hovedstaden]})))
        area_names = 'GID_2'
        
        # Change DNK to DK
        areas.loc[:, area_names] = areas.loc[:, area_names].str.replace('DNK', 'DK')
        
        # Change . to _
        areas.loc[:, area_names] = areas.loc[:, area_names].str.replace('.', '_')

        
    # NUTS3 (Also contains NUTS2, and NUTS1)
    elif choice.replace(' ','').lower() == 'nuts1':
        areas = gpd.read_file(r'.\Data\Shapefiles\NUTS_RG_01M_2021_4326\NUTS_RG_01M_2021_4326.shp')
        areas = areas[(areas.LEVL_CODE == 1)] 
        
        # The index for next file
        area_names = 'NUTS_ID'
        
        # Filter only DK
        # areas = areas[areas.NUTS_ID.str.find('DK') != -1]
    
    elif choice.replace(' ','').lower() == 'nuts2':
        areas = gpd.read_file(r'.\Data\Shapefiles\NUTS_RG_01M_2021_4326\NUTS_RG_01M_2021_4326.shp')
        areas = areas[(areas.LEVL_CODE == 2)] 
        
        # The index for next file
        area_names = 'NUTS_ID'
        
        # Filter only DK
        # areas = areas[areas.NUTS_ID.str.find('DK') != -1]
        
    elif choice.replace(' ','').lower() == 'nuts3':
        areas = gpd.read_file(r'.\Data\Shapefiles\NUTS_RG_01M_2021_4326\NUTS_RG_01M_2021_4326.shp')
        areas = areas[(areas.LEVL_CODE == 3)]
        
        # The index for next file
        area_names = 'NUTS_ID'
        
        # Filter only DK
        # areas = areas[areas.NUTS_ID.str.find('DK') != -1]
        
    # Nordpool market regions
    elif choice.replace(' ','').lower() == 'nordpool':
        p = r'.\Data\Shapefiles\NordpoolRegions\geojson'
        
        areas = gpd.GeoDataFrame()
        for file in os.listdir(p):
            areas = pd.concat((areas, gpd.read_file(p+'/'+file)), ignore_index=True)
        area_names = 'zoneName'
        
        # Filter only DK
        # areas = areas[(areas.zoneName == 'DK_1') | (areas.zoneName == 'DK_2')]
    
    elif choice.replace(' ','').lower() == 'nordpoolreal':
        p = r'.\Data\Shapefiles\NordpoolRegions\geojson_real'
        
        i = 0
        areas = gpd.GeoDataFrame({'RRR' : []})
        for file in os.listdir(p):
            areas = pd.concat((areas, gpd.read_file(p+'/'+file)), ignore_index=True)
            areas.loc[i, 'RRR'] = file.strip('.geojson')
            i += 1
            
        # Filter Russia
        areas = areas[areas.RRR != 'RU']
        areas['Country'] = areas.RRR.str[:2]
        area_names = 'RRR'
        country_code = 'Country'
    
    elif choice.replace(' ','').lower() == 'balmorelvreareas':
        areas = gpd.read_file(r'.\Data\Shapefiles\BalmorelVRE\BalmorelVREAreas.gpkg')
        area_names = 'Region' 
        country_code = 'Country'
    
    else:
        print("You didn't choose any geodata! Check spelling or create new elif statement in code block 1.2")
    
    areas.index = areas[area_names]
        
        
    ### 1.2 Visualise current areas
    # Set projection
    crs = ccrs.UTM(32)
    # Make compatible with geopandas
    # projection = crs.proj4_init # doesn't work, so actually cartopy is useless - continuing only with geopandas

    if plot == 'y':
        # Make figure
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={"projection": crs},
                               dpi=200)
    
    
        # Add areas
        ax.add_geometries(areas.geometry, crs = crs,
                          facecolor=[.9, .9,.9], edgecolor='grey',
                          linewidth=.2)
    
        ax.set_xlim(areas.bounds[['minx']].values.min(), areas.bounds[['maxx']].values.max())
        ax.set_ylim(areas.bounds[['miny']].values.min(), areas.bounds[['maxy']].values.max())
    # ax.set_xlim(7.5,16)      
    # ax.set_ylim(54.4,58)  


    ### 1.3 Load Nordpool regions
    # NP = pd.read_csv(project_dir/'geo_files/coordinates_RRR.csv')
    # NP = NP.loc[df_unique['Type'] == 'region', ]

    if not('country_code' in locals()):
        print('No country code defined in these shapefiles.')
        country_code = 'No country code'  

    return area_names, areas, country_code












