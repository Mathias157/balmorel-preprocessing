"""
Offshore Wind Definition

Loads profiles generated with "createVRE.py"

Created on 27.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import pandas as pd
from geofiles import prepared_geofiles
from pybalmorel import IncFile
from Submodules.municipal_template import DataContainer
import xarray as xr
import click
import geopandas as gpd
import matplotlib.pyplot as plt

#%% ------------------------------- ###
###        1. Offshore Wind         ###
### ------------------------------- ###

def load_profiles(choice: str = 'dkmunicipalities_names', nordsoeen_connection: str = 'Esbjerg', plot: bool = False):
    # Load files
    profiles = xr.load_dataset('Output/VRE/2012_offshore_wind.nc')
    ind, geo, c = prepared_geofiles(choice)
    offshore_geo = gpd.read_file('Data/Shapefiles/Offshore/OffshoreRegions.gpkg')
    
    # Change names
    offshore_geo['Name'] = offshore_geo.Name.replace('Nordsoeen', '%s_OFF5'%nordsoeen_connection)
    names = profiles.coords['Name'].data
    names[names == 'Nordsoeen'] = '%s_OFF5'%nordsoeen_connection
    profiles.coords['Name'] = names

    if plot:
        fig, ax = plt.subplots()
        geo.plot(ax=ax)
        offshore_geo.plot(ax=ax,color='r')
        plt.show()
    
    return profiles, geo, offshore_geo

def create_geo_sets(profiles: xr.Dataset):
    
    # Get names
    profiles = profiles.to_dataframe().reset_index()
    areas = pd.Series(profiles['Name'].unique())  

    # CCCRRRAAA and AAA
    f = IncFile(name='OFFSHORE_CCCRRRAAA', path='Output',
                prefix="SET CCCRRRAAA 'All geographical entities (CCC + RRR + AAA)'\n/\n",
                body="\n".join(areas),
                suffix='\n/;')
    f.save()
    f.name = 'OFFSHORE_AAA'
    f.prefix = "SET AAA 'Offshore areas'\n/\n"
    f.save()
    
    # RRRAAA
    f = IncFile(name='OFFSHORE_RRRAAA', path='Output',
                prefix="SET RRRAAA(RRR,AAA) 'Areas in regions'\n/\n",
                body="\n".join([area.split('_OFF')[0] + ' . ' + area for area in areas]),
                suffix='\n/;')
    f.save()
    
def create_profiles(profiles: xr.Dataset, year: int = 2012):
    
    # Get 00:00 first monday to 23:00 last sunday (hardcoded for 2012)
    profiles = profiles.to_dataframe().reset_index().pivot_table(index='time', columns='Name', values='specific generation')
    t0 = 24
    t1 = 24
    
    # To check
    # time = pd.Series(profiles.index).iloc[t0:-t1].dt.isocalendar()
    # print('\nCheck if first time is week 1, day 1, and last time is week 52, day 7\n', time)
    assert year == 2012, 'Change hardcoding to obtain correct 1st monday to last sunday in timeseries'
    
    # Select profile 
    profiles = profiles.iloc[t0:-t1] 
    
    S = ['S0%d'%i for i in range(1, 10)] + ['S%d'%i for i in range(10, 53)]
    T = ['T00%d'%i for i in range(1, 10)] + ['T0%d'%i for i in range(10, 100)] + ['T%d'%i for i in range(100, 169)]
    
    profiles.index = ['%s . %s'%(s, t) for s in S for t in T]
    
    # Make WND_VAR_T
    f = IncFile(name='OFFSHORE_WND_VAR_T', path='Output',
                prefix="TABLE WND_VAR_T1(SSS,TTT,AAA) 'Variation of the wind generation'\n",
                body=profiles,
                suffix="\n".join([
                    "",   
                    ";",                 
                    "WND_VAR_T(AAA,SSS,TTT)$WND_VAR_T1(SSS,TTT,AAA) = WND_VAR_T1(SSS,TTT,AAA);",
                    "WND_VAR_T1(SSS,TTT,AAA) = 0;"
                ]))
    profiles.columns.name = ''
    f.save()
    
    # Make WNDFLH
    f = IncFile(name='OFFSHORE_WNDFLH', path='Output',
                prefix="PARAMETER WNDFLH(AAA)  'Full load hours for wind power'\n/",
                suffix="\n/\n;")
    f.body = (
        profiles
        .sum()
        .div(profiles.max())
        .T
        .to_string()
    )
    f.save()
    
def create_investment_options(profiles: xr.Dataset):
    
    # AGKN
    areas = profiles.coords['Name'].data
    options = [
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2020",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2030",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2040",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2050"
    ]
    
    f = IncFile(name='OFFSHORE_AGKN', path='Output',
                prefix='', suffix='')
    f.body = "\n".join(["AGKN('%s','%s') = YES;"%(area, option) for area in areas for option in options])
    f.save()
    
def distribute_offshore_potential(total_potential: float, geofile: gpd.GeoDataFrame):
    
    # Calculate area as potential distribution
    temp = geofile.copy().to_crs('EPSG:4093') # To geocentric (meters)
    geofile['Values'] = temp.geometry.area / temp.geometry.area.sum() * total_potential
    geofile['TECH_GROUP'] = 'WINDTURBINE_OFFSHORE'
    geofile['SUBTECH_GROUP'] = 'RG1_OFF1'
    
    # SUBTECHGROUPKPOT
    f = IncFile(name='OFFSHORE_SUBTECHGROUPKPOT', path='Output',
                prefix="TABLE SUBTECHGROUPKPOT(CCCRRRAAA, TECH_GROUP, SUBTECH_GROUP)  'Subtechnology group capacity restriction by geography (MW)'\n",
                suffix='\n;')
    f.body = geofile.drop(columns='geometry')
    f.body_prepare(index=['Name', 'TECH_GROUP'], columns='SUBTECH_GROUP', values='Values')
    f.save()
    
#%% ------------------------------- ###
###            2. Main              ###
### ------------------------------- ###

@click.command()
@click.option('--weather-year', type=int, required=True, help='The weather year chosen for wind profiles')
@click.option('--total-offshore-wind-potential', type=int, required=True, help='The weather year chosen for wind profiles')
@click.option('--nordsoeen-connection', type=str, required=False, help="Connection point to Nordsøen. Esbjerg or Holstebro")
def main(weather_year: int, total_offshore_wind_potential: float, nordsoeen_connection: str = 'Esbjerg'):
    profiles, geo, offshore_geo = load_profiles(nordsoeen_connection=nordsoeen_connection, plot=False)
    create_geo_sets(profiles)
    create_profiles(profiles, weather_year)
    create_investment_options(profiles)
    distribute_offshore_potential(total_offshore_wind_potential, offshore_geo)

if __name__ == '__main__':
    main()
