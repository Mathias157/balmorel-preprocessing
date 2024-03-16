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
from pybalmorel.functions import IncFile, read_lines
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
###        1. Industry Data         ###
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


    def apply_ef_to_original_data(self, incfiles: dict, original_area: str, 
                  new_area: str, frac_sum: str, include_new_area: bool = False) -> None:
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
    
    def create_industry_data(self, areas: gpd.GeoDataFrame,
                             save_new_area_to_df: bool = False,
                             plot_point_sources: bool = False,
                             ax: matplotlib.axes.Axes = '') -> dict:
        """Prepares industry data .inc files  
        """
        
        # Placeholder for incfiles
        incfiles = {}
        incfilenames = ['INDUSTRY_AGKN', 'INDUSTRY_DE', 'INDUSTRY_DH',
                        'INDUSTRY_DH_VAR_T', 'INDUSTRY_GKFX', 'INDUSTRY_CCCRRRAAA',
                        'INDUSTRY_RRRAAA', 'INDUSTRY_AAA'] 
        for name in incfilenames:
            incfiles[name] = IncFile(name=name,
                                    path='Output',
                                    body=pd.DataFrame(),
                                    prefix=read_lines(name+'_prefix.inc',
                                                      file_path='Data/IncFilePreSuf'),
                                    suffix=read_lines(name+'_suffix.inc',
                                                      file_path='Data/IncFilePreSuf'))
            
        for new_area in areas.index:
            idx = self.PS.within(areas.geometry[new_area])
            
            try:
                if plot_point_sources & (ax != ''):
                    self.PS[idx].plot(ax=ax, zorder=5)
                
                # Get original areas (can be more, if the chosen spatial resolution is coarser than the original)
                original_areas = self.PS.R[idx].unique()

                # Go through original areas
                for original_area in original_areas:    
                    
                    # Sum fraction of emissions in the new area
                    frac_sum = self.PS.loc[idx & (self.PS.R == original_area), 'EmiFrac'].sum()
                    
                    # Disaggregate DH, DH_VAR_T, DE, GKFX
                    self.apply_ef_to_original_data(incfiles, original_area, new_area, frac_sum, save_new_area_to_df)
                    
                    # Disaggregate AGKN
                    temp = self.AGKN[self.AGKN.A.str.find(original_area) != -1].copy()
                    temp['A'] = temp['A'].str.replace(original_area, new_area)
                    
                    incfiles['INDUSTRY_AGKN'].body_concat(temp) # perhaps make a IncFile.body.concat function..
            
            except ValueError:
                print('No industry in %s'%new_area)
                
        return incfiles
     
    def plot_original_data(self, emission_scale: float = 5e5, 
                           bounds: list[float, float, float, float] = [-12, 30, 33, 73]) -> tuple[matplotlib.figure.Figure, 
                                                                                                matplotlib.axes._axes.Axes]:        
        fig, ax = plt.subplots()
        self.geo.plot(ax=ax, facecolor=[.85 for i in range(3)])
        self.PS.plot(ax=ax, marker='o', color=[.3, .3, .3],
                    markersize=self.PS['Emissions_ETS_2014']/emission_scale)
        ax.set_title('Original Data')
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_xlim([bounds[0], bounds[1]])
        ax.set_ylim([bounds[2], bounds[3]])
        fig.savefig('Output/Figures/IND_original.png', bbox_inches='tight')
        fig.savefig('Output/Figures/IND_original.pdf', bbox_inches='tight')
        
        return fig, ax
    
    def plot_aggregated_data(self, incfiles: dict, 
                             areas: gpd.GeoDataFrame,
                             indicator: str = 'DH') -> tuple[matplotlib.figure.Figure, 
                                                            matplotlib.axes._axes.Axes]:
    
        # Generate industry data for a specific spatial resolution

        # Plot
        try:
            if indicator == 'DH':
                temp = incfiles['INDUSTRY_DH'].body.pivot_table(index=['Y', 'new_area'], values=['Value'], aggfunc='sum').loc['2050']
                areas['new_col'] = temp.Value / 1e6
                ax.set_title('Industry Heat Demand (TWh)')
            elif indicator == 'DE':        
                temp = incfiles['INDUSTRY_DE'].body.pivot_table(index=['Y', 'new_area'], values=['Value'], aggfunc='sum').loc['2050']
                areas['new_col'] = temp.Value / 1e6
                ax.set_title('Industry Electricity Demand (TWh)')
            elif indicator == 'GKFX':
                temp = incfiles['INDUSTRY_GKFX'].body.pivot_table(index=['Y', 'new_area'], values=['Value'], aggfunc='sum').loc['2020']
                areas['new_col'] = temp.Value 
                ax.set_title('Industry Generation Capacity (MW)')
            
            fig, ax = plt.subplots()
            areas.plot(ax=ax, zorder=2, column='new_col', legend=True, cmap=cmap)
            areas.plot(ax=ax, zorder=1, facecolor=cmap(0))
        
        except KeyError:
            print('New area column not created in .inc file')
            print('save_new_area_to_df was probably set to False in create_industry_data function')

        return fig, ax
    


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


