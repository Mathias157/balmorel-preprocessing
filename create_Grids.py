# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 22:51:15 2022

@author: Mathias Berg Rosendal, PhD, DTU Management

Use electricity transmission cost data from DEA2021:
https://ens.dk/en/our-services/projections-and-models/technology-data/technology-catalogue-transport-energy
A map of the extisting transmission grids:
https://energinet.dk/media/gqjj2xpk/eksisterende-net-2021.pdf <- DK

This is used to create demand files for Balmorel.

Assumption of how much a certain kV of transmission line can transmit of power
comes from: https://wise-answer.com/how-much-power-can-a-transmission-line-carry/
765 kV => 2200-2400 MW
500 kV => 900 MW
345 kV => 400 MW
*300 kV => 300 MW
*132 kV => 100 MW
*220 kV => 200 MW
GET A BETTER SOURCE!!! Look in power grid course material?
* = derived from three data assumptions (2nd degree assumption)


Power grid is manually drawed from: https://energinet.dk/media/ouufo5ll/eksisterende-net-2021.jpeg
NEED automatic source! (ENTSO-E data)

Works with the environment.yaml distributed in XXX
"""

import matplotlib.pyplot as plt
from matplotlib import rc
from formplot import *
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import MultiPolygon, Point, LineString
import shapely
from pyproj import Proj
import numpy as np
import matplotlib.pyplot as plt
from functions import PreProcessShapes
from pyproj import Proj

        
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

# 0.1 Choice of spatial aggregation
# choice = 'DK municipalities'
# choice = 'NUTS3'
# choice = 'NUTS2'
choice = 'NordpoolReal'

# 0.2 Parameters
growth = 10 # Maximum growth of areas with no grid connection in km
growth_step = 1 # Step towards maximum growth in km
# Electricity transmission
# From DEA 2021, 111 'Main electricity distribution grid' (no data for transmission? these costs are for 50/60 kV)
XE_cost = 3.1 # €/MW/m high bound
# XE_cost = 2.511 # €/MW/m low bound
# XE_cost = 2.175 # €/MW/m actual transmission data: Maxwell Brown, Wesley Cole, Kelly Eurek, Jonathon Becker, David Bielen, Ilya Chernyakhovskiy, Stuart Cohen, Allister Frazier, Pieter Gagnon, Nathaniel Gates, et al. Regional energy deployment system (reeds) model documentation: Version 2019. Technical report, National Renewable Energy Lab.(NREL), Golden, CO (United States), 2020.
XE_substation_cost = 76000 # €/MW very high bound
# XE_substation_cost = 4476 # €/MW low bound
# XE_substation_cost = 0 # No cost
XE_FOM = 21.7/1e3 # €/MW/m/year
Xsub = 99 # Amount of substations (assumed similar to today ~ one pr. municipality)
XT = 40 # Lifetime of electricity grid elements

XLOSS_E = 3.318383e-08 # fraction of loss pr. m, From Balmorel DK1-DK2 line
XCOST_E = 0.0001 # €/MWh Transmission costs
DLOSS_E = 0.05 # Electricity distribution loss
DCOST_E = 5 # €/MWh Electricity distribution cost 

### See more assumptions in sections
# 2.2 - Manual adjustments to links between regions
# 2.5 - Automatic XKFX through power line input data does not work for regions that do not touch! (e.g. across sea)
# 4.1 - Assumed symmetrical lines
# 4.3 - Assuming same distribution loss in all regions!!!

#%% ----------------------------- ###
###        1. Read files          ###
### ----------------------------- ###

### 1.1 Load geodata
the_index, areas = PreProcessShapes(choice)

if 'nuts' in choice.lower():
    areas = areas[areas.CNTR_CODE == 'DK']
elif 'nordpool' == choice.lower():
    # idx = ((areas.index.str.find('DK') != -1) | (areas.index.str.find('SE') != -1) | (areas.index.str.find('NO') != -1)) & (areas.index.str.find('IT') == -1)
    idx = (areas.index.str.find('DK') != -1) 
    areas = areas[idx]
elif 'nordpoolreal' == choice.lower():
    areas = areas[areas.RRR != 'RU']
    
### 1.2 Load power grid data
PL = pd.read_csv("Data/Power Grid/entsoe/links.csv", quotechar="'")
PL.geometry = PL.geometry.apply(lambda x: shapely.wkt.loads(x))
PL = gpd.GeoDataFrame(PL)

# Filter no voltage away
idx = PL.voltage.isna()
PL = PL[~idx]

# Plot
fig, ax = plt.subplots(1)
areas.plot(ax=ax)
PL.plot(ax=ax, color='k')
# plt.xlim([7, 16])
# plt.ylim([54, 59])
plt.xlim([7, 16])
plt.ylim([54, 59])

### 1.3 Assume capacities 
kVtoMW = {132 : 100, 220 : 200,
          300 : 300, 380 : 400,
          500 : 900, 750 : 2200}


# Assert capacities
for kV in kVtoMW:
    idx = PL.voltage == kV
    PL.loc[idx, 'Cap (MW)'] = kVtoMW[kV]


#%% ----------------------------- ###
###        2. Create XKFX         ###
### ----------------------------- ###

    
### 2.1 Create matrix for possible grid connections
X = pd.DataFrame(np.zeros((len(areas), len(areas))).astype(int),
                 index=areas.loc[:, the_index],
                 columns=areas.loc[:, the_index])
X.index.name = 'IRRRE'
X.columns.name = 'IRRRI'

### 2.1 Find Neighbours
# Use touches or intersects for areas not separated
for i,a in areas.iterrows():
    
    # Index for touching regions
    idx = areas.touches(a.geometry)
    
    # Assign possible links
    X.loc[a[the_index], areas.loc[idx, the_index]] = 1

# MAYBE ADD THAT IF NO ONE IS TOUCHING, THE CLOSEST ONES SHOULD BE CONNECTED?
# Could solve over-seas-interconnector issue    
# However, won't solve if several regions on each side of ocean!

### 2.2 Manual Adjustments - ASSUMPTIONS
# Find those with no grids
no_grids = list(X.columns[~X.any()])

# Semi-manual expansion 
# for a in no_grids:
#     A = areas.loc[areas.loc[:,the_index] == a, :]
#     for step in np.arange(0, growth, growth_step):
#         temp = areas[areas.overlaps(A.geometry.buffer(step*1e4))]
#         if not(len(temp) == 0):
#             temp.plot()
#             print(temp)

## Manual
if choice.lower().replace(' ', '') == 'dkmunicipalities':
    # Skærbæk-Fyn
    X.loc['DK_5_8_1', 'DK_5_13_1'] = 1
    # Nyborg-Sjælland
    X.loc['DK_4_13_1', 'DK_5_15_1'] = 1
    # Guldborgsund-Vordingborg
    X.loc['DK_4_3_1', 'DK_4_17_1'] = 1
    # Vordingborg-Næstved
    X.loc['DK_4_9_1', 'DK_4_17_1'] = 1
    # Lolland-Langeland
    X.loc['DK_4_8_1', 'DK_5_12_1'] = 1
    # Langeland-Svendborg
    X.loc['DK_5_12_1', 'DK_5_18_1'] = 1
    # Sønderborg-Faaborg-Midtfyn
    X.loc['DK_5_6_1', 'DK_5_17_1'] = 1
    # Samsø-Kalundborg
    X.loc['DK_2_13_1', 'DK_4_5_1'] = 1
    # Samsø-Midtjylland
    X.loc['DK_2_10_1', 'DK_2_13_1'] = 1
    # Frederikshavn-Læsø
    X.loc['DK_3_3_1', 'DK_3_6_1'] = 1
    # Haderslev-Assens
    X.loc['DK_5_3_1', 'DK_5_9_1'] = 1
    # Skive-Morsø
    X.loc['DK_2_16_1', 'DK_3_8_1'] = 1
    # Morsø-Thisted
    X.loc['DK_3_8_1', 'DK_3_10_1'] = 1
    # Morsø-Vesthimmerland
    X.loc['DK_2_16_1', 'DK_3_11_1'] = 1
    
    
elif choice.lower() == 'nuts3':
    # Fyn
    X.iloc[2, 7] = 1
    X.iloc[2, 8] = 1
    X.iloc[2, 9] = 1   
    
    # Bornholm
    # X.iloc[4, 8] = 1
elif choice.lower() == 'nuts2':
    X.iloc[0, 3] = 1
elif choice.lower() == 'nordpool':
    X.iloc[0, 1] = 1

# Symmetry
for i,row in X.iterrows():
    X.loc[:,i] = X.loc[i, :]

### 2.3 Plot for inspection
fig, ax = newplot(fc=fc)
areas.plot(ax=ax, zorder=2, edgecolor='k')

line_center_x = []
line_center_y = []
for a in X.index:
    idx = X[a] == 1
    # temp = 
    # print(areas.set_index(the_index)[idx].plot())
    A = areas.loc[areas.loc[:,the_index] == a, :]
    
    # Plot centroid lines
    for i,l in areas[idx].iterrows():
        
        p, = ax.plot([A.geometry.centroid.x, l.geometry.centroid.x],
                [A.geometry.centroid.y, l.geometry.centroid.y], 'r-')

#%%

### 2.4 Create XKFX
XKFX = X.copy()*0

### 2.5 Find intersects between power grid data and polygons
for i,line in PL.iloc[:].iterrows():
    
    # Intersects between areas and line i    
    idx = areas.geometry.intersects(line.geometry)
    
    # Make overlay - how to make XKFX between disconnected polygons..?
    # OV = gpd.GeoDataFrame({'geometry' : areas[idx].geometry.union(line.geometry)})
    
    # Find touching regions within line intersects
    for j,poly in areas[idx].iterrows():
        idx2 = areas[idx].touches(areas[idx].geometry[j])
        As = areas[idx][idx2].loc[:,the_index] # The names of the areas touching area j (poly)
        XKFX.loc[poly[the_index],As] = XKFX.loc[poly[the_index],As] + line['Cap (MW)']
    # for j,poly in OV.iterrows():
    #     idx2 = OV.touches(OV[idx].geometry[j])
    #     As = OV[idx2].loc[:,the_index] # The names of the areas touching area j (poly)
    #     XKFX.loc[poly.name,As] = XKFX.loc[poly.name,As] + line['Cap (MW)']


### 2.6 Save XKFX
XKFX.columns.name = ''
XKFX.index.name = ''
XKFX.index = '2016 . ' + XKFX.index 
XKFX = XKFX.astype(str).replace('0', '')
with open('./Output/XKFX.inc', 'w') as f:
    f.write("TABLE XKFX(YYY,IRRRE,IRRRI)  'Initial transmission capacity between regions'\n")
    dfAsString = XKFX.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n;\n')
    f.write("XKFX(YYY,IRRRE,IRRRI)$(YYY.VAL GT 2016) = XKFX('2016',IRRRE,IRRRI);")

"""
What's missing in the municipality model, due to lacking method of connecting overseas regions:

