# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 22:51:15 2022

@author: Mathias Berg Rosendal, PhD, DTU Management

Use electricity transmission cost data from DEA2021:
https://ens.dk/en/our-services/projections-and-models/technology-data/technology-catalogue-transport-energy
A map of the extisting transmission grids:
https://energinet.dk/media/gqjj2xpk/eksisterende-net-2021.pdf <- DK

This is used to create demand files for Balmorel.


Works with the environment.yaml distributed in XXX
"""

import matplotlib.pyplot as plt
from matplotlib import rc
import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import MultiPolygon, Point
from pyproj import Proj
import numpy as np
import matplotlib.pyplot as plt
from functions import preprocess_geofiles
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
# choice = 'NUTS2'
# choice = 'DK municipalities'
choice = 'Nordpool'

# 0.2 Parameters
growth = 10 # Maximum growth of areas with no grid connection in km
growth_step = 1 # Step towards maximum growth in km
# Electricity transmission
# From DEA 2021, 111 'Main electricity distribution grid' (no data for transmission? these costs are for 50/60 kV)
XE_cost = 3.1*532 / 127 # €/MW/m high bound
# XE_cost = 2.511 # €/MW/m low bound
XE_substation_cost = 76000 # €/MW very high bound
# XE_substation_cost = 4476 # €/MW low bound
# XE_substation_cost = 0 # No cost
XE_FOM = 21.7/1e3*532 / 127 # €/MW/m/year

# 0.3 Assumptions for cost analysis
XCAP_high = 5 # GW electrical transmission capacity in total
XCAP_low = 0.5 # GW pr. line small line
Xsub = 99 # Amount of substations (assumed similar to today ~ one pr. municipality)
XT = 40 # Lifetime of electricity grid elements


# 0.4 Assumptions  distribution
# Choose between even or 'highway' distribution
distribution_type = 'highway'
# distribution_type = 'even'

# 'High capacity'-highway distribution
# XCAP_high is put on highway, XCAP_low everywhere else
if choice.lower().replace(' ', '') == 'dkmunicipalities':
    # Create 'power highway' paths
    line_path = pd.Series(['DNK.2.12_1', 'DNK.5.4_1', 'DNK.5.22_1',
                 'DNK.5.8_1', 'DNK.5.13_1', 'DNK.5.3_1',
                 'DNK.5.6_1', 'DNK.5.15_1', 'DNK.4.13_1',
                 'DNK.4.15_1', 'DNK.4.11_1', 'DNK.4.6_1', 
                 'DNK.4.14_1', 'DNK.4.2_1', 'DNK.1.24_1', 
                 'DNK.1.30_1', 'DNK.1.5_1', 'DNK.1.23_1', 
                 'DNK.1.25_1']).str.replace('DNK', 'DK')
    line_path = np.array([[line_path[i], line_path[i+1]] for i in range(len(line_path)-1)])
elif choice.lower() == 'nuts3':
    line_path = pd.Series(['DK041',
                           'DK032',
                           'DK031',
                           'DK022',
                           'DK021',
                           'DK012',
                           'DK011'])
    line_path = np.array([[line_path[i], line_path[i+1]] for i in range(len(line_path)-1)])    
elif choice.lower() == 'nuts2':
    line_path = pd.Series(['DK04',
                           'DK03',
                           'DK02',
                           'DK01'])
    line_path = np.array([[line_path[i], line_path[i+1]] for i in range(len(line_path)-1)])    
elif choice.lower() == 'nordpool':
    line_path = pd.Series(['DK_1',
                           'DK_2'])
    line_path = np.array([[line_path[i], line_path[i+1]] for i in range(len(line_path)-1)])    


### See more assumptions in sections
# 2.2 - Manual adjustments to links between regions
# 3.1 - Assumed symmetrical costs

#%% ----------------------------- ###
###        1. Read files          ###
### ----------------------------- ###

### 1.1 Load geodata
the_index, areas = preprocess_geofiles(choice)

if 'nuts' in choice.lower():
    areas = areas[areas.CNTR_CODE == 'DK']
elif 'nordpool' in choice.lower():
    # idx = ((areas.index.str.find('DK') != -1) | (areas.index.str.find('SE') != -1) | (areas.index.str.find('NO') != -1)) & (areas.index.str.find('IT') == -1)
    idx = (areas.index.str.find('DK') != -1) 
    areas = areas[idx]


#%% ----------------------------- ###
###    2. Calculate Distances     ###
### ----------------------------- ###

# Convert to geocentric coordinates for meter units
areas = areas.to_crs(4328)

### 2.1 Find Neighbours

# Create matrix for possible grid connections
X = pd.DataFrame(np.zeros((len(areas), len(areas))).astype(int),
                 index=areas.loc[:, the_index],
                 columns=areas.loc[:, the_index])
X.index.name = 'IRRRE'
X.columns.name = 'IRRRI'

# Use touches or intersects for areas not separated
for i,a in areas.iterrows():
    
    # Index for touching regions
    idx = areas.touches(a.geometry)
    
    # Assign possible links
    X.loc[a[the_index], areas.loc[idx, the_index]] = 1
    

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
    X.loc['DK.5.8_1', 'DK.5.13_1'] = 1
    # Nyborg-Sjælland
    X.loc['DK.4.13_1', 'DK.5.15_1'] = 1
    # Guldborgsund-Vordingborg
    X.loc['DK.4.3_1', 'DK.4.17_1'] = 1
    # Vordingborg-Næstved
    X.loc['DK.4.9_1', 'DK.4.17_1'] = 1
    # Lolland-Langeland
    X.loc['DK.4.8_1', 'DK.5.12_1'] = 1
    # Langeland-Svendborg
    X.loc['DK.5.12_1', 'DK.5.18_1'] = 1
    # Sønderborg-Faaborg-Midtfyn
    X.loc['DK.5.6_1', 'DK.5.17_1'] = 1
    # Samsø-Kalundborg
    X.loc['DK.2.13_1', 'DK.4.5_1'] = 1
    # Samsø-Midtjylland
    X.loc['DK.2.10_1', 'DK.2.13_1'] = 1
    # Frederikshavn-Læsø
    X.loc['DK.3.3_1', 'DK.3.6_1'] = 1
    # Haderslev-Assens
    X.loc['DK.5.3_1', 'DK.5.9_1'] = 1
    # Skive-Morsø
    X.loc['DK.2.16_1', 'DK.3.8_1'] = 1
    # Morsø-Thisted
    X.loc['DK.3.8_1', 'DK.3.10_1'] = 1
    # Morsø-Vesthimmerland
    X.loc['DK.2.16_1', 'DK.3.11_1'] = 1
    
    
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
fig, ax = plt.subplots(facecolor=fc)
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
        # Make fat 'power highway' if highway distribution is chosen
        if distribution_type == 'highway':
            if np.any((line_path[:,0] == A[the_index].values[0])*(line_path[:,1] == l[the_index])):
                width = 3
            else:
                width = 1
        else:
            width = 1
        p, = ax.plot([A.geometry.centroid.x, l.geometry.centroid.x],
                [A.geometry.centroid.y, l.geometry.centroid.y], 'r-',
                linewidth=width)

### 2.4 Calculate Distances
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
###      3. Calculate Costs       ###
### ----------------------------- ###


### 3.1 Electricity Transmission - ASSUMPTIONS
# It is assumed that costs are symmmetrical
D = d.sum().sum()/2  # Total, modelled length
L = (d > 0).sum().sum()/2 # Total modelled lines

XE = d * XE_cost # € pr. MW

#%% ----------------------------- ###
###          4. Analysis          ###
### ----------------------------- ###
### 4.1 Capital costs - ASSUMING EVEN DISTRIBUTION OF TOTAL GRID CAPACITY!!!!
CAPEX = XE.sum().sum()/2 * XCAP_high*1e3/2   # Assuming 50% of high capacity in all lines
CAPEX = CAPEX + Xsub*XE_substation_cost      # Substations
FOM = D * XE_FOM * XCAP_high*1e3/2           # Fixed costs
capacity = XCAP_high/2

### 4.2 Capital costs - with assumption on 'power highway'
if distribution_type == 'highway':
    CAPEX = XE * XCAP_low*1e3 
    FOM = d * XE_FOM * XCAP_low*1e3
    for ele in line_path:
        CAPEX.loc[ele[0], ele[1]] = XE.loc[ele[0], ele[1]] * XCAP_high*1e3
        CAPEX.loc[ele[1], ele[0]] = XE.loc[ele[1], ele[0]] * XCAP_high*1e3
        FOM.loc[ele[0], ele[1]] = d.loc[ele[0], ele[1]] * XE_FOM * XCAP_high*1e3
        FOM.loc[ele[1], ele[0]] = d.loc[ele[0], ele[1]] * XE_FOM * XCAP_high*1e3
    capacity = (CAPEX / XE).sum().sum()/2/1e3/L # GW/line
    CAPEX = CAPEX.sum().sum()/2 + Xsub*XE_substation_cost
    FOM = FOM.sum().sum()/2
    

# Annualised costs
# Discount factor (disc rate of 4%)
# AnnCosts = np.array([CAPEX] + [FOM for i in range(XT)]) # With FOM
AnnCosts = np.array([CAPEX] + [0 for i in range(XT)]) # Without FOM
disc_fac = np.array([1/(1+0.04)**i for i in range(XT+1)])

AnnCosts_disc = disc_fac*AnnCosts

CRF = 0.04*(1+0.04)**XT / ((1+0.04)**XT - 1)
NPV = np.sum(AnnCosts_disc)

# Annualised cost
ann_cost = NPV*CRF


print('------------------------------------','\nAt %s resolution:'%choice, 
      '\nCAPEX (annualised)\t = %d M€/yr\nFOM\t\t\t = %d M€/yr\nVirtual length\t\t = %d km\nNr. of lines\t\t = %d\nAverage Capacity\t = %d GW/line'%(ann_cost/1e6, FOM/1e6, D/1e3, L, capacity),
      '\n------------------------------------')


