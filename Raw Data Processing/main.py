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
