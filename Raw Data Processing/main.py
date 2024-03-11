"""
Created on 11.03.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from Modules.createDH import DistrictHeat
from Modules.geofiles import preprocess_geofiles

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'
    
the_index, areas, c = preprocess_geofiles('nuts3')
DH = DistrictHeat()


#%% ------------------------------- ###
###        1. 
### ------------------------------- ###


DKareas = areas[areas[the_index].str.find('DK') != -1]
fig, ax = plt.subplots()
DKareas.plot(ax=ax, facecolor=[.8, .8, .8])
DH.geo.plot(ax=ax, facecolor=[.6, 0, 0])

DKareas = DKareas.to_crs(4328) # To geocentric (meters)
DH.geo = DH.geo.to_crs(4328) # To geocentric (meters)

df = pd.DataFrame()
for element in DKareas.index:
    df['DK areas'] = DH.geo.BalmorelAr
    df['m^2 intersect'] = DH.geo.geometry.intersection(DKareas.geometry[element]).area
print('Intersect of %s with \n%s'%(element, df.to_string()))
    
DH.geo = DH.geo.to_crs(4326) # To geocentric (meters)
DKareas = DKareas.to_crs(4326) 