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
from pybalmorel.functions import IncFile, read_lines
from Modules.createDH import DistrictHeat
from Modules.geofiles import prepared_geofiles, calculate_intersects

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

# Go to section X. for the execution of the functions below

#%% ------------------------------- ###
###     1. District Heating Data    ###
### ------------------------------- ###

def generate_DH_data(areas):
    ### 1.0 Aggregate district heating data
    DKareas = areas[areas[the_index].str.find('DK') != -1]
    DH = DistrictHeat('Denmark')
    DH.dfint = calculate_intersects(DKareas, DH.geo) # Find intersects between district heat areas and chosen areas
    DH.assign_DH(DKareas, DH.dfint)
    DH.assign_DHT(DKareas, DH.dfint)


    ### 1.1 Check that the aggregation got all data:
    # Annual DH
    print('\nOriginal data, annual DH:')
    print(DH.DH[DH.DH.A.str.find('DK') != -1].pivot_table(index='A', columns='Y').sum() / 1e6)
    print('\nNew data, annual DH:')
    print(DH.dfDH.sum() / 1e6)


    ## Plot original vs aggregated data
    year = '2050'
    DH.plot_original_data(year, DKareas, plot_density=True)
    DH.plot_aggregated_data(year, DKareas, True)


    ### 1.2 Save .inc files
    incfiles = {}
    for file in ['DH', 'DH_VAR_T']:
        incfiles[file] = IncFile(prefix=read_lines(file+'_prefix.inc', 
                                                file_path='Data/IncFilePreSuf'),
                                suffix=read_lines(file+'_suffix.inc',
                                                file_path='Data/IncFilePreSuf'),
                                path='Output',
                                name=file)
        
    incfiles['DH'].body = DH.dfDH.to_string()
    incfiles['DH_VAR_T'].body = DH.dfDHT.to_string()

    for file in incfiles.keys():
        incfiles[file].save()

    return DH

#%% ------------------------------- ###
###          2. VRE Data            ###
### ------------------------------- ###



#%% ------------------------------- ###
###        X. Generate Data         ###
### ------------------------------- ###

if __name__ == '__main__':

    ### X.1 Load the desired spatial resolution
    choice = 'nuts3'
    the_index, areas, c = prepared_geofiles(choice)

    ### X.2 Generate Data
    # DH = generate_DH_data(areas)
    
    