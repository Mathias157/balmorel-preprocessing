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
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import geopandas as gpd
from pybalmorel.functions import IncFile
from Modules.geofiles import prepared_geofiles
from shapely.geometry import Point, Polygon, LineString
from typing import Union
try:
    import cmcrameri
    cmap = cmcrameri.cm.cmaps['roma_r']
    colors = [cmap(i) for i in range(256)]
except ModuleNotFoundError:
    print('cmrameri package not installed, using default colourmaps')
    cmap = matplotlib.colormaps['viridis']
    colors = [cmap(i) for i in range(256)]

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

### 1.0 Assumptions
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
        

    def assign_original_region(self):
        self.PS['R'] = ''  
        for area in self.geo.index:
            # Find containing region
            idx = self.PS.within(self.geo.geometry[area])
            self.PS.loc[idx, 'R'] = area # Should only have one value

        # If it's not contained within a region, use smallest distance to find remaining
        for PS in self.PS[self.PS.R == ''].index:
            temp = self.geo.copy().to_crs('EPSG:4328')
            dist = temp.distance(self.PS.geometry[PS])

            try:
                self.PS.loc[PS, 'R'] = dist[dist == dist.min()].index[0] # Should only have one value
            except IndexError:
                print('Datapoint %d probably had invalid geometry'%PS)
        
    def assign_emission_fractions(self):
        # Use EPRTR emissions for CH
        self.PS.loc[self.PS.R == 'CH', 'Emissions_ETS_2014'] = self.PS[self.PS.R == 'CH']['Emissions_EPRTR_2014']
        # RS only has one source with no data
        self.PS.loc[self.PS.R == 'RS', 'Emissions_ETS_2014'] = 0

        # Total emissions in a region
        emisum = self.PS.pivot_table(index='R', values=['Emissions_ETS_2014'], fill_value=0, aggfunc='sum')

        # The fraction of emissions at point sources
        for R in self.PS.R.unique():
            idx = self.PS.R == R
            self.PS.loc[idx, 'EmiFrac'] = self.PS.loc[idx, 'Emissions_ETS_2014'] / emisum.loc[R, 'Emissions_ETS_2014']  


    def create_industry_data(self, incfiles: dict, original_area: str, 
                  new_area: str, frac_sum: str, include_new_area: bool = False):
        """Assign industry heat demand from original area to new area"""

        for attr in ['DH', 'DH_VAR_T', 'GKFX', 'DE']:
            # Find original Balmorel data
            if attr != 'DE':
                temp = getattr(self, attr)[getattr(self, attr).A.str.find(original_area) != -1].copy()
            else:
                temp = getattr(self, attr)[getattr(self, attr).R == original_area].copy()
            
            # Apply sum to Balmorel data
            temp.loc[:, 'Value'] = temp['Value'] * frac_sum
            
            # Replace original area name with new area name
            if attr != 'DE':
                temp.loc[:, 'A'] = temp['A'].str.replace(original_area, new_area)
            else:
                temp.loc[:, 'R'] = temp['R'].str.replace(original_area, new_area)
            
            if include_new_area:
                temp.loc[:, 'new_area'] = new_area # If wanting to plot it
            
            # Concatenate to body in incfile 
            incfiles['INDUSTRY_' + attr].body_concat(temp) 
    
    def create_industry_agkn():
        ...  
    
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
IND.assign_original_region()

# Assign fraction of emissions in region
IND.assign_emission_fractions() # The numbers in EmiFrac can be used directly on 


#%%

choice = 'NUTS3'
the_index, areas, c = prepared_geofiles(choice)
areas = areas[areas[the_index].str.find('DK') != -1]


# Placeholder for incfiles
incfiles = {}
incfilenames = pd.Series(os.listdir('Data/BalmorelData')).str.rstrip('.gzip') 
for name in incfilenames:
    incfiles[name] = IncFile(name=name,
                            path='Output',
                            body=pd.DataFrame())

# Calculate demands in area
fig, ax = plt.subplots()
df = pd.DataFrame(index=areas.index)
for R in areas.index:
    idx = IND.PS.within(areas.geometry[R])
    
    try:
        IND.PS[idx].plot(ax=ax, zorder=5)
        
        # Get original areas (can be more, if the chosen spatial resolution is coarser than the original)
        original_areas = IND.PS.R[idx].unique()

        # Go through original areas
        for original_area in original_areas:    
            
            # Sum fraction of emissions in the new area
            frac_sum = IND.PS.loc[idx & (IND.PS.R == original_area), 'EmiFrac'].sum()
            
            IND.create_industry_data(incfiles, original_area, R, frac_sum, True)
            
            # AGKN
            temp = IND.AGKN[IND.AGKN.A.str.find(original_area) != -1].copy()
            temp['A'] = temp['A'].str.replace(original_area, R)
            # incfiles['INDUSTRY_AGKN'].body = pd.concat((incfiles['INDUSTRY_AGKN'].body, temp)) # perhaps make a IncFile.body.concat function..
            incfiles['INDUSTRY_AGKN'].body_concat(temp) # perhaps make a IncFile.body.concat function..
    
    except ValueError:
        print('No industry in %s'%R)

temp = incfiles['INDUSTRY_DH'].body.pivot_table(index=['Y', 'new_area'], values=['Value'], aggfunc='sum').loc['2050']
# temp = incfiles['INDUSTRY_DE'].body.pivot_table(index=['Y', 'new_area'], values=['Value'], aggfunc='sum').loc['2050']
# temp = incfiles['INDUSTRY_GKFX'].body.pivot_table(index=['Y', 'new_area'], values=['Value'], aggfunc='sum').loc['2020']
areas['DH'] = temp.Value / 1e6
areas.plot(ax=ax, zorder=2, column='DH', legend=True, cmap=cmap)
areas.plot(ax=ax, zorder=1, facecolor=cmap(0))
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


