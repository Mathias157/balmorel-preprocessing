#%%
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 16:29:32 2022

@author: mathi
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc
from formplot import *
from scipy.optimize import curve_fit
import geopandas as gpd
import cartopy.crs as ccrs
from shapely.geometry import MultiPolygon
from functions import PreProcessShapes

style = 'ppt'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ----------------------------- ###
###         0. ASSUMPTIONS        ###
### ----------------------------- ###

### 0.1 Load geodata
# What areas to load?
# choice = 'Nordpool'
# choice = 'NUTS1'
# choice = 'NUTS2'
# choice = 'NUTS3'
choice = 'DK Municipalities'
# choice = 'BalmorelVREAreas'

### 0.2 Choose country 

### ASSUMPTIONS
# 2.1 Only DK right now
# 2.2 - Investment options!!! How to distribute? Right now a semi-automatic hack


#%% ------------------------------- ###
### 1. Load Geodata and Pre-process ###
### ------------------------------- ###

the_index, areas = PreProcessShapes(choice)
areas.plot()


#%% ------------------------------- ###
###       2. Make Set Files         ###
### ------------------------------- ###

### 2.1 Create regions and areas
# if choice.replace(' ', '').lower() == 'dkmunicipalities':
#     AAA = areas.GID_2
# elif (choice.replace(' ', '').lower() == 'nuts1') |\
#     (choice.replace(' ', '').lower() == 'nuts2') |\
#         (choice.replace(' ', '').lower() == 'nuts3'):
#     AAA = areas.NUTS_ID
AAA = areas[the_index]    

# Regions
RRR = AAA

# Areas
AAA = AAA + '_A'

# f = open('CCCRRRAAA.inc', 'w')
# with open('CCCRRRAAA.inc', 'a') as f:
#     f.write("SET AAA(CCCRRRAAA)  'All areas'\n")
#     f.write("/\n")
#     dfAsString = AAA.to_string(header=False, index=False)
#     f.write(dfAsString)
#     f.write('\n/\n;')

# f = open('./Output/CCCRRRAAA.inc', 'w')
with open('./Output/CCCRRRAAA.inc', 'w') as f:
    f.write("SET CCCRRRAAA 'All geographic entities'       \n")
    f.write("/\n")
    # dfAsString = (RRR + ' . ' + AAA).to_string(header=False, index=False)
    f.write('DENMARK\n')
    f.write(RRR.to_string(header=False, index=False))
    f.write('\n')
    f.write(AAA.to_string(header=False, index=False))
    f.write('\n/\n;')

with open('./Output/CCCRRR.inc', 'w') as f:
    f.write("SET CCCRRR(CCC, RRR) 'Regions in countries'       \n")
    f.write("/\n")
    dfAsString = ('DENMARK' + ' . ' + RRR).to_string(header=False, index=False)
    f.write(dfAsString)
    f.write('\n/\n;')

# f = open('./Output/RRRAAA.inc', 'w')
with open('./Output/RRRAAA.inc', 'w') as f:
    f.write("SET RRRAAA(RRR,AAA) 'Areas in regions'       \n")
    f.write("/\n")
    dfAsString = (RRR + ' . ' + AAA).to_string(header=False, index=False)
    f.write(dfAsString)
    f.write('\n/\n;')


# f = open('AAA.inc', 'w')
with open('./Output/AAA.inc', 'w') as f:
    f.write("SET AAA(CCCRRRAAA)  'All areas'\n")
    f.write("/\n")
    dfAsString = AAA.to_string(header=False, index=False)
    f.write(dfAsString)
    f.write('\n/\n;')
    
with open('./Output/RRR.inc', 'w') as f:
    f.write("SET RRR(CCCRRRAAA)  'All regions'\n")
    f.write("/\n")
    dfAsString = RRR.to_string(header=False, index=False)
    f.write(dfAsString)
    f.write('\n/\n;')

### 2.2 Create investment options
# Do something that takes into account offshore possibilities


# AGKN - Allowed investments how to do?
# Hack for now
with open('./Output/AGKN.inc', 'w') as f:
    for a in areas.index:
        f.write("""
                AGKN('%s', GGG) = AGKN('DK2_Large',GGG) + AGKN('DK2_NoDH',GGG);
                AGKN('%s', 'GNR_ST_NUCL_CND_E-33') = YES;
                AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GWND)  = YES  ;
                AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GHSTO) = YES  ;          
                AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GESTO) = YES  ;          
                AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GESTOS) = YES ;          
                AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GSOLE) = YES  ;          
                AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GSOLH) = YES  ;          
                """%tuple(8*[a + '_A']))
                #.replace(' ', '')%tuple(8*[a + '_A']))