* Storebælt
XKFX(YYY,'DK_4_13_1','DK_5_15_1') = 600;
XKFX(YYY,'DK_5_15_1', 'DK_4_13_1') = 590;  

* Frederikshavn-Læsø
XKFX(YYY,'DK_3_6_1','DK_3_3_1') = 740;
XKFX(YYY,'DK_3_3_1', 'DK_3_6_1') = 740; 

* Fredericia-Middelfart
XKFX(YYY,'DK_5_8_1','DK_5_13_1') = 1200;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             
XKFX(YYY,'DK_5_13_1','DK_5_8_1') = 1200;


* Slagelse-Lolland
XKFX(YYY,'DK_4_13_1','DK_4_8_1') = 400;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
XKFX(YYY,'DK_4_8_1','DK_4_13_1') = 400;


* Guldborgssund-Vordingborg
XKFX(YYY,'DK_4_3_1','DK_4_17_1') = 400;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
XKFX(YYY,'DK_4_17_1','DK_4_3_1') = 400;
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
                                             
* Morsø-Skive
XKFX(YYY,'DK_3_8_1','DK_2_16_1') = 200;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
XKFX(YYY,'DK_2_16_1','DK_3_8_1') = 200;


* Morsø-Thisted
XKFX(YYY,'DK_3_8_1','DK_3_10_1') = 200;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
XKFX(YYY,'DK_3_10_1','DK_3_8_1') = 200;
                                           
