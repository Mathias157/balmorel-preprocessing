#%%# -*- coding: utf-8 -*-
"""
Created on Sat Dec  3 15:33:10 2022

@author: mathi

See the following documentation, for understanding how this script works:
    Cutouts: https://atlite.readthedocs.io/en/latest/examples/create_cutout.html
    Power potentials: https://atlite.readthedocs.io/en/latest/examples/landuse-availability.html

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc
from scipy.optimize import curve_fit
import atlite
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import MultiPolygon
from pyproj import Proj, Transformer
from rasterio.plot import show
import xarray as xr
from atlite.gis import shape_availability, ExclusionContainer
import os
from Modules.geofiles import prepared_geofiles

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

### Function fo load duration curve analysis
def doLDC(file, cols, idx, r, c, title=''):
    global fc
    fig, axes = plt.subplots(nrows=r, ncols=c, figsize=(8,5), facecolor=fc)
    axes = np.asarray(axes).reshape(-1) # Convert axes to array
    i = 0
    for c in cols:
        # Extract profile
        data_ht = np.histogram(file[c], bins=50)
        data_lt = np.histogram(file[c][idx], bins=50)
        lt_hours = idx.sum() # Hours in low time res is the amount of "true" in idx
        
        # Plot
        axes[i].plot((np.cumsum(data_ht[0][::-1])/8736*100), data_ht[1][:-1][::-1]/max(data_ht[1])*100, label='8736h')
        axes[i].plot((np.cumsum(data_lt[0][::-1])/lt_hours*100), data_lt[1][:-1][::-1]/max(data_lt[1])*100, label='%dh'%(lt_hours))
         
        axes[i].set_ylim([0, 100])
        #axes[i].set_title(c)
        axes[i].text(20, 80, c, 
                     bbox=dict(facecolor=fc, alpha=.5, edgecolor='none'))
        # ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
        # verticalalignment='top', bbox=dict(boxstyle='square,pad=.6',facecolor='lightgrey', edgecolor='black', alpha=0.7))

        # Better if only one plot
        # if title != '':
        #     axes[i].set_ylabel(title)    
        if (i == 0) | (i == 4) | (i == 8):
            axes[i].set_ylabel(title)
        else:
            axes[i].set_yticklabels([])
        # axes[i].set_title(c)
        # axes[i].legend()
        if (i >= 7):
            axes[i].set_xlabel('Duration [%]')
        else:
            axes[i].set_xticklabels([])
        i += 1
            
    # Other finesse
    fig.delaxes(axes[i])
    # fig.suptitle(S)
    axes[10].legend(loc='center', bbox_to_anchor=(1.7, .5))
    
    return fig, axes

#%% ------------------------------- ###
###         0. Assumptions          ###
### ------------------------------- ###

### 0.1 Capacity pr. km for PV and Wind
cap_per_sqkm_pv = 1.7 # MW/km2
cap_per_sqkm_wind = 0.67 # MW/km2 According to NREL: 2 MW / 1.5 acres (0.00607028 km2)


### 0.2 Choice of technologies
panel = atlite.solarpanels.CSi # Possible to choose crystalline Si (CSi) or advanced cadmium-tellurium (CdTe)
wind_turbine = atlite.windturbines.Vestas_V66_1750kW
# wind_turbine = atlite.windturbines.Enercon_E82_3000kW
# wind_turbine = atlite.windturbines.Bonus_B1000_1000kW

# Offshore wind
# wind_turbine = atlite.windturbines.NREL_ReferenceTurbine_5MW_offshore

### 0.3 What areas to load?
# choice = 'DK Municipalities'
# choice = 'NUTS1'
# choice = 'NUTS2'
# choice = 'NUTS3'
choice = 'NordpoolReal'
# choice = 'BalmorelVREAreas'

## Cutouts
# path = "Nicolas_2015_full.nc"
path = "DK.nc"
# cutout_bounds_x = (11.015880, 13.078094) # Longitude
# cutout_bounds_y = (43.239006, 45.207804) # Latitude
# cutout_bounds_x = (11.7, 12.2) # Longitude
# cutout_bounds_y = (43.85, 44.4) # Latitude
cutout_bounds_x = (7.5, 16) # Longitude
cutout_bounds_y = (54.4, 58) # Latitude


### 0.4 What time to load?
# T = "2011-01-01"
T = '2017'

### 0.5 Overwrite cutout?
OverW = True

### 0.6 Read Geodata
the_index, areas, country_code = prepared_geofiles(choice)
areas = areas.loc[['DK1', 'DK2']] # Testing DK and DE
areas.geometry = areas['geometry']
# areas.loc[:,'GID_2'] = areas.GID_2.str.replace('.', '_')

# Read homemade offshore potentials for DK
OFFWNDPOT = gpd.read_file(r'.\Data\RandomOffWindPot\DK.gpkg')

# Plot
fig, ax = plt.subplots()
areas.plot(ax=ax)

ax.set_xlim(-11,32)      
ax.set_ylim(35,72)
ax.set_title(choice)
# OFFWNDPOT.plot(ax=ax)

# Filtering Italy
# if choice == 'Nordpool':
#     areas = areas[areas.index == 'IT_NORD']



### ASSUMPTIONS
# 3.3 A quick fix for SOLH_VAR_T and SOLHFLH
# 3.4 Capacity is based on RG1 VRE technology - all others regions are set to 0 potential
# 3.4 Offshore wind potential is a hack right now - manual inputted GW

#%% ------------------------------- ###
### 1. Load Geodata and Pre-process ###
### ------------------------------- ###

## Projections

UTM32 = Proj(proj='utm', zone=32, ellps='WGS84', preserve_units=False)
GM = Proj('EPSG:900913', preserve_units=False)
# transformer = Transformer.from_crs('EPSG:900913', 'EPSG:4326')
# out = Transformer(GM, UTM32, (11, 13), (43, 45), always_xy=True) 

    

### 1.2 Visualise current areas
# Set projection
crs = ccrs.UTM(32)
# Make compatible with geopandas
# projection = crs.proj4_init # doesn't work, so actually cartopy is useless - continuing only with geopandas

# Make figure
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={"projection": crs},
                       dpi=200)


# Add areas
ax.add_geometries(areas.geometry, crs = crs,
                  facecolor=[.9, .9,.9], edgecolor='grey',
                  linewidth=.2)

ax.set_xlim(areas.bounds[['minx']].values.min(), areas.bounds[['maxx']].values.max())
ax.set_ylim(areas.bounds[['miny']].values.min(), areas.bounds[['maxy']].values.max())
# ax.set_xlim(7.5,16)      
# ax.set_ylim(54.4,58)  


### 1.3 Load Nordpool regions
# NP = pd.read_csv(project_dir/'geo_files/coordinates_RRR.csv')
# NP = NP.loc[df_unique['Type'] == 'region', ]

#%% ------------------------------- ###
###   2. Calculate RE Potentials    ###
### ------------------------------- ###

### 2.1 Load Cutout
cutout = atlite.Cutout(path=path,
                       module="era5",
                       x=slice(cutout_bounds_x[0], cutout_bounds_x[1]),
                       y=slice(cutout_bounds_y[0], cutout_bounds_y[1]),
                       time=T
                       )
cutout.prepare(overwrite=OverW)




### 2.2 Load Map for RE Spatial Availabilities
# CORINE = 'corine.tif'
CORINE = r'Data\CORINE\u2018_clc2018_v2020_20u1_raster100m\u2018_clc2018_v2020_20u1_raster100m\DATA\U2018_CLC2018_V2020_20u1.tif'
excluder = ExclusionContainer()
excluder.add_raster(CORINE, codes=range(20))

# Convert crs to CORINE map
A = areas.geometry.to_crs(excluder.crs)
A.index = getattr(areas, the_index)




### 2.3 Calculate eligible shares
masked, transform = shape_availability(A, excluder)
# eligible_share = masked.sum() * excluder.res**2 / A.loc[[3]].geometry.item().area # Only eligible share for bornholm 3
# Eligible share of all of A
Aall = gpd.GeoDataFrame({'geometry' : [A.geometry.cascaded_union]})
eligible_share = masked.sum() * excluder.res**2 / Aall.geometry.item().area # Only eligible share for bornholm 3




### 2.4 Plot figures of availabilities (green is available land)
# Simple plot
# fig, ax = plt.subplots()
# ax = show(masked, transform=transform, cmap='Greens', ax=ax)
# A.plot(ax=ax, edgecolor='k', color='None')
# ax.set_title(f'Eligible area (green) {eligible_share * 100:2.2f}%')

### Plot that shows the discrete rectangles used
fig, ax = plt.subplots()
ax = show(masked, transform=transform, cmap='Greens', ax=ax)
A.plot(ax=ax, edgecolor='k', color='None')
# cutout.grid.plot(edgecolor='grey', color='None', ax=ax, ls=':')
cutout.grid.to_crs(excluder.crs).plot(edgecolor='grey', color='None', ax=ax, ls=':')
ax.set_title(f'Eligible area (green) {eligible_share * 100:2.2f}%')

# ax.set_xlim(4.5e6-0.1e6, 4.5e6+0.1e6)
# ax.set_ylim(2.46-0.1e6, 2.4e6+0.1e6)

### 2.5 Calculate Availability Matrix for all Regions
# Amat.index = ['Denmark']
A = A.geometry.set_crs(excluder.crs)
Amat = cutout.availabilitymatrix(A, excluder)

### Plot first region availability  
fig, ax = plt.subplots()
Amat.sel({the_index :A.index[0]}).plot(ax=ax) # Amat gives fractional availabilities in each weather cell
A.plot(ax=ax, edgecolor='k', color='None')
cutout.grid.plot(ax=ax, color='None', edgecolor='grey', ls=':')
# ax.set_xlim(7.5,16)      
# ax.set_ylim(54.4,58) 

### Calculate areas in weather cells in sqkm
area = cutout.grid.set_index(['y', 'x']).to_crs(3035).area / 1e6 # 3035 is CRS of CORINE map
area = xr.DataArray(area, dims=('spatial'))




### 2.6 Calculate PV Potential
capacity_matrix = Amat.stack(spatial=['y', 'x']) * area * cap_per_sqkm_pv # Converts fraction of weather cells to
cutout.prepare()

# Sum of matrix is total potential...?

# Get production
# pv = cutout.pv(matrix=capacity_matrix, panel=panel,
#                 orientation='latitude_optimal', index=A.index)
pv = cutout.pv(matrix=capacity_matrix, panel=panel,
                orientation={'slope': 30, 'azimuth': 180.}, index=A.index)
ax = pv.to_pandas().div(1e3).plot(ylabel='Solar Power [GW]', ls='--', figsize=(15, 4))
ax.legend(ncol=8, loc='center', bbox_to_anchor=(.5, 1.5))

# Getting a specific profile
pv.loc[:, getattr(pv, the_index).values[0]]




### 2.7 Calculate Wind Turbine Potential
capacity_matrix = Amat.stack(spatial=['y', 'x']) * area * cap_per_sqkm_wind
cutout.prepare()

# Get production
wind = cutout.wind(matrix=capacity_matrix, turbine=wind_turbine,
                index=A.index)
ax = wind.to_pandas().div(1e3).plot(ylabel='Wind Power [GW]', ls='--', figsize=(15, 4)) 
ax.legend(ncol=8, loc='center', bbox_to_anchor=(.5, 1.5))

# Getting a specific profile
wind.loc[:, getattr(wind, the_index).values[0]]

#%% ------------------------------- ###
###     3. Create Balmorel Input    ###
### ------------------------------- ###


### 3.1 Convert data
# .to_pandas() can be used to store profiles from wind or pv
W = wind.to_pandas()
S = pv.to_pandas()

# Get correct timeseries index for Balmorel
t = W.index.isocalendar()
t['hour'] = t.index.hour

# Filter away first week, from last year 
idx = t.index.year == t['year'] 
t = t[idx]
W = W[idx]
S = S[idx]

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
t.loc[idx, 'T'] = '00' + t['T']
idx = t['T'].str.len() == 2
t.loc[idx, 'T'] = '0' + t['T']
t['T'] = 'T' + t['T']
 

# Create new index
W.index = t['S'] + ' . ' + t['T']
S.index = t['S'] + ' . ' + t['T']

# Clean up areas
W.columns = W.columns.str.replace('.', '_')
W.columns.name = ''
W.columns = W.columns + '_A'
S.columns = S.columns.str.replace('.', '_')
S.columns.name = ''
S.columns = S.columns + '_A'

# Clean up values
# W.iloc[:,:] = W.iloc[:,:].astype(str)
# S.iloc[:,:] = S.iloc[:,:].astype(str)




### 3.2 Variation Profiles
# Format of SOLE_VAR_T and WND_VAR_T
# TABLE WND/SOLE_VAR_T1(SSS,TTT,AAA)               "Variation of the wind/solar generation"    
#               A1     A2     ...
# S01.T001      val    val
# ...
# S52.T168      val    val
# ;
#

## Saving directly to .inc files:
# Wind
# f = open('WND_VAR_T.inc', 'w')
with open('./Output/WND_VAR_T.inc', 'w') as f:
    f.write('TABLE WND_VAR_T1(SSS,TTT,AAA)            "Variation of the wind generation"\n')
    # f.write('+') # If adding to another WND_VAR_T
    dfAsString = W.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n;')
    f.write('\nWND_VAR_T(AAA,SSS,TTT) = WND_VAR_T1(SSS,TTT,AAA);')
    f.write('\nWND_VAR_T1(SSS,TTT,AAA) = 0;')

# Solar
# f = open('SOLE_VAR_T.inc', 'w')
with open('./Output/SOLE_VAR_T.inc', 'w') as f:
    f.write('TABLE SOLE_VAR_T1(SSS,TTT,AAA)            "Variation of the solar generation"\n')
    dfAsString = S.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n;\n')
    f.write('SOLE_VAR_T(AAA,SSS,TTT) = SOLE_VAR_T1(SSS,TTT,AAA);\n')
    f.write('SOLE_VAR_T1(SSS,TTT,AAA) = 0;\n')




### 3.3 Full load hours
# Format of SOLEFLH and WNDFLH
# TABLE WND/SOLEFLH(AAA)               "Full load hours for wind/solar power" 
# /   
# A1        val
# A2        val
# ...
# An        val
# /;
#

# Calculating full load hours by sum of normalised timeseries
FLH_W = W.sum() / W.max() * (8736/len(t))
FLH_S = S.sum() / S.max() * (8736/len(t))
with open('./Output/SOLEFLH.inc', 'w') as f:
    f.write('Parameter SOLEFLH(AAA)            "Full load hours for solar power (hours)"\n')
    f.write('/')
    dfAsString = FLH_S.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n/\n;')
    
with open('./Output/WNDFLH.inc', 'w') as f:
    f.write('Parameter WNDFLH(AAA)            "Full load hours for wind power (hours)"\n')
    f.write('/')
    dfAsString = FLH_W.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n/\n;')
    
# Quick fix for solar heating profiles
FLH_SH = FLH_S / 5
with open('./Output/SOLHFLH.inc', 'w') as f:
    f.write('Parameter SOLHFLH(AAA)            "Full load hours for solar heat (hours)"\n')
    f.write('/')
    dfAsString = FLH_SH.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n/\n;')
    
    
with open('./Output/SOLH_VAR_T.inc', 'w') as f:
    f.write('TABLE SOLH_VAR_T1(SSS,TTT,AAA)            "Variation of the solar generation"\n')
    dfAsString = S.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n;\n')
    f.write('SOLH_VAR_T(AAA,SSS,TTT) = SOLH_VAR_T1(SSS,TTT,AAA);\n')
    f.write('SOLH_VAR_T1(SSS,TTT,AAA) = 0;\n')

### X.X CALCULATE POTENTIALS
exc_points = gpd.read_file(r'.\Data\Shapefiles\BalmorelVRE\BalmGrid-Urb-GLWD123-WDPA012-MTabove1km.gpkg')
VREareas = gpd.read_file(r'.\Data\Shapefiles\BalmorelVRE\BalmorelVREAreas.gpkg')
exc_points = exc_points.set_crs(VREareas.crs) # Set CRS
exc_points_bounds = exc_points.bounds
#%%
for i,row in areas.iloc[10:13].iterrows(): # West-germany and DK in NordpoolReal
    print(row['RRR'])
    
    fig, ax = plt.subplots()
    geo_ser = VREareas.intersection(row.geometry)
    geo_ser_df = gpd.GeoDataFrame({'geometry' : geo_ser.geometry})
    geo_ser.plot(ax=ax)
    xlims = ax.get_xlim()
    ylims = ax.get_ylim()
    
    ## Narrow points down
    idx = exc_points_bounds.minx > xlims[0]
    idx = idx & (exc_points_bounds.maxx < xlims[1])
    idx = idx & (exc_points_bounds.miny > ylims[0])
    idx = idx & (exc_points_bounds.maxy < ylims[1])
    temp_points = exc_points[idx]
    
    ## Get points inside polygon intersection
    temp_points = gpd.sjoin(temp_points, geo_ser_df)
    
    temp_points.plot(ax=ax, markersize=0.5, color='r')
    
    ## Get capacity
    available_space = temp_points.shape[0] * 30 * 30 # km2
    
    print('Potential of PV installation: %0.0f MW'%(cap_per_sqkm_pv*available_space)) 
    print('Potential of Wind installation: %0.0f MW'%(cap_per_sqkm_wind*available_space)) 
    
    
    ### OFFSHORE IF STATEMENT! OR AFTERWARDS?

    # print(VREareas[VREareas.intersects(row.geometry)].Region)
    # l = gpd.GeoSeries(areas.loc[R].geometry).plot(ax=ax)
    # ax.set_title(R)
    
## Each marker is 30x30 km


#%% 3.4 Potentials
# Format of SOLEFLH and WNDFLH
# TABLE WND/SOLEFLH(AAA)               "Full load hours for wind/solar power" 
# /   
# A1        val
# A2        val
# ...
# An        val
# /;
#

# Calculating capacity by maximum power output from atlite series
CAP_W = W.max()
CAP_S = S.max()

CAP_OFFW = pd.DataFrame({'WINDTURBINE_OFFSHORE.RG1_OFF1' : [0]*len(CAP_W)}, index = CAP_W.index)
### For offshore wind - HACK! Manually created points
for i,row in OFFWNDPOT.iterrows():
    
    # Assign point to nearest polygon
    dist = {r[0] : r[1].geometry.distance(row.geometry) for r in areas.iterrows()}
    
    # Get index of closest region
    ind = min(dist, key=dist.get)
    
    # Accumulate capacity to closest region and make new offshore area
    # try:
    #     CAP_OFFW.loc[ind+'_A_OFF'] = CAP_OFFW.loc[ind+'_A_OFF'] + row['Pot_GW']
    # except KeyError:
    #     CAP_OFFW.loc[ind+'_A_OFF'] = row['Pot_GW']
    # Accumulate capacity to closest region
    CAP_OFFW.loc[ind+'_A'] = CAP_OFFW.loc[ind+'_A'] + row['Pot_GW']
         
    
    # print(ind)
    # if choice == 'NUTS3':
    #     pp.loc[i, 'area'] = areas.loc[ind, 'NUTS_ID']
    # elif choice == 'DK Municipalities':
    #     pp.loc[i, 'area'] = areas.loc[ind, 'GID_2']

# Make format
CAP = pd.DataFrame({'SOLARPV.RG1' : np.hstack((CAP_S.values, np.zeros(len(CAP_OFFW) - len(CAP_S)))),
                    'WINDTURBINE_ONSHORE.RG1' : np.hstack((CAP_W.values, np.zeros(len(CAP_OFFW) - len(CAP_S)))),
                    'WINDTURBINE_OFFSHORE.RG1_OFF1' : CAP_OFFW.values[:,0]*1e3},  # In MW
                   index=CAP_OFFW.index)

with open('./Output/SUBTECHGROUPKPOT.inc', 'w') as f:
    f.write("TABLE SUBTECHGROUPKPOT(CCCRRRAAA,TECH_GROUP,SUBTECH_GROUP)       'SubTechnology group capacity restriction by geography (MW)'\n")
    dfAsString = CAP.to_string(header=True, index=True)
    f.write(dfAsString)
    f.write('\n;')
    # These lines make sure that the RG2-3 OFF2-5 regions are not available (all assigned to RG1!)
    f.write("\nSUBTECHGROUPKPOT(AAA,'SOLARPV',SUBTECH_GROUP)$(SUBTECHGROUPKPOT(AAA,'SOLARPV',SUBTECH_GROUP) = 0) = EPS;")
    f.write("\nSUBTECHGROUPKPOT(AAA,'WINDTURBINE_ONSHORE',SUBTECH_GROUP)$(SUBTECHGROUPKPOT(AAA,'WINDTURBINE_ONSHORE',SUBTECH_GROUP) = 0) = EPS;")
    f.write("\nSUBTECHGROUPKPOT(AAA,'WINDTURBINE_OFFSHORE',SUBTECH_GROUP)$(SUBTECHGROUPKPOT(AAA,'WINDTURBINE_OFFSHORE',SUBTECH_GROUP) = 0) = EPS;")

    
#%% ------------------------------- ###
###          4. Analysis            ###
### ------------------------------- ###

### 4.1 Look at representative periods
# The weeks to compare to full resolution
# per = ['S01', 'S14', 'S27', 'S40']
# # per = ['S27']I

# idx = W.index.str.find(per[0]) != -1 
# for s in per[1:]:
#     idx = idx | (W.index.str.find(s) != -1)

# for i in range(9):
#     doLDC(W, W.columns[i*11:(i+1)*11], idx, 3, 4, title='Wind LDC [%]')
#     doLDC(S, S.columns[i*11:(i+1)*11], idx, 3, 4, title='Solar LDC [%]')

