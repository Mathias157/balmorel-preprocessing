#%%
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 25 13:33:33 2022

@author: Mathias Berg Rosendal, Research Assistant DTU Management

Reads the Danish Energy Agency's "Energiproducenttælling" (EPT, includes solar power) 
and windturbines datasheet.

It is converted and aggregated to a GKFX.inc file for Balmorel.

Download EPT and datasheet for windturbines here:
https://ens.dk/service/statistik-data-noegletal-og-kort/data-oversigt-over-energisektoren


Works with the environment.yaml distributed in XXX
"""

import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import MultiPolygon
from pyproj import Proj
import numpy as np
import matplotlib.pyplot as plt
from Modules.geofiles import prepared_geofiles

#%% ----------------------------- ###
###         0. ASSUMPTIONS        ###
### ----------------------------- ###

### Assumptions for DEA EPT data
### 0.1 Lifetimes in years
# Unique techs - COPY PASTED IN FROM DEA DATA
techs = np.array(['Kedel', 'Dampturbine', 'Nødstrømsanlæg', 'Solvarme', 'Elpatron',
       'Forbrændingsmotor', 'Varmepumpe Luft', 'Anden',
       'Varmepumpe Spildevand', 'Dampkedel', 'Varmepumpe',
       'Varmepumpe Overskudsvarme', 'Varmepumpe Anden', 'Kombianlæg',
       'Gasturbine', 'Bioforgasn. m. KE', 'Varmepumpe Kombi',
       'Bioforgasn. m. FM', 'Geotermi', 'Vandkraft', 'Stirlingmotor',
       'Varmepumpe Grundvand', 'Organic Rankine (ORC)', 'Landvindmølle',
       'Havvindmølle'])
T = {tech : 25 for tech in techs}
T['Dampturbine'] = 60
T['Gasturbine'] = 60
T['Organic Rankine (ORC)'] = 60
T['Vandkraft'] = 60
T['Kombianlæg'] = 60
T['Solvarme'] = 30


### 0.2 Assumed fuels in Balmorel
# Assuming: 
# Gasolie = Light oil
# Brændselsfrit = Heat (upon inspection it was 'other', geothermal and excess heat)
# Spildolie = Light oil
fuels = np.array(['Træpiller', 'Skovflis', 'Gasolie', 'Naturgas', 'Solenergi',
       'Elektricitet', 'Halm', 'Brændselsfrit', 'Affald', 'Fuelolie',
       'Træ- og biomasseaffald', 'Bio-olie', 'Biogas', 'Kul', 'Vandkraft',
       'Spildolie', 'Vindenergi'])
fuels_assumed = np.array(['WOODPEL', 'WOODCHI', 'LIGHTOIL', 'NGAS', 'SUN',
                            'ELEC', 'STRW', 'HEAT', 'MSW', 'FUELOIL',
                            'WOODWST', 'BIOIL', 'BGAS', 'COAL', 'WTR',
                            'LIGHTOIL', 'WIND'])
F = {fuels[i] : fuels_assumed[i] for i in range(len(fuels))}

### 0.3 Assumed techs in Balmorel
# Assuming:
# Anden = Gas turbine
# ORC = Engine
units = np.array(['Kedel', 'Dampturbine', 'Nødstrømsanlæg', 'Solvarme', 'Elpatron',
       'Forbrændingsmotor', 'Varmepumpe Luft', 'Anden',
       'Varmepumpe Spildevand', 'Dampkedel', 'Varmepumpe',
       'Varmepumpe Overskudsvarme', 'Varmepumpe Anden', 'Kombianlæg',
       'Gasturbine', 'Bioforgasn. m. KE', 'Varmepumpe Kombi',
       'Bioforgasn. m. FM', 'Geotermi', 'Vandkraft', 'Stirlingmotor',
       'Varmepumpe Grundvand', 'Organic Rankine (ORC)', 'Landvindmølle',
       'Havvindmølle'])
units_assumed = np.array(['BO', 'ST', 'GT', 'SH', 'GT',
                          'ENG', 'HP', 'GT', 
                          'HP', 'BO', 'HP',
                          'HP', 'HP', 'ST',
                          'GT', 'GT', 'HP',
                          'GT', 'GEO', 'ROR', 'ENG',
                          'HP', 'ENG', 'WT',
                          'WT'])
U = {units[i] : units_assumed[i] for i in range(len(units))}


### 0.4 Last year of GKFX
Ymax = 2050

### 0.5 Load geodata
# What areas to load?
choice = 'DK Municipalities'
# choice = 'NUTS3'
# choice = 'NUTS2'
# choice = 'Nordpool'



### OTHER ASSUMPTIONS IN PRE-PROCESSING ARE ALSO MADE IN OTHER SECTIONS
# Look for "- ASSUMPTIONS" locater
# Assumptions are made in the following sections:
# 2.3
# 2.4
# 2.6

#%% ----------------------------- ###
###         1. Read file          ###
### ----------------------------- ###

filename_EPT = './Data/Powerplants (Energistyrelsen)/ept2020_anlaeg_stamdata_m_hovedbraensel_og_braendselsfordeling_geoxy_0.xlsx'
filename_WT = './Data/Powerplants (Energistyrelsen)/anlaeg.xlsx'

## 1.1 Read EPT
f = pd.read_excel(filename_EPT)
# f = pd.read_excel(filename_EPT.replace('anlaeg', 'vaerk'))
fWT = pd.read_excel(filename_WT)
# Set data range
fWT = fWT.iloc[16:6313, :16]
# Set columns
fWT.columns = fWT.iloc[0, :]
fWT = fWT.iloc[1:,:]
fWT = fWT.dropna()
# Make new, clean dataframe
pp = f.loc[1:, :]
pp = pp.drop(columns=['year', 'company_ID', 'Plant_ID', 'Unit_ID',
                      'company name', 'plant name', 'address', 'zipcode',
                      'municipality_ID', 'district heating net_ID',
                      'district heating network name', 'unit name',
                      'Unnamed: 15', 'share -  coal', 'share -  oil',
                      'share -  natural gas', 'share -  waste', 'share -  biogas',
                      'share -  solid biomass', 'share -  bio oil',
                      'share -  no fuels', 'share -  solar ', 'share -  hydro',
                      'share -  electricity'])

## 1.2 Create shapefile
# Set projection of the meter-coordinates
UTM32 = Proj(proj='utm', zone=32, ellps='WGS84', preserve_units=False)
# Reverse to longitude, latitude coordinates
lon, lat = UTM32(f.loc[1:,['UTM X']].values, f.loc[1:,['UTM Y']].values, inverse=True)


pp.loc[:, ['Lon']] = lon[:,0]
pp.loc[:, ['Lat']] = lat[:,0]
pp = pp.drop(columns=['UTM X', 'UTM Y'])

## Get wind turbine coordinates
lon, lat = UTM32(fWT.loc[:, ['X (øst) koordinat \nUTM 32 Euref89']].values, fWT.loc[:,  ['Y (nord) koordinat \nUTM 32 Euref89']].values, inverse=True)
# Merge into pp
newWT = pd.DataFrame({'town' : fWT['Kommune'],
                      'type of plant' : 'Decentralt værk',
                      'unit type' : fWT['Type af placering'].str.replace('LAND', 'Landvindmølle').str.replace('HAV', 'Havvindmølle'),
                      'commissioning' : fWT['Dato for oprindelig nettilslutning'],
                      'decommissioning' : np.nan,
                      'electric caapcity_MW' : fWT['Kapacitet (kW)']/1000,
                      'heating capacity_MW' : 0,
                      'main fuel' : 'Vindenergi',
                      'main fuel type' : 'Vindenergi',
                      'Lon' : lon[:,0],
                      'Lat' : lat[:,0]})
pp = pd.concat((pp, newWT), ignore_index=True)
pp = gpd.GeoDataFrame(pp, geometry=gpd.points_from_xy(pp['Lon'], pp['Lat']))

## Readability
# Make columns more object oriented for readability
pp.columns = pp.columns.str.replace(' ', '_')
# Correct grammatical error
pp.columns = pp.columns.str.replace('electric_caapcity_MW', 'electric_capacity_MW')





### ----------------------------- ###
###        2. Preprocessing       ###
### ----------------------------- ###

### 2.1 Filtering
# Remove decommissioned powerplants
pp = pp[pp.decommissioning.isna()]

# Remove industry
pp = pp[pp.type_of_plant != 'Erhvervsværk']




### 2.2 Set commissioning year
# Get commissioning year
dt = pp.commissioning.astype('datetime64')
dt_int = np.zeros(len(dt))
# Round to nearest year
idx = dt.dt.month >= 6
dt_int[idx] = dt[idx].dt.year + 1
dt_int[~idx] = dt[~idx].dt.year
dt_int = dt_int.astype(int)
# Save
pp.commissioning = dt_int




### 2.3 Clean up fuel data - ASSUMPTIONS
# Assume nødstrømsanlæg run on light oil (most do, upon inspection)
idx = pp.main_fuel.isna() & (pp.unit_type == 'Nødstrømsanlæg')
pp.loc[idx, 'main_fuel'] = 'Gasolie'

# Assume boilers run on natural gas (hard assumption! A lot of unknown boilers)
idx = pp.main_fuel.isna() & (pp.unit_type == 'Kedel')
pp.loc[idx, 'main_fuel'] = 'Naturgas'

# Assume engines run on natural gas (most do upon inspection, but also biogas and gasolie)
idx = pp.main_fuel.isna() & (pp.unit_type == 'Forbrændingsmotor')
pp.loc[idx, 'main_fuel'] = 'Naturgas'

# Assume all heat pumps run on electricity (not true for gas-hybrid, but this require addon in Balmorel)
idx = pp.main_fuel.isna() & (pp.unit_type.str.find('Varmepumpe') != -1)
pp.loc[idx, 'main_fuel'] = 'Elektricitet'

# Solar heating runs on sun
idx = pp.main_fuel.isna() & (pp.unit_type == 'Solvarme')
pp.loc[idx, 'main_fuel'] = 'Solenergi'

# Geothermal runs on heat
idx = pp.main_fuel.isna() & (pp.unit_type == 'Geotermi')
pp.loc[idx, 'main_fuel'] = 'Brændselsfrit'

# Hydro runs on water
idx = pp.main_fuel.isna() & (pp.unit_type == 'Vandkraft')
pp.loc[idx, 'main_fuel'] = 'Vandkraft'

# Biogas on biogas
idx = pp.main_fuel.isna() & (pp.unit_type == 'Bioforgasn. m. KE')
pp.loc[idx, 'main_fuel'] = 'Biogas'

# The rest on natural gas
idx = pp.main_fuel.isna() 
pp.loc[idx, 'main_fuel'] = 'Naturgas'



### 2.4 Assume condenser, extraction, backpressure, wind or solar techs - ASSUMPTIONS
pp['producer_type'] = np.array(['None']*len(pp))

# Extraction
# According to Ea Energianalyse (link: https://www.ea-energianalyse.dk/da/publikationer/balmorel-user-guide/),
# backpressure CHP plants are usually characterised by being gas turbine, combustion- or stirling engines.
# This is therefore assumed in the following
CHPidx = (pp.electric_capacity_MW > 0) & (pp.heating_capacity_MW > 0)
EXTidx = (pp.unit_type == 'Gasturbine') | (pp.unit_type == 'Stirlingmotor') |\
                (pp.unit_type == 'Organic Rankine (ORC)') | (pp.unit_type == 'Forbrændingsmotor')
pp.loc[CHPidx & EXTidx, 'producer_type'] = 'EXT'

# Backpressure being the rest
pp.loc[CHPidx & ~EXTidx, 'producer_type'] = 'BP'

# Offshore wind
pp.loc[pp.unit_type == 'Havvindmølle', 'producer_type'] = 'OFF'

# Onshore wind
pp.loc[pp.unit_type == 'Landvindmølle', 'producer_type'] = 'ONS'

# Condensers are the remaining
pp.loc[(pp.producer_type == 'None') & (pp.heating_capacity_MW == 0), 'producer_type'] = 'CND'




### 2.5 Set decommissioning year and technology
pp['decommissioning'] = np.zeros(len(pp))
for tech in T.keys():
    idx = pp.unit_type == tech
    pp.loc[idx, 'decommissioning'] = pp.loc[idx, 'commissioning'] + T[tech]

pp.decommissioning = pp.decommissioning.astype(int)



### 2.6 Final filtering - ASSUMPTIONS
# Assume plants are decommissioned 2030 at the earliest
pp.loc[pp.loc[:, 'decommissioning'] < 2030, 'decommissioning'] = 2030


### 2.7 Make Prefix - ASSUMPTIONS
# All possibilities from Balmorel:
E = pd.Series(['GNR_BIOGASUPGRADING_E-99_Y-2020                 ' ,
    'GNR_BO_BGAS_E-100                               ' ,
    'GNR_BO_BGAS_E-90                                ' ,
    'GNR_BO_BGAS_E-91                                ' ,
    'GNR_BO_BGAS_E-92                                ' ,
    'GNR_BO_BGAS_E-95                                ' ,
    'GNR_BO_BGAS_E-99                                ' ,
    'GNR_BO_BIOIL_E-100                              ' ,
    'GNR_BO_BIOIL_E-102                              ' ,
    'GNR_BO_BIOIL_E-103                              ' ,
    'GNR_BO_BIOIL_E-113                              ' ,
    'GNR_BO_BIOIL_E-75                               ' ,
    'GNR_BO_BIOIL_E-79                               ' ,
    'GNR_BO_BIOIL_E-85                               ' ,
    'GNR_BO_BIOIL_E-86                               ' ,
    'GNR_BO_BIOIL_E-90                               ' ,
    'GNR_BO_BIOIL_E-91                               ' ,
    'GNR_BO_BIOIL_E-92                               ' ,
    'GNR_BO_BIOIL_E-93                               ' ,
    'GNR_BO_BIOIL_E-94                               ' ,
    'GNR_BO_BIOIL_E-97                               ' ,
    'GNR_BO_BIOIL_E-99                               ' ,
    'GNR_BO_COAL_E-80                                ' ,
    'GNR_BO_COAL_E-91                                ' ,
    'GNR_BO_ELEC_E-100                               ' ,
    'GNR_BO_ELEC_E-100_SS-3-KW-FEED                  ' ,
    'GNR_BO_ELEC_E-98                                ' ,
    'GNR_BO_ELEC_E-99                                ' ,
    'GNR_BO_FUELOIL_E-100                            ' ,
    'GNR_BO_FUELOIL_E-61                             ' ,
    'GNR_BO_FUELOIL_E-80                             ' ,
    'GNR_BO_FUELOIL_E-83                             ' ,
    'GNR_BO_FUELOIL_E-88                             ' ,
    'GNR_BO_FUELOIL_E-89                             ' ,
    'GNR_BO_FUELOIL_E-90                             ' ,
    'GNR_BO_FUELOIL_E-91                             ' ,
    'GNR_BO_FUELOIL_E-92                             ' ,
    'GNR_BO_FUELOIL_E-95                             ' ,
    'GNR_BO_FUELOIL_E-99                             ' ,
    'GNR_BO_LIGHTOIL_E-100                           ' ,
    'GNR_BO_LIGHTOIL_E-109                           ' ,
    'GNR_BO_LIGHTOIL_E-110                           ' ,
    'GNR_BO_LIGHTOIL_E-114                           ' ,
    'GNR_BO_LIGHTOIL_E-115                           ' ,
    'GNR_BO_LIGHTOIL_E-120                           ' ,
    'GNR_BO_LIGHTOIL_E-67                            ' ,
    'GNR_BO_LIGHTOIL_E-72                            ' ,
    'GNR_BO_LIGHTOIL_E-73                            ' ,
    'GNR_BO_LIGHTOIL_E-75                            ' ,
    'GNR_BO_LIGHTOIL_E-78                            ' ,
    'GNR_BO_LIGHTOIL_E-79                            ' ,
    'GNR_BO_LIGHTOIL_E-81                            ' ,
    'GNR_BO_LIGHTOIL_E-82                            ' ,
    'GNR_BO_LIGHTOIL_E-83                            ' ,
    'GNR_BO_LIGHTOIL_E-84                            ' ,
    'GNR_BO_LIGHTOIL_E-85                            ' ,
    'GNR_BO_LIGHTOIL_E-86                            ' ,
    'GNR_BO_LIGHTOIL_E-87                            ' ,
    'GNR_BO_LIGHTOIL_E-88                            ' ,
    'GNR_BO_LIGHTOIL_E-89                            ' ,
    'GNR_BO_LIGHTOIL_E-90                            ' ,
    'GNR_BO_LIGHTOIL_E-91                            ' ,
    'GNR_BO_LIGHTOIL_E-92                            ' ,
    'GNR_BO_LIGHTOIL_E-92_SS-15-KW                   ' ,
    'GNR_BO_LIGHTOIL_E-93                            ' ,
    'GNR_BO_LIGHTOIL_E-94                            ' ,
    'GNR_BO_LIGHTOIL_E-95                            ' ,
    'GNR_BO_LIGHTOIL_E-96                            ' ,
    'GNR_BO_LIGHTOIL_E-97                            ' ,
    'GNR_BO_LIGHTOIL_E-98                            ' ,
    'GNR_BO_MSW_E-100                                ' ,
    'GNR_BO_MSW_E-104                                ' ,
    'GNR_BO_MSW_E-105                                ' ,
    'GNR_BO_NGAS_E-100                               ' ,
    'GNR_BO_NGAS_E-101                               ' ,
    'GNR_BO_NGAS_E-102                               ' ,
    'GNR_BO_NGAS_E-103                               ' ,
    'GNR_BO_NGAS_E-104                               ' ,
    'GNR_BO_NGAS_E-105                               ' ,
    'GNR_BO_NGAS_E-85                                ' ,
    'GNR_BO_NGAS_E-95_SS-10-KW                       ' ,
    'GNR_BO_NGAS_E-97                                ' ,
    'GNR_BO_NGAS_E-98                                ' ,
    'GNR_BO_NGAS_E-99                                ' ,
    'GNR_BO_STRW_E-100                               ' ,
    'GNR_BO_STRW_E-102                               ' ,
    'GNR_BO_WOODCHI_E-100                            ' ,
    'GNR_BO_WOODCHI_E-105                            ' ,
    'GNR_BO_WOODCHI_E-106                            ' ,
    'GNR_BO_WOODCHI_E-107                            ' ,
    'GNR_BO_WOODCHI_E-108                            ' ,
    'GNR_BO_WOODCHI_E-110                            ' ,
    'GNR_BO_WOODCHI_E-111                            ' ,
    'GNR_BO_WOODCHI_E-112                            ' ,
    'GNR_BO_WOODCHI_E-113                            ' ,
    'GNR_BO_WOODCHI_E-114                            ' ,
    'GNR_BO_WOODCHI_E-117                            ' ,
    'GNR_BO_WOODCHI_E-118                            ' ,
    'GNR_BO_WOODCHI_E-119                            ' ,
    'GNR_BO_WOODCHI_E-120                            ' ,
    'GNR_BO_WOODPEL_E-100                            ' ,
    'GNR_BO_WOODPEL_E-102                            ' ,
    'GNR_BO_WOODPEL_E-75_SS-12-KW-FEED               ' ,
    'GNR_BO_WOODWST_E-100                            ' ,
    'GNR_BO_WOODWST_E-113                            ' ,
    'GNR_BO_WOODWST_E-82                             ' ,
    'GNR_BO_WOODWST_E-84                             ' ,
    'GNR_BO_WOODWST_E-86                             ' ,
    'GNR_BO_WOODWST_E-89                             ' ,
    'GNR_BO_WOODWST_E-90                             ' ,
    'GNR_BO_WOODWST_E-91                             ' ,
    'GNR_BO_WOODWST_E-94                             ' ,
    'GNR_EH_HEAT                                     ' ,
    'GNR_ENG_BGAS_BP_E-30                            ' ,
    'GNR_ENG_BGAS_BP_E-31                            ' ,
    'GNR_ENG_BGAS_BP_E-32                            ' ,
    'GNR_ENG_BGAS_BP_E-33                            ' ,
    'GNR_ENG_BGAS_BP_E-34                            ' ,
    'GNR_ENG_BGAS_BP_E-35                            ' ,
    'GNR_ENG_BGAS_BP_E-36                            ' ,
    'GNR_ENG_BGAS_BP_E-37                            ' ,
    'GNR_ENG_BGAS_BP_E-38                            ' ,
    'GNR_ENG_BGAS_BP_E-39                            ' ,
    'GNR_ENG_BGAS_BP_E-40                            ' ,
    'GNR_ENG_BGAS_BP_E-41                            ' ,
    'GNR_ENG_BGAS_BP_E-42                            ' ,
    'GNR_ENG_BGAS_BP_E-43                            ' ,
    'GNR_ENG_BGAS_CND_E-32                           ' ,
    'GNR_ENG_BGAS_CND_E-35                           ' ,
    'GNR_ENG_BGAS_CND_E-36                           ' ,
    'GNR_ENG_BGAS_CND_E-42                           ' ,
    'GNR_ENG_FUELOIL_CND_E-42                        ' ,
    'GNR_ENG_LIGHTOIL_BP_E-35                        ' ,
    'GNR_ENG_LIGHTOIL_BP_E-37                        ' ,
    'GNR_ENG_LIGHTOIL_BP_E-39                        ' ,
    'GNR_ENG_LIGHTOIL_BP_E-43                        ' ,
    'GNR_ENG_LIGHTOIL_CND_E-33                       ' ,
    'GNR_ENG_LIGHTOIL_CND_E-34                       ' ,
    'GNR_ENG_LIGHTOIL_CND_E-36                       ' ,
    'GNR_ENG_LIGHTOIL_CND_E-37                       ' ,
    'GNR_ENG_LIGHTOIL_CND_E-38                       ' ,
    'GNR_ENG_LIGHTOIL_CND_E-39                       ' ,
    'GNR_ENG_LIGHTOIL_CND_E-40                       ' ,
    'GNR_ENG_LIGHTOIL_CND_E-41                       ' ,
    'GNR_ENG_LIGHTOIL_CND_E-42                       ' ,
    'GNR_ENG_LIGHTOIL_CND_E-43                       ' ,
    'GNR_ENG_NGAS_BP_E-33                            ' ,
    'GNR_ENG_NGAS_BP_E-34                            ' ,
    'GNR_ENG_NGAS_BP_E-35                            ' ,
    'GNR_ENG_NGAS_BP_E-36                            ' ,
    'GNR_ENG_NGAS_BP_E-37                            ' ,
    'GNR_ENG_NGAS_BP_E-38                            ' ,
    'GNR_ENG_NGAS_BP_E-39                            ' ,
    'GNR_ENG_NGAS_BP_E-40                            ' ,
    'GNR_ENG_NGAS_BP_E-41                            ' ,
    'GNR_ENG_NGAS_BP_E-42                            ' ,
    'GNR_ENG_NGAS_BP_E-43                            ' ,
    'GNR_ENG_NGAS_BP_E-44                            ' ,
    'GNR_ENG_NGAS_BP_E-45                            ' ,
    'GNR_ENG_NGAS_BP_E-46                            ' ,
    'GNR_ENG_NGAS_BP_E-47                            ' ,
    'GNR_ENG_NGAS_CND_E-41                           ' ,
    'GNR_ENG_NGAS_CND_E-46                           ' ,
    'GNR_GEO_HEAT_HO                                 ' ,
    'GNR_GT_LIGHTOIL_CND_E-26                        ' ,
    'GNR_GT_LIGHTOIL_CND_E-27                        ' ,
    'GNR_GT_NGAS_BP_E-27                             ' ,
    'GNR_GT_NGAS_BP_E-28                             ' ,
    'GNR_GT_NGAS_BP_E-30                             ' ,
    'GNR_GT_NGAS_BP_E-31                             ' ,
    'GNR_GT_NGAS_BP_E-33                             ' ,
    'GNR_GT_NGAS_BP_E-36                             ' ,
    'GNR_GT_NGAS_BP_E-41                             ' ,
    'GNR_GT_NGAS_BP_E-42                             ' ,
    'GNR_GT_NGAS_BP_E-43                             ' ,
    'GNR_GT_NGAS_BP_E-44                             ' ,
    'GNR_GT_NGAS_BP_E-47                             ' ,
    'GNR_HP_ELEC_AIR-WTR_COP-325_SS-4-KW             ' ,
    'GNR_HP_ELEC_COP-300                             ' ,
    'GNR_HP_ELEC_COP-350                             ' ,
    'GNR_HP_ELEC_COP-400                             ' ,
    'GNR_HP_ELEC_COP-430                             ' ,
    'GNR_HP_ELEC_COP-450                             ' ,
    'GNR_HP_ELEC_COP-460                             ' ,
    'GNR_HP_ELEC_COP-470                             ' ,
    'GNR_HP_ELEC_COP-500                             ' ,
    'GNR_HP_ELEC_COP-530                             ' ,
    'GNR_HP_ELEC_COP-600                             ' ,
    'GNR_HS_HEAT_WTR-TANK_SS_E-95_Y-2010             ' ,
    'GNR_PV_SUN                                      ' ,
    'GNR_ROR_WTR                                     ' ,
    'GNR_SH_SUN                                      ' ,
    'GNR_ST_COAL_BP_E-35                             ' ,
    'GNR_ST_COAL_BP_E-38                             ' ,
    'GNR_ST_COAL_EXT_E-41                            ' ,
    'GNR_ST_COAL_EXT_E-42                            ' ,
    'GNR_ST_COAL_EXT_E-43                            ' ,
    'GNR_ST_COAL_EXT_E-47                            ' ,
    'GNR_ST_FUELOIL_BP_E-27                          ' ,
    'GNR_ST_FUELOIL_BP_E-34                          ' ,
    'GNR_ST_FUELOIL_CND_E-32                         ' ,
    'GNR_ST_LIGHTOIL_CND_E-33                        ' ,
    'GNR_ST_MSW_BP_E-16                              ' ,
    'GNR_ST_MSW_BP_E-17                              ' ,
    'GNR_ST_MSW_BP_E-18                              ' ,
    'GNR_ST_MSW_BP_E-19                              ' ,
    'GNR_ST_MSW_BP_E-20                              ' ,
    'GNR_ST_MSW_BP_E-21                              ' ,
    'GNR_ST_MSW_BP_E-22                              ' ,
    'GNR_ST_MSW_BP_E-23                              ' ,
    'GNR_ST_MSW_BP_E-25                              ' ,
    'GNR_ST_MSW_BP_E-26                              ' ,
    'GNR_ST_MSW_BP_E-27                              ' ,
    'GNR_ST_MSW_BP_E-28                              ' ,
    'GNR_ST_NGAS_BP_E-39                             ' ,
    'GNR_ST_NGAS_EXT_E-47                            ' ,
    'GNR_ST_STRW_BP_E-21                             ' ,
    'GNR_ST_STRW_BP_E-24                             ' ,
    'GNR_ST_STRW_BP_E-26                             ' ,
    'GNR_ST_STRW_BP_E-27                             ' ,
    'GNR_ST_STRW_BP_E-28                             ' ,
    'GNR_ST_WOODCHI_BP_E-15                          ' ,
    'GNR_ST_WOODCHI_BP_E-17                          ' ,
    'GNR_ST_WOODCHI_BP_E-23                          ' ,
    'GNR_ST_WOODCHI_BP_E-24                          ' ,
    'GNR_ST_WOODCHI_BP_E-27                          ' ,
    'GNR_ST_WOODCHI_BP_E-30                          ' ,
    'GNR_ST_WOODPEL_BP_E-18                          ' ,
    'GNR_ST_WOODPEL_BP_E-30                          ' ,
    'GNR_ST_WOODPEL_EXT_E-50                         ' ,
    'GNR_STEAM-REFORMING_E-70_Y-2020                 ' ,
    'GNR_WT_WIND_OFF                                 ' ,
    'GNR_WT_WIND_ONS_RG1                             ' ,
    'GNR_WT_WIND_ONS_RG2                             ' ,
    'GNR_WT_WIND_ONS_RG3                             ',
    'GNR_ENG_NGAS_EXT_E-43',  
    'GNR_ENG_NGAS_EXT_E-44',
    'GNR_ENG_BGAS_BP_CB-100       ' 
    'GNR_ENG_BGAS_BP_CB-100       ' ,
    'GNR_ENG_BGAS_BP_E-30         ' ,
    'GNR_ENG_BGAS_BP_E-31         ' ,
    'GNR_ENG_BGAS_BP_E-32         ' ,
    'GNR_ENG_BGAS_BP_E-33         ' ,
    'GNR_ENG_BGAS_BP_E-34         ' ,
    'GNR_ENG_BGAS_BP_E-35         ' ,
    'GNR_ENG_BGAS_BP_E-36         ' ,
    'GNR_ENG_BGAS_BP_E-37         ' ,
    'GNR_ENG_BGAS_BP_E-38         ' ,
    'GNR_ENG_BGAS_BP_E-39         ' ,
    'GNR_ENG_BGAS_BP_E-40         ' ,
    'GNR_ENG_BGAS_BP_E-41         ' ,
    'GNR_ENG_BGAS_BP_E-42         ' ,
    'GNR_ENG_BGAS_BP_E-43         ' ,
    'GNR_ENG_BGAS_BP_E-43_Y-2020  ' ,
    'GNR_ENG_BGAS_BP_E-45         ' ,
    'GNR_ENG_BGAS_BP_E-45_Y-2030  ' ,
    'GNR_ENG_BGAS_BP_E-46_Y-2040  ' ,
    'GNR_ENG_BGAS_BP_E-47_Y-2050  ' ,
    'GNR_ENG_BGAS_CND_E-32        ' ,
    'GNR_ENG_BGAS_CND_E-35        ' ,
    'GNR_ENG_BGAS_CND_E-36        ' ,
    'GNR_ENG_BGAS_CND_E-42        ' ,
    'GNR_ENG_BGAS_CND_E-43_Y-2020 ' ,
    'GNR_ENG_BGAS_CND_E-44        ' ,
    'GNR_ENG_BGAS_CND_E-45        ' ,
    'GNR_ENG_BGAS_CND_E-45_Y-2030 ' ,
    'GNR_ENG_BGAS_CND_E-46_Y-2040 ' ,
    'GNR_ENG_BGAS_CND_E-47_Y-2050 ' ,
    'GNR_ENG_BGAS_EXT_E-33        ' ]).str.replace(' ', '')

# # Create G
# for u in units:
#     for f in fuels:
#         idx = (pp.unit_type == u) & (pp.main_fuel == f)
#         pp.loc[idx, 'G'] = 'GNR' + '_' + U[u] + '_' + F[f] + '_' + pp.loc[idx, 'producer_type']  

# pp.loc[:, 'G'] = pp.loc[:, 'G'].str.rstrip('_None')

# # Allocate RANDOM technology in Balmorel!
# # THIS IS QUITE A HACK AND NOT VERY INTELLIGENT FOR DIFFERENT EFFICIENCIES
# # AND ONSHORE WIND REGIONS
# # (random suffix added)
# for e in E:
#     idx = pp.loc[:, 'G'].str.find(e[:e.rfind('_')]) != -1 
    
#     pp.loc[idx, 'G'] = e

### Create G #2 attempt
# Note that a random E is picked (the first one)
for u in units:
    for f in fuels:
        idxE = (E.str.find(U[u]) != -1) & (E.str.find(F[f]) != -1)
        idxP = (pp.unit_type == u) & (pp.main_fuel == f)
        
        # print(E)
        try:
            pp.loc[idxP, 'G'] = E[idxE].values[0] ### <- RANDOM assignment of the matching types!!!
        except IndexError:
            pass

### Missing power plants
print('Missing capacity:', round(pp[pp.G.isna()].electric_capacity_MW.sum()), 'MW')

# Typically too small to matter, so delete
pp = pp[~pp.G.isna()]

#%% ------------------------------- ###
### 3. Load Geodata and Pre-process ###
### ------------------------------- ###


the_index, areas, country_code = prepared_geofiles(choice)
areas.plot()

# ## 3.1 Choose geodata file
# # DKmunicipal 
# if choice == 'DK Municipalities':
# # Filter away unnescescary columns
# # areas = areas[['NAME_1', 'NAME_2', 'geometry']]
#     areas = gpd.read_file('Denmark/Adm/gadm36_DNK_2.shp')
#     # Aggregate hovedstaden - MODIFY TO USE NUTS3 AREAS FOR CAPITAL REGION
#     idx = (areas.NAME_1 == 'Hovedstaden') & (areas.NAME_2 != 'Bornholm') & (areas.NAME_2 != 'Christiansø')
#     hovedstaden = MultiPolygon(areas[idx].geometry.cascaded_union)
    
#     areas = areas.drop(index=list(areas.index[idx]))
#     areas = pd.concat((areas, gpd.GeoDataFrame({'NAME_1' : 'Hovedstaden', 
#                           'NAME_2' : 'København',
#                           'geometry' : [hovedstaden]})))
    
# # NUTS 
# # NUTS areas are useful for a high-res european model
# elif choice == 'NUTS3':
#     areas = gpd.read_file('NUTS_RG_01M_2021_4326.shp')
#     areas = areas[(areas.LEVL_CODE == 3) & (areas.NUTS_ID.str.find('DK') != -1)] # Only DK

# else:
#     print("You didn't choose any geodata! Check spelling")
    
    
    
    
# ### 3.2 Visualise current areas and power plants
# # Set projection
crs = ccrs.UTM(32)
# # Make compatible with geopandas
# # projection = crs.proj4_init # doesn't work, so actually cartopy is useless - continuing only with geopandas

# Make figure
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={"projection": crs},
                        dpi=200)


# Add areas
ax.add_geometries(areas.geometry, crs = crs,
                  facecolor=[.9, .9,.9], edgecolor='grey',
                  linewidth=.2)

# # Add power plants according to some type
# types = 'main_fuel'
# for typ in pp[types].unique():
#     idx = pp[types] == typ
#     ax.plot(pp.loc[idx, 'Lon'],pp.loc[idx, 'Lat'], 'o', markersize=.7, markeredgecolor='None')

# # Formatting the plot
# lines = ax.get_lines()
# new_ax = []
# for line in lines:
#     new = copy.copy(line)
#     new.set_markersize(4)
#     new_ax.append(new)
# ax.legend(new_ax, pp[types].unique())
# # ax.set_xlim(7.5,16)      
# # ax.set_ylim(54.4,58)  
# # fig.savefig('anlæg.pdf', bbox_inches='tight')



# ### Check what municipality the offshore wind turbine belongs to (DK Municipality assumption)
# # mun = pp.loc[pp.unit_type == 'Havvindmølle', 'town'].unique()
# # Is it in the shapefile used?
# # for m in mun:
# #     print(m in areas['NAME_2'].unique())


# ## Figure out where each powerplant is located (intersection with municipality)
# # How do i get from here though? 
# # a = MultiPoint(pp.geometry).intersection(areas.geometry[0])



#%% ------------------------------- ###
###          4. Aggregation         ###
### ------------------------------- ###

# NOTE: This might be an incredibly stupid way to go!
#       Try using spatial join (gpd.sjoin)
#       This could, e.g., create a new gpd, where areas (on the left) is joined with
#       powerplants if it's inside (using op='contains')
#       Or the other way around:
#       powerplants on the left are joined with an area (using op='within')
#       Use the 'inner' option for deleting powerplants/areas that did not contain/within
#       any of it's counterparts, or 'left' to keep those powerplants/areas with
#       NaN values, to not lose data

### 4.1 Assign areas
temp_pp = pp.copy()
for i,row in areas.iterrows():
    # Iterate through each polygon (could be multipolygon)
    # Assign polygon to powerplants
    idx = pp.geometry.intersects(row.geometry)
    
    # Assign area    
    pp.loc[idx, 'area'] = row[the_index]
        
# Assign the missing powerplants to nearest polygon (could be used for all, but this way is probably faster)
# Typically offshore plants
idx = pp['area'].isna()
for i,row in pp[idx].iterrows():
    
    # Calculate distances
    dist = {r[0] : r[1].geometry.distance(row.geometry) for r in areas.iterrows()}
    
    # Get index in areas
    ind = min(dist, key=dist.get)

    # Assign area
    pp.loc[i, 'area'] = areas.loc[ind, the_index]

# Plot to see if assignment was succesful
for a in pp.loc[:,'area'].unique():
    idx = pp.loc[:, 'area'] == a
    ax.plot(pp[idx].geometry.x,pp[idx].geometry.y, 'o', markersize=2)


#%% 4.2 Do aggregation
GKFX = pp.pivot_table(values='electric_capacity_MW', index=['area', 'G'], columns=['decommissioning'], aggfunc=np.sum)

## Cleaning up
# New index as combined columns
GKFX.index = ['_A . '.join(map(str,i)) for i in GKFX.index.tolist()]
GKFX[GKFX.isna()] = 0 # All years where no capacity is present
GKFX.columns.name = ''

# Make summation from last decommissioning year, to get GKFX
GKFX = GKFX.iloc[:,::-1].cumsum(axis=1) # Sums from last year to 2020
GKFX = GKFX.iloc[:,::-1] # Turn back around to 2020 -> 
     
# Have capacity from 2020 at least
Ymin = GKFX.columns.min()
if Ymin > 2020:
    for i in range(2020, Ymin):
        GKFX[i] = GKFX[Ymin]
    
# Sort columns for readability
GKFX = GKFX[GKFX.columns.sort_values()]

# Delete all years after Ymax
GKFX = GKFX[np.arange(GKFX.columns.min(), Ymax+1)]


#%% 4.3 Save as GKFX.inc
with open('./Output/GKFX.inc', 'w') as f:
    f.write("PARAMETER GKFX(YYY,AAA,GGG)        'Capacity of generation technologies';\n")
    f.write("TABLE GKFX1(AAA,GGG,YYY)           'Capacity of generation technologies' \n")
    dfAsString = GKFX.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n;')
    f.write('\nGKFX(YYY,AAA,GGG) = GKFX1(AAA,GGG,YYY);')
    f.write('\nGKFX1(AAA,GGG,YYY)=0;')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                                                                                                                                   
#%% Test cascaded_union
# Make figure
# fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={"projection": crs},
#                        dpi=200)

# # Add danish municipalities
# ax.add_geometries(areas.geometry, crs = crs,
#                   facecolor=[.9, .9,.9], edgecolor='grey',
#                   linewidth=.2)
# ax.plot(temp_pp['Lon'], temp_pp['Lat'], 'k+', markersize=3)

# dist = {r[0] : r[1].geometry.distance(areas.geometry.iloc[0]) for r in temp_pp.iterrows()}
