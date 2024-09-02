"""
Creating Danish heat demand for Balmorel 

Futuregas dataset default. Can be used to get temporal profiles

Aalborg dataset, can be used to get individual and district heat gross supply:
https://vbn.aau.dk/da/datasets/kommunepakker-varmeplan-danmark-2021
- Note that heat demand should be combined wrt. the s1-s5 scenarios (sums to 53.95 TWh without heat efficiency investments)

Python package requirements:
- xlrd 

Created on 11.03.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

from typing import Union
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from Modules.Submodules.aauvarmeplan2021 import VPDK21 
from Modules.Submodules.danmarks_statistik import DKSTAT 
from Modules.Submodules.municipal_template import DataContainer
import xarray as xr
import numpy as np
import os
try:
    import cmcrameri
    cmap = cmcrameri.cm.cmaps['roma_r']
    cmap = cmcrameri.cm.cmaps['vik']
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
###    1. FutureGas District Heat   ###
### ------------------------------- ###

class DistrictHeat:
    """Class for district heating data
    
    Existing datasets:
        - Denmark_Futuregas

    Args:
        dataset (str, optional): _description_. Defaults to 'DK'.
    """
    
    def __init__(self, dataset: str = 'Denmark_Futuregas') -> None:
        if dataset.lower() == 'denmark_futuregas': 
            DH_shapes = 'Data/Shapefiles/Balmorel Areas/Balmorel_areas.shp'
            name_col = 'BalmorelAr'
            # Load data
            self.DH = pd.read_parquet('Data/Timeseries/DKMUNI36_DH.gzip')
            self.DHT = pd.read_parquet('Data/Timeseries/DKMUNI36_DH_VAR_T.gzip')
            self.geo = gpd.read_file(DH_shapes)
            self.geo.index = self.geo[name_col]
            self.geo = self.geo.to_crs('EPSG:4326')
            
            # Delete CA_Vestfrb with no data in DH
            self.geo = self.geo.drop(index='DK_CA_Vestfrb')
            
            # Aggregate to the 36 DH areas:
            i = 0
            for dh_area in ['DK_SA_E_BG',
                            'DK_SA_E_NG_CHP',
                            'DK_SA_E_NG_HO',
                            'DK_SA_E_ST_CHP',
                            'DK_SA_E_ST_HO',
                            'DK_SA_E_WO_HO']:
                if i == 0:
                    temp = self.geo.loc[dh_area].copy()
                    temp.crs = 'EPSG:4326'
                else:
                    temp.geometry = temp.geometry.union(self.geo.loc[dh_area].geometry) 
                self.geo = self.geo.drop(index=dh_area)
                i += 1 
            self.geo.loc['DK_E_Rural'] = temp
            i = 0
            for dh_area in ['DK_SA_W_BG',
                            'DK_SA_W_EB',
                            'DK_SA_W_NG_CHP',
                            'DK_SA_W_NG_HO',
                            'DK_SA_W_ST_HO',
                            'DK_SA_W_WO_CHP',
                            'DK_SA_W_WO_HO']:
                if i == 0:
                    temp = self.geo.loc[dh_area].copy()
                else:
                    temp.geometry = temp.geometry.union(self.geo.loc[dh_area].geometry) 
                self.geo = self.geo.drop(index=dh_area)
                i += 1 
            self.geo.loc['DK_W_Rural'] = temp
            self.geo.crs = 'EPSG:4326'
  
        else: 
            print("Dataset doesn't exist - this is an empty object\n")
            print("Available datasets:\n- Denmark_Futuregas (default)")

    def assign_DH(self, areas: gpd.GeoDataFrame, df_intercepts: pd.DataFrame,
                  value_col: str = 'Value') -> None:
        """DH data must have A and Y sets, where A matches the areas index\n
        Ends up with format:\n
            Y1\tY2\tY3\t--\tYN\n
        A1\n
        A2\n 
        |\n
        AM
        """
        # DH table for IncFile
        df_DH = pd.DataFrame(index=areas.index) 
        
        # Use df_intercepts to assign DH
        temp = self.DH.pivot_table(index='A', columns='Y')
        
        # Check the dataframe structure
        if type(temp.columns) == pd.Index:
            col_ind = "year"
        elif type(temp.columns) == pd.MultiIndex:
            col_ind = "(value_col, year)"
        else:
            print('Wrong column format!')
        
        for agg_area in areas.index:
            for year in temp.columns.get_level_values(1):
                df_DH.loc[agg_area, year] = (temp.loc[:,eval(col_ind)] * df_intercepts[agg_area]).sum()

        self.dfDH = df_DH
        
        # Finalise index
        self.dfDH.index = 'RESH . ' + pd.Series(self.dfDH.index) + '_A'
        self.dfDH.index.name = '' 
        
    def assign_DHT(self, areas: gpd.GeoDataFrame, df_intercepts: pd.DataFrame,
                  value_col: str = 'Value', agg_func: str = 'sum') -> None:
        """DHT data must have S.T and A sets, where A matches the areas index\n
        Ends up with format:\n
        \t\t\tA1\tA2\tA3\t--\tAN\n
        S01\t.\tT001\n
        S01\t.\tT002\n
        |\n
        S52\t.\tT168\n
        """
        
        # Pivot DHT
        temp = self.DHT.pivot_table(index=['S', 'T'], columns='A')

        # DHT table for IncFile
        df_DHT = pd.DataFrame(index=temp.index, columns=areas.index,
                              data=0) 
        
        # Check the dataframe structure
        if type(temp.columns) == pd.Index:
            col_ind = "dh_area"
        elif type(temp.columns) == pd.MultiIndex:
            col_ind = "(value_col, dh_area)"
        else:
            print('Wrong column format!')
        
        if agg_func.lower() == 'sum':
            for agg_area in areas.index:
                for dh_area in [dh_area0 for dh_area0 in df_intercepts[agg_area].index if df_intercepts.loc[dh_area0, agg_area] > 1e-10]:
                    df_DHT[agg_area] += temp.loc[(slice(None),slice(None)),eval(col_ind)] * df_intercepts.loc[dh_area, agg_area]
                    print()

        self.dfDHT = df_DHT
        
        # Finalise index
        self.dfDHT.index = pd.Series(self.dfDHT.index.get_level_values(0)) + ' . ' + pd.Series(self.dfDHT.index.get_level_values(1))
        self.dfDHT.index.name = ''
        self.dfDHT.columns.name = ''
        self.dfDHT.columns = pd.Series(self.dfDHT.columns) + '_A'


    def assign_DH_profile():
        ...
    
    def join_geo_with(self, df: pd.DataFrame, kwargs: dict = {'how' : 'inner'}) -> None:
        # Join df to pandas dataframe
        self.geo = self.geo.join(df, **kwargs)
        
    def plot_original_data(self, year: str, areas: gpd.GeoDataFrame, 
                  plot_density: bool = False, fc: str = 'white',
                  area_fc: Union[str, list] = [.85, .85, .85],
                  ax: Union[matplotlib.axes._axes.Axes, str] = '') -> tuple[matplotlib.figure.Figure, 
                                                       matplotlib.axes._axes.Axes]:        
        if ax == '':
            # Create plot if no ax was inserted
            fig, ax = plt.subplots(facecolor=fc)
        areas.plot(ax=ax, facecolor=area_fc, linewidth=.3)
        df = self.geo.copy()
        df = df.join(self.DH[self.DH.Y == year].pivot_table(index='A'), how='inner')
        df = df.to_crs('EPSG:4328')
        if plot_density:
            df['Value'] = df['Value'] / df.area # Heat density (MWh/m^2)
            leg = 'MWh$\cdot$m$^{-2}$'
        else:
            df['Value'] = df['Value'] / 1e6 # TWh 
            leg = 'TWh'
        df = df.to_crs('EPSG:4326')
        df.plot(ax=ax, column ='Value', legend=True, cmap=cmap)
        ax.set_title('Original Data - %s'%leg)
        ax.set_ylabel('Latitude')
        ax.set_xlabel('Longitude')
        
        return fig, ax
    
    def plot_aggregated_data(self, year: str, areas: gpd.GeoDataFrame, 
                  plot_density: bool = False) -> tuple[matplotlib.figure.Figure, 
                                                       matplotlib.axes._axes.Axes]:
                      
        if hasattr(self, 'dfDH'):
            fig, ax = plt.subplots(facecolor=fc)
            df = areas.copy()
            df2 = self.dfDH.copy()
            df2.index = df2.index.str.replace('RESH . ', '').str.replace('_A', '')
            df = df.join(df2, how='inner')
            df = df.to_crs('EPSG:4328')
            if plot_density:
                df[year] = df[year] / df.area # Heat density (MWh/m^2)
                leg = 'MWh$\cdot$m$^{-2}$'
            else:
                df[year] = df[year] / 1e6 # TWh
                leg = 'TWh'
            df2 = areas.copy()
            df2[year] = df[year]
            df2.plot(ax=ax, column =year, legend=True, cmap=cmap)
            ax.set_title('Aggregated Data - %s'%leg)
            ax.set_ylabel('Latitude')
            ax.set_xlabel('Longitude')
            
            return fig, ax
        
        else:
            print('Aggregation have not been made.')    

def find_value(df: pd.DataFrame, element: any, 
                func: str = 'max', ind: int = 0) -> any:
    val_idx = eval("df[element].%s()"%func) == df[element]
    temp = df.index[val_idx]
    l = len(temp)
    if l > 1:
        print('%d %s values! Picked index %d'%(l, func, ind))
    return temp[ind]
    

#%% ------------------------------- ###
###     2. VPDK21 District Heat     ###
### ------------------------------- ###

class DistrictHeatAAU:
    def __init__(self) -> None:
        f1 = VPDK21()
        f2 = DKSTAT()
        self.f1 = f1
        self.f2 = f2

if __name__ == '__main__':
    X = DistrictHeatAAU()

    #%%
    data = DataContainer()
    data.muni = data.muni.merge(X.f1.DH)
    data.muni = data.muni.merge(X.f1.IND)
    data.muni = data.muni.merge(X.f2.IND)


    ## Get industry demands per municipality, per heat type 
    data.muni = data.muni.merge(xr.Dataset(
        {'energy_demand_mwh' : (('year', 'user', 'municipality'), 
                                np.expand_dims(
                                    np.vstack((
        data.muni.heat_demand_normalised.sel(year=2019, user='industry_phh') * data.muni.energy_demand_type_mwh.sel(year=2018, user='other') / data.muni.energy_demand_type_mwh.sel(year=2018).sum() * data.muni.energy_demand_mun_mwh.sel(year=2018),
        data.muni.heat_demand_normalised.sel(year=2019, user='industry_phm') * data.muni.energy_demand_type_mwh.sel(year=2018, user='other') / data.muni.energy_demand_type_mwh.sel(year=2018).sum() * data.muni.energy_demand_mun_mwh.sel(year=2018),
        data.muni.heat_demand_normalised.sel(year=2019, user='industry_phl') * data.muni.energy_demand_type_mwh.sel(year=2018, user='other') / data.muni.energy_demand_type_mwh.sel(year=2018).sum() * data.muni.energy_demand_mun_mwh.sel(year=2018),
        # data.energy_demand_type_mwh.sel(year=2018, user='district_heating') / data.energy_demand_type_mwh.sel(year=2018).sum() * data.energy_demand_mun_mwh.sel(year=2018),
        data.muni.energy_demand_type_mwh.sel(year=2018, user='electricity') / data.muni.energy_demand_type_mwh.sel(year=2018).sum() * data.muni.energy_demand_mun_mwh.sel(year=2018)
        )),
                                    axis=0)
                                )},
        coords={
            'year' : [2019],
            'user' : [
                    'industry_phh',
                    'industry_phm',
                    'industry_phl',
                    #   'district_heating',
                    'electricity'
                    ],
            'municipality' : data.muni.coords['municipality']
        }
    ))

    ## Drop year 2018, user electricity and other
    data.muni = data.muni.drop_vars(['energy_demand_mun_mwh',
                    'energy_demand_type_mwh',
                    'heat_demand_normalised'])
    data.muni = data.muni.sel(year=[2019], user=['district_heating', 'individual',
                                 'industry_phl', 'industry_phm', 'industry_phh'])

    temp = data.muni.heat_demand_mwh.sel(year=2019, user='district_heating').data
    temp += data.muni.heat_demand_mwh.sel(year=2019, user='individual').data
    temp += data.muni.energy_demand_mwh.sel(year=2019, user='industry_phl').data.astype(float)
    temp += data.muni.energy_demand_mwh.sel(year=2019, user='industry_phm').data.astype(float)
    temp += data.muni.energy_demand_mwh.sel(year=2019, user='industry_phh').data.astype(float)

    fig, ax = plt.subplots()
    data.get_polygons().plot(ax=ax,
                            column=temp,
                            legend=True)
