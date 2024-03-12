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
import matplotlib.pyplot as plt
import geopandas as gpd
import cartopy.crs as ccrs
from pyproj import Proj
import os

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'


### ------------------------------- ###
### 1. Load Geodata and Pre-Process ###
### ------------------------------- ###
def prepared_geofiles(choice: str, plot: bool = False) -> tuple[str, gpd.GeoDataFrame, str]:
    """
    Prepared geofiles for various spatial resolutions

    Parameters
    ----------
    choice : str
        Currently supports:\n
            'DK Municipalities'\n
            'NUTS1'\n
            'NUTS2'\n
            'NUTS3'\n
            'Nordpool'\n
            'NordpoolReal'\n
            'BalmorelVREAreas'\n
            'Antbalm'\n
            
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
    # UTM32 = Proj(proj='utm', zone=32, ellps='WGS84', preserve_units=False)
    # GM = Proj('EPSG:900913', preserve_units=False)
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
    elif choice.replace(' ','').lower() == 'antbalm':
        areas = gpd.read_file(r'.\Data\Shapefiles\240112 AntBalmMap.gpkg')
        areas.loc[(areas.ISO_A3 == 'FIN'), 'id'] = 'FIN'
        areas.loc[(areas.ISO_A3 == 'DZA'), 'id'] = 'DZA'
        areas.loc[(areas.ISO_A3 == 'EGY'), 'id'] = 'EGY'
        areas.loc[(areas.ISO_A3 == 'LBY'), 'id'] = 'LBY'
        areas.loc[(areas.ISO_A3 == 'MAR'), 'id'] = 'MAR'
        areas.loc[(areas.ISO_A3 == 'TUN'), 'id'] = 'TUN'
        areas = areas[areas.NAME_0 != 'Finland']
        area_names = 'id'
        country_code = 'ADMIN'
    else:
        print("You didn't choose any geodata! Check spelling or create new elif statement in code block 1.2")
    
    areas.index = areas[area_names]
    areas.geometry = areas['geometry']
        
        
    ### 1.2 Visualise current areas
    # Set projection
    crs = ccrs.UTM(32)
    # Make compatible with geopandas
    # projection = crs.proj4_init # doesn't work, so actually cartopy is useless - continuing only with geopandas

    if plot:
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

def calculate_intersects(areas_inter1: gpd.GeoDataFrame, 
                    areas_inter2: gpd.GeoDataFrame, 
                    sum_total: bool = False) -> pd.DataFrame:        
        """Calculates intersection of the series of areas_inter2 to each areas_inter1 element 

        Args:
            areas_inter1 (gpd.GeoDataFrame): _description_
            areas_inter2 (gpd.GeoDataFrame): _description_
            sum_total (bool, optional): _description_. Defaults to False.

        Returns:
            pd.DataFrame: _description_
        """

        # Convert to geocentric projection
        temp_area1 = areas_inter1.to_crs(4328) # To geocentric (meters)
        temp_area2 = areas_inter2.to_crs(4328) # To geocentric (meters)

        # Find intersection of DH shapes to each element in aggregated areas
        df_intercepts = pd.DataFrame()
        for agg_area in temp_area1.index:
            df_intercepts[agg_area] = temp_area2.geometry.intersection(temp_area1.geometry[agg_area]).area
        
        if sum_total:
            # Divide by total area:
            df_intercepts = df_intercepts.div(temp_area2.area, axis=0)
            
        else:
            # Divide by sum of intersected areas
            df_intercepts = df_intercepts.div(df_intercepts.sum(axis=1), axis=0)
        
        return df_intercepts










