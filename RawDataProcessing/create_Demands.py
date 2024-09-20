#%%
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 17:17:25 2022

@author: Mathias Berg Rosendal, Research Assistant DTU Management

Use NUTS3 data for population density, which can be downloaded here:
https://ec.europa.eu/eurostat/web/products-datasets/product?code=demo_r_d3dens
    
And demand data from:


This is used to create demand files for Balmorel.


Works with the environment.yaml distributed in XXX
"""

import matplotlib.pyplot as plt
from matplotlib import rc
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import MultiPolygon
from pyproj import Proj
import numpy as np
import matplotlib.pyplot as plt
from Modules.geofiles import prepared_geofiles
from Modules.createDH import DistrictHeat
from pyproj import Proj
import datetime as dt
from pybalmorel.functions import IncFile


style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ----------------------------- ###
###         0. ASSUMPTIONS        ###
### ----------------------------- ###

### 0.1 Limit area
# If you type 'All', then no filter is applied
Afilt = 'All'


### 0.2 Population Year
Y = '2019'


### 0.3 Load geodata
# What areas to load?
choice = 'DK Municipalities'
# choice = 'NUTS1'
# choice = 'NUTS2'
# choice = 'NUTS3'
# choice = 'NordpoolReal'

### 0.4 Input parameters
DE = pd.DataFrame({'MWh' : 37000000}, index=['DK']) ### DUMMY DATA only for DK
DH = pd.DataFrame({'MWh' : 50000000}, index=['DK']) ### DUMMY DATA only for DK
Esector = 'RESE'
Hsector = 'RESH'
Dprof = pd.read_excel(r'.\Data\Timeseries\DummyProfiles.xlsx')
profYear = 2017 # Year for profiles

Dprof = pd.read_parquet('Data/Timeseries/DKMUNI36_DH.gzip')
### Assumptions
# 2.3 ToDo: Only one country at a time right now
# 2.3 ToDo: Should include yearly change
# 3.1 ToDo: Include different sectors
# 3.2 ToDo: Need to include data on profiles
#           Right now, DK1 large and DK el demand profiles are used for all


#%% ----------------------------- ###
###        1. Read files          ###
### ----------------------------- ###a

### 1.1 Read NUTS3 data
pop = pd.read_csv(r'.\Data\demo_r_d3dens.tsv', sep='\t')
N3 = gpd.read_file(r'.\Data\Shapefiles\NUTS_RG_01M_2021_4326\NUTS_RG_01M_2021_4326.shp')

## Make more readable
pop.columns = ['NUTS_ID'] + list(pd.Series(pop.columns).str.replace(' ',''))[1:]
pop['NUTS_ID'] = pop['NUTS_ID'].str.replace('PER_KM2,','')

## Apply filter
# Only NUTS3
pop = pop[pop.NUTS_ID.str.len() == 5]
N3 = N3[N3.NUTS_ID.str.len() == 5]
# Customised filters
if Afilt.lower() != 'all':
    N3 = N3[N3.NUTS_ID.str.find(Afilt) != -1]
    pop = pop[pop.NUTS_ID.str.find(Afilt) != -1]
# Year
pop = pop[['NUTS_ID', Y]]
# Convert to Numbers
pop[Y] = pop[Y].str.replace(':','0')
pop[Y] = pop[Y].astype(float)
   
## Merge
N3 = pd.concat((N3.set_index('NUTS_ID'), pop.set_index('NUTS_ID')), axis=1, join='inner')

## Change projections to a geocentric one
N3 = N3.to_crs(4328)

## Factor in area and normalise
N3[Y] = N3[Y]*N3.geometry.area
N3[Y] = N3[Y] / N3[Y].sum() ### HAS TO BE DONE PR COUNTRY

## Plot density heatmap
# fig, ax = newplot(fc=fc)
fig, ax = plt.subplots(facecolor=fc)
N3.plot(ax=ax, column=Y, cmap='coolwarm', legend=True, zorder=2)
ax.set_title('Fraction of population - ' + Y)


### 1.2 Read demand data
### DEMAND data should be on country scale, and used to iterate through in the next section

## Plot yearly demand


### 1.3 Read geodata
the_index, areas, country_code = prepared_geofiles(choice)
if 'nuts' in choice.lower():
    areas = areas[(areas[the_index].str.find('DK') != -1)]
areas.plot()
areas = areas[(areas[country_code] == 'DK') | (areas[country_code] == 'DE')] # Testing DK and DE

## Change projections to a geocentric one
if choice.lower().replace(' ', '') == 'nordpoolreal':
    areas.crs = 4326
areas = areas.to_crs(4328)




#%% ----------------------------- ###
###     2. Calculate Demands      ###
### ----------------------------- ###


### 2.2 Calculate intersecting area of areas with N3
### HAS TO BE NORMALISED PR COUNTRY !!!! Only works with one country at a time right now
### idea, use demand: for country in DE...
for i,row in areas.iterrows():
    # Intersecting Areas 
    w = N3.geometry.intersection(areas.geometry[i]).area
    # Normalise with N3 total area to get area fraction of country
    w = w / N3.area
    # Final weight is factoring population fraction on area fractions
    w = w * N3[Y]
    
    # Population Fraction X Intersecting Fractions
    areas.loc[i, 'DE'] = (w * DE.loc['DK', 'MWh']).sum() ### NEED key
    areas.loc[i, 'DH'] = (w * DH.loc['DK', 'MWh']).sum() ### NEED key for country

areas.plot(column='DE', cmap='coolwarm', legend=True, zorder=2)

### 2.3 Adjust to actual demands
print('DE input: %0.2f'%DE.loc['DK', 'MWh'], 'DE sum after intersect: %0.2f'%areas.DE.sum())
print('DH input: %0.2f'%DH.loc['DK', 'MWh'], 'DH sum after intersect: %0.2f'%areas.DH.sum())

# Linearly adjust all to fit actual input
areas.loc[:, 'DE'] = areas.loc[:, 'DE'] * DE.loc['DK', 'MWh'] / areas.DE.sum()
areas.loc[:, 'DH'] = areas.loc[:, 'DH'] * DH.loc['DK', 'MWh'] / areas.DH.sum()


### 2.3 MAKE CALCULATIONS ON YEARLY PROJECTION


#%% ----------------------------- ###
###           3. Save             ###
### ----------------------------- ###

inc = {} # Incfile container

### 3.1 Save DE and DH
DEtable = pd.DataFrame({'2050' : areas['DE'].values}, index=areas.index + ' . %s'%Esector)
DEtable.index.name = ''
DHtable = pd.DataFrame({'2050' : areas['DH'].values}, index='%s . '%Hsector + areas.index + '_A')
DHtable.index.name = ''

inc['DE'] = IncFile(name='DE', path='./Output',
                    prefix="TABLE DE1(RRR, DEUSER, YYY)        'Annual electricity consumption (MWh)'\n",
                    body=DEtable.to_string(header=True, index=True),
                    suffix="\n;\nDE(YYY,RRR,DEUSER) = DE1(RRR,DEUSER,YYY);\nDE1(RRR,DEUSER,YYY)=0;")

with open('./Output/DH.inc', 'w') as f:
    f.write("PARAMETER DH(YYY,AAA,DHUSER)  'Annual brutto heat consumption';\n")
    f.write("TABLE DH1(DHUSER, AAA, YYY)\n")
    dfAsString = DHtable.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n;')
    f.write("\nDH(YYY,AAA,DHUSER) = DH1(DHUSER, AAA, YYY);\nDH1(DHUSER, AAA, YYY)=0;")


### 3.2 Save DE and DH profiles - HACK

#%% Convert data
# Get correct timeseries index for Balmorel
t = Dprof['Time'].dt.isocalendar()
t.index = Dprof['Time']
t['hour'] = t.index.hour

# Filter away first week, from last year 
idx = t.index.year == t['year'] 
idx = idx & (t.index.year == profYear)
t = t[idx]
DT = Dprof[idx]

# Fix summer-period switch
t.index = np.array([t.index[0]+dt.timedelta(hours=i) for i in range(8736)])
t = t.index.isocalendar()

# Make seasons
t['S'] = t['week'].astype(str)
idx = t['S'].str.len() == 1
t.loc[idx, 'S'] = '0' + t.loc[idx, 'S']
t['S'] = 'S' + t['S']

# Make terms
try:
    t['T'] = np.array([i for i in range(1, 169)]*52)
except ValueError:
    print("\nWARNING!\nYou didn't load 8736 hours of data! Select a bit of the next year, in cutout (T parameter in beginning).")
    print("The current profile will be %d too short (%d hours in total)\n"%(8736-len(t), len(t)))
    
    array = np.array([i for i in range(1, 169)]*52)
    t['T'] = array[:len(t)]

    
t['T'] = t['T'].astype(str)
idx = t['T'].str.len() == 1
t.loc[idx, 'T'] = '00' + t.loc[idx, 'T']
idx = t['T'].str.len() == 2
t.loc[idx, 'T'] = '0' + t.loc[idx, 'T']
t['T'] = 'T' + t['T']


# Create new index - ASSUMING DK1 LARGE HEAT and DK EL PROFILE
DT.index = t['S'] + ' . ' + t['T']

DET = pd.DataFrame(data={A : DT['El demand'] for A in areas.index}, index=DT.index)
DHT = pd.DataFrame(data={A : DT['DK1_Large'] for A in areas.index}, index=DT.index)
DHT.columns = DHT.columns + '_A'

#%%
with open('./Output/DE_VAR_T.inc', 'w') as f:
    f.write("PARAMETER DE_VAR_T(RRR,DEUSER,SSS,TTT) 'Variation in electricity demand';\n")
    f.write("TABLE DE_VAR_T1(SSS,TTT,RRR)\n")
    dftostring = DET.to_string(header=True, index=True)
    f.write(dftostring)
    f.write("\n;\n")
    f.write("DE_VAR_T(RRR,'RESE',SSS,TTT) = DE_VAR_T1(SSS,TTT,RRR);\n")
    f.write("DE_VAR_T1(SSS,TTT,RRR)=0;\n")

with open('./Output/DH_VAR_T.inc', 'w') as f:
    f.write("PARAMETER DH_VAR_T(AAA,DHUSER,SSS,TTT) 'Variation in heat demand';\n")
    f.write("TABLE DH_VAR_T1(SSS,TTT,AAA)\n")
    dftostring = DHT.to_string(header=True, index=True)
    f.write(dftostring)
    f.write("\n;\n")    
    f.write("DH_VAR_T(AAA,'RESH',SSS,TTT) = DH_VAR_T1(SSS,TTT,AAA);\n")
    f.write("DH_VAR_T1(SSS,TTT,AAA)=0;\n")
