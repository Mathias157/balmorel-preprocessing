"""
Created on 11.03.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd

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

class DistrictHeat:
    """Class for district heating data
    
    Existing datasets:
        - Denmark

    Args:
        dataset (str, optional): _description_. Defaults to 'DK'.
    """
    
    def __init__(self, dataset: str = 'Denmark') -> None:
        if dataset.lower() == 'denmark': 
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
            for element in ['DK_SA_E_BG',
                            'DK_SA_E_NG_CHP',
                            'DK_SA_E_NG_HO',
                            'DK_SA_E_ST_CHP',
                            'DK_SA_E_ST_HO',
                            'DK_SA_E_WO_HO']:
                if i == 0:
                    temp = self.geo.loc[element].copy()
                    temp.crs = 'EPSG:4326'
                else:
                    temp.geometry = temp.geometry.union(self.geo.loc[element].geometry) 
                self.geo = self.geo.drop(index=element)
                i += 1 
            self.geo.loc['DK_E_Rural'] = temp
            i = 0
            for element in ['DK_SA_W_BG',
                            'DK_SA_W_EB',
                            'DK_SA_W_NG_CHP',
                            'DK_SA_W_NG_HO',
                            'DK_SA_W_ST_HO',
                            'DK_SA_W_WO_CHP',
                            'DK_SA_W_WO_HO']:
                if i == 0:
                    temp = self.geo.loc[element].copy()
                else:
                    temp.geometry = temp.geometry.union(self.geo.loc[element].geometry) 
                self.geo = self.geo.drop(index=element)
                i += 1 
            self.geo.loc['DK_W_Rural'] = temp
            self.geo.crs = 'EPSG:4326'
        else:
            print("Dataset doesn't exist - this is an empty object\n")
            print("Available datasets:\n- Denmark (default)")

    def find_intersects(self, areas: gpd.GeoDataFrame, sum_total: bool = False) -> pd.DataFrame:        
        # Convert to geocentric projection
        temp_areas = areas.to_crs(4328) # To geocentric (meters)
        temp_DH = self.geo.to_crs(4328) # To geocentric (meters)

        # Find intersection of DH shapes to each element in areas
        df_intercepts = pd.DataFrame()
        for element in temp_areas.index:
            df_intercepts[element] = temp_DH.geometry.intersection(temp_areas.geometry[element]).area
        
        if sum_total:
            # Divide by total area:
            df_intercepts = df_intercepts.div(temp_DH.area, axis=0)
            
        else:
            # Divide by sum of intersected areas
            df_intercepts = df_intercepts.div(df_intercepts.sum(axis=1), axis=0)
        
        return df_intercepts

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
        
        for element in areas.index:
            for year in temp.columns.get_level_values(1):
                df_DH.loc[element, year] = (temp.loc[:,eval(col_ind)] * df_intercepts[element]).sum()

        self.dfDH = df_DH


    def assign_DH_profile():
        ...
    
    def join_geo_with(self, df: pd.DataFrame, kwargs: dict = {'how' : 'inner'}) -> None:
        # Join df to pandas dataframe
        self.geo = self.geo.join(df, **kwargs)
        
    def plot_original_data(self, year: str, areas: gpd.GeoDataFrame, 
                  plot_density: bool = False) -> tuple[matplotlib.figure.Figure, 
                                                       matplotlib.axes._axes.Axes]:        
        fig, ax = plt.subplots(facecolor=fc)
        areas.plot(ax=ax, facecolor=[.8, .8, .8], edgecolor=[0,0,0], linewidth=.3)
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
        df.plot(ax=ax, column ='Value', legend=True, cmap='viridis')
        ax.set_title('Original Data - %s'%leg)
        
        return fig, ax
    
    def plot_aggregated_data(self, year: str, areas: gpd.GeoDataFrame, 
                  plot_density: bool = False) -> tuple[matplotlib.figure.Figure, 
                                                       matplotlib.axes._axes.Axes]:
                      
        if hasattr(self, 'dfDH'):
            fig, ax = plt.subplots(facecolor=fc)
            df = areas.copy()
            df = df.join(DH.dfDH, how='inner')
            df = df.to_crs('EPSG:4328')
            if plot_density:
                df[year] = df[year] / df.area # Heat density (MWh/m^2)
                leg = 'MWh$\cdot$m$^{-2}$'
            else:
                df[year] = df[year] / 1e6 # TWh
                leg = 'TWh'
            df2 = areas.copy()
            df2[year] = df[year]
            df2.plot(ax=ax, column =year, legend=True, cmap='viridis')
            ax.set_title('%s Aggregation - %s'%(choice, leg))
            
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
        
#%% Example

if __name__ == '__main__':
    choice = 'DKMunicipalities'
    # the_index, areas, c = prepared_geofiles(choice)


    DKareas = areas[areas[the_index].str.find('DK') != -1]
    DH = DistrictHeat('Denmark')
    DH.dfint = DH.find_intersects(DKareas) # Find intersects between district heat areas and chosen areas
    DH.assign_DH(DKareas, DH.dfint)

    # Check that the aggregation got all data:
    # Annual DH
    print('\nOriginal data, annual DH:')
    print(DH.DH[DH.DH.A.str.find('DK') != -1].pivot_table(index='A', columns='Y').sum() / 1e6)
    print('\nNew data, annual DH:')
    print(DH.dfDH.sum() / 1e6)


    ## Plot aggregated data
    year = '2050'

    DH.plot_original_data(year, DKareas, True)

    DH.plot_aggregated_data(year, DKareas)