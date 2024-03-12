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
from Modules.geofiles import prepared_geofiles

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'
    
the_index, areas, c = prepared_geofiles('nuts3')


#%% ------------------------------- ###
###        1. 
### ------------------------------- ###


choice = 'DKMunicipalities'
the_index, areas, c = prepared_geofiles(choice)


DKareas = areas[areas[the_index].str.find('DK') != -1]
DH = DistrictHeat('Denmark')
DH.dfint = DH.find_intersects(DKareas) # Find intersects between district heat areas and chosen areas
DH.assign_DH(DKareas, DH.dfint)


# Check that the aggregation got all data:
# Annual DH
print('\nOriginal data, annual DH:')
print(DH.DH[DH.DH.A.str.find('DK') != -1].pivot_table(index='A', columns='Y').sum() / 1e6)
print('\nNew data, annual DH:')
print(DH.dfDH.sum() / 1e6)


## Plot aggregated data
year = '2050'

DH.plot_original_data(year, DKareas, plot_density=True)

DH.plot_aggregated_data(year, DKareas, True)