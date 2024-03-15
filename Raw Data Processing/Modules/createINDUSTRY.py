"""
Created on 14.03.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)

Script for creating data for industry sector
Sources:
    - Balmorel Data 2024
    - Manz, Pia, Tobias Fleiter, and Wolfgang Eichhammer. “The Effect of Low-Carbon Processes on Industrial Excess Heat Potentials for District Heating in the EU: A GIS-Based Analysis.” Smart Energy 10 (May 1, 2023): 100103. https://doi.org/10.1016/j.segy.2023.100103.

"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import os 
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import geopandas as gpd
from Modules.geofiles import prepared_geofiles
from shapely.geometry import Point, Polygon, LineString
from typing import Union

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

choice = 'NUTS3'
the_index, areas, c = prepared_geofiles(choice)


#%% 1.0 Assumptions
XHLOSS = 0.1        # MWh/Mwh
XHCOST = 0.001      # €/Mwh
XHINVCOST = 396000  # €/MW


class Industry:
    """Class for district heating data
    
    Existing datasets:
        - Denmark

    Args:
        dataset (str, optional): _description_. Defaults to 'DK'.
    """
    
    def __init__(self, dataset: str = 'EUBalmorel') -> None:
        if dataset.lower() == 'eubalmorel': 
            choice = 'Balmorel2022'
            the_index, self.geo, c = prepared_geofiles(choice)
            
            # Load data
            datasets = pd.Series([ds0 for ds0 in os.listdir('Data/BalmorelData') if 'INDUSTRY' in ds0])

            for ds in datasets:
                setattr(self, ds.replace('INDUSTRY_', '').replace('.gzip', ''), pd.read_parquet('Data/BalmorelData/' + ds))
            
        else:
            print("Dataset doesn't exist - this is an empty object\n")
            print("Available datasets:\n- EUBalmorel (default)")

        # Load high resolution dataset
        self.PS = pd.read_csv('Data/Gas, Transport and Industry Data/Industrial_Database.csv',
                              sep=';', encoding='UTF-8')
        
        # Delete sources with no coordinates (you could look the cities up with google maps API)
        self.PS = self.PS[self.PS.Latitude.isna() == False]
        self.PS.index = np.arange(len(self.PS)) # Fix index
        
        # Fill NaN's with zeros
        self.PS['Emissions_ETS_2014'] = self.PS['Emissions_ETS_2014'].fillna(0)
        
        self.PS['geometry'] = gpd.GeoSeries([Point(xy) for xy in zip(self.PS.Longtitude, self.PS.Latitude)])
        self.PS = gpd.GeoDataFrame(self.PS)
        self.PS.geometry.crs = 'EPSG:4326'
        self.geoindex = the_index
        

    def assign_original_region(self, geo_index):
        self.PS['R'] = ''  
        for PS in self.PS.index:
            # Find containing region
            idx = self.geo.contains(self.PS.geometry[PS])
            try:
                self.PS.loc[PS, 'R'] = self.geo.loc[idx, geo_index].iloc[0] # Should only have one value
            except IndexError:
                # If it's not contained within a region, use smallest distance
                temp = self.geo.copy().to_crs('EPSG:4328')
                dist = temp.distance(self.PS.geometry[PS])

                try:
                    self.PS.loc[PS, 'R'] = dist[dist == dist.min()].index[0] # Should only have one value
                except IndexError:
                    print('Datapoint %d probably had invalid geometry'%PS)
            except:
                print('something wrong with point %d'%PS)

    def assign_emission_fractions(self):
        # Use EPRTR emissions for CH
        self.PS.loc[self.PS.R == 'CH', 'Emissions_ETS_2014'] = self.PS[self.PS.R == 'CH']['Emissions_EPRTR_2014']
        # RS only has one source with no data
        self.PS.loc[self.PS.R == 'RS', 'Emissions_ETS_2014'] = 0

        # Total emissions in a region
        emisum = self.PS.pivot_table(index='R', values=['Emissions_ETS_2014'], fill_value=0)

        # The fraction of emissions at point sources
        for R in self.PS.R.unique():
            idx = self.PS.R == R
            self.PS.loc[idx, 'EmiFrac'] = self.PS.loc[idx, 'Emissions_ETS_2014'] * emisum.loc[R, 'Emissions_ETS_2014']  


    
    
# def find_containing_geometries(gdf: gpd.GeoDataFrame, 
#                                geo: Union[Point, Polygon, LineString]) -> gpd.GeoDataFrame:
#     # Find elements containing shape
#     idx = gdf.geo.contains(geo)

#     return gdf.loc[idx].iloc[0]    
    

IND = Industry()

#%% 1.1 Take a look at DK
fig, ax = plt.subplots()
IND.geo.loc[['DK1', 'DK2']].plot(ax=ax, facecolor=[.85 for i in range(3)])
IND.PS[IND.PS.Country == 'Denmark'].plot(ax=ax, marker='o', color=[.3, .3, .3],
                                         markersize=IND.PS.loc[IND.PS.Country == 'Denmark', 
                                                               'Emissions_ETS_2014']/1e4)
ax.set_ylabel('Latitude')
ax.set_xlabel('Longitude')
fig.savefig('Output/Figures/IND_original.png', bbox_inches='tight')
fig.savefig('Output/Figures/IND_original.pdf', bbox_inches='tight')

### 1.2 Assign Original Region
IND.assign_original_region(IND.geoindex)

# Assign fraction of emissions in region
IND.assign_emission_fractions() # The numbers in EmiFrac can be used directly on 


#%%

choice = 'NUTS3'
the_index, areas, c = prepared_geofiles(choice)
areas = areas[areas[the_index].str.find('DK') != -1]

#%%

# Calculate 



# Need to make incfiles:
# INDUSTRY_AGKN
# INDUSTRY_CCCRRRAAA
# INDUSTRY_RRRAAA
# INDUSTRY_AAA
# INDUSTRY_GKFX
# INDUSTRY_DH
# INDUSTRY_DH_VAR_T
# INDUSTRY_DE
# INDUSTRY_DE_VAR_T

# Later:
# INDUSTRY_XHMAXK
# INDUSTRY_XHKFX
# INDUSTRY_XHLOSS
# INDUSTRY_XHCOST
# INDUSTRY_XHINVCOST