"""

#%% ----------------------------- ###
###    3. Calculate Distances     ###
### ----------------------------- ###

# Convert to geocentric coordinates for meter units
areas = areas.to_crs(4328)


### 3.1 Calculate Distances
d = X.copy()
for a in X.index:
    # Index for connecting areas
    idx = X[a] == 1
    
    # Calculate centroid distances to a
    dist = areas[idx].centroid.distance(areas.loc[a].geometry.centroid) # m

    d.loc[a, idx] = dist * X.loc[a, idx]

# Symmetricality
for i,row in d.iterrows():
    d.loc[:,i] = d.loc[i, :]


#%% ----------------------------- ###
###         4. Save Costs         ###
### ----------------------------- ###


### 4.1 Electricity Transmission - ASSUMPTIONS
# It is assumed that costs are symmmetrical
D = d.sum().sum()/2  # Total, modelled length
L = (d > 0).sum().sum()/2 # Total modelled lines

XE = d * XE_cost # € pr. MW




### 4.2 XINVCOST.inc
# Remove names
XE.columns.name = ''
XE.index.name = ''

# Add year
XE.index = '2016 . ' + XE.index

# Delete zeros
XE = XE.replace(0, '')

with open('./Output/XINVCOST.inc', 'w') as f:
    f.write("TABLE XINVCOST(YYY,IRRRE,IRRRI)        'Investment cost in new transmission capacity (Money/MW)'\n")
    dfAsString = XE.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n;')
    f.write("\nXINVCOST(YYY,IRRRE,IRRRI) = XINVCOST('2016',IRRRE,IRRRI);")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
          
### 4.3 Energy losses
XL = XLOSS_E * d

## Transmission
# Adjust
XL.columns.name = ''
XL.index.name = ''
XL = XL.replace(0, '')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
with open('./Output/XLOSS.inc', 'w') as f:
    f.write("TABLE XLOSS(IRRRE,IRRRI)        'Transmission loss between regions (fraction)'\n")
    dfAsString = XL.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n;')



### 4.4 XCOST.inc                   
xcost_e = X * XCOST_E
xcost_e.index.name = ''
# xcost_e.columns.name = ''
xcost_e = xcost_e.replace(0, '')

with open('./Output/XCOST.inc', 'w') as f:
    f.write("TABLE XCOST(IRRRE,IRRRI)  'Transmission cost between regions (Money/MWh)'\n")
    dfAsString = xcost_e.to_string(header=True, index=True).replace(the_index, '')
    f.write(dfAsString)
    f.write('\n;')




### 4.5 Distribution
## DISLOSS_E
disloss_e = pd.DataFrame(data={'' : [DLOSS_E]*len(areas.index)}, index=areas.index) # create losses
disloss_e.index.name = ''
disloss_e.columns.name = ''

with open('./Output/DISLOSS_E.inc', 'w') as f:
    f.write("PARAMETER DISLOSS_E(RRR)  'Loss in electricity distribution'              \n")
    f.write('/')
    dfAsString = disloss_e.to_string(header=True, index=True).replace(the_index, '')
    f.write(dfAsString)
    f.write('\n/;')
    
    
## DISCOST_E
discost_e = pd.DataFrame(data={'' : [DCOST_E]*len(areas.index)}, index=areas.index) # create losses
discost_e.index.name = ''
discost_e.columns.name = ''

with open('./Output/DISCOST_E.inc', 'w') as f:
    f.write("PARAMETER DISCOST_E(RRR)  'Cost of electricity distribution (Money/MWh)'")
    f.write('/')
    dfAsString = discost_e.to_string(header=True, index=True).replace(the_index, '')
    f.write(dfAsString)
    f.write('\n/;')
    
    

        
    
    
    
    
    
    
    
    
    