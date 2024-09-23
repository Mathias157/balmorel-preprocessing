"""
Generate heat profiles from futuregas data

Assumes that the distribution of heat profiles that i made using FutureGas data is in the Balmorel/muni/data folder

Created on 10.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

from pybalmorel import Balmorel
from pybalmorel.utils import symbol_to_df
from Modules.geofiles import prepared_geofiles
from Modules.Submodules.municipal_template import DataContainer
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#%% ------------------------------- ###
###        1. Read .inc Files       ###
### ------------------------------- ###

m = Balmorel(r'C:\Users\mberos\gitRepos\Balmorel')
m.load_incfiles('muni')

#%% Get profiles
profiles = symbol_to_df(m.input_data['muni'], 'DH_VAR_T', ['A', 'DHUSER', 'S', 'T', 'Value'])

# Remove the _A suffix
profiles.A = profiles.A.str.replace('_A', '')

profiles = profiles.pivot_table(index=['A', 'DHUSER', 'S', 'T'])

#%% Get municipality geofile
index, areas, c = prepared_geofiles('dkmunicipalities')
correct_names = {'Århus' : 'Aarhus',
                'Høje Taastrup' : 'Høje-Taastrup',
                'Vesthimmerland' : 'Vesthimmerlands'}
areas['NAME_2'] = areas['NAME_2'].replace(correct_names)

#%% Get only residential heat profiles
DK_profiles = (
    profiles[
        (
            profiles
            .index
            .get_level_values(0)
            .str
            .find('DK_') != -1
        )
        & 
        (
            profiles
            .index
            .get_level_values(0)
            .str
            .find('_IND') == -1
        )
    ]
)

# Fix missing data for Herlev DK_1_19_1 (not for DK_1_6_1 Christiansø) 
areas2 = areas.query("NAME_2 != 'Herlev' and NAME_2 != 'Christiansø'")
converter = dict(areas2.NAME_2)

# Convert to municipality names
DK_profiles = DK_profiles.reset_index()
DK_profiles['A'] = DK_profiles['A'].replace(converter)
       
# Add assumption on Herlev data being equal to Ballerup
temp = DK_profiles.query('A == "Ballerup"')
temp.A = 'Herlev'
DK_profiles = pd.concat((
    DK_profiles,
    temp
))
       
# Convert to correct column names
DK_profiles.columns = ['municipality', 'user', 'week', 'hour', 'heat_demand_profile']

# Convert to correct coordinate names
DK_profiles['week'] = (
    DK_profiles['week']
    .str.replace('S0', '')
    .str.replace('S', '')
    .astype(int)
)
DK_profiles['hour'] = (
    DK_profiles['hour']
    .str.replace('T00', '')
    .str.replace('T0', '')
    .str.replace('T', '')
    .astype(int)
)

# Pivot and convert to xarray
DK_profiles = DK_profiles.pivot_table(index=['municipality', 'user', 'week', 'hour'],
                                      values='heat_demand_profile').to_xarray()

#%% Save
DK_profiles.to_netcdf('Data/Timeseries/DK_heat_profile_futuregas.nc')

#%% Combine with polygon data
X = DataContainer()
X.muni = X.muni.merge(DK_profiles)

#%% Get maximum values 
max_vals = X.muni.heat_demand_profile.max(('week', 'hour', 'user'))

#%% Plot the timevariation
for i in range(1):
    for j in range(24):
        fig, ax = plt.subplots()
        X.get_polygons().plot(
            ax=ax,
            column=(
                X
                .muni
                .heat_demand_profile
                .sel(user='RESH')
                .isel(week=i, hour=j)
                .data
            )/max_vals.data,
            legend=True,
            vmin=0,
            vmax=1
        )
        ax.axes.axis('off')
        # fig.savefig()
        # plt.close(fig)
# Make gif = C:\Users\mberos\Danmarks Tekniske Universitet\PhD in Transmission and Sector Coupling - Dokumenter\Documents\Social\Friday Bar\createGIF.py
