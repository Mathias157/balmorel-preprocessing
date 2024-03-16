"""
Created on 11.03.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
# Disable the limit on pandas display ranges
pd.set_option('display.max_colwidth', None)
from pybalmorel.functions import IncFile, read_lines
from Modules.createDH import DistrictHeat
from Modules.createINDUSTRY import Industry
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

def generate_heat_data(areas):
    ### 1.0 Aggregate district heating data (only danish dataset for now)
    DKareas = areas[areas[the_index].str.find('DK') != -1]
    DH = DistrictHeat('Denmark')
    DH.dfint = calculate_intersects(DKareas, DH.geo) # Find intersects between district heat areas and chosen areas
    DH.assign_DH(DKareas, DH.dfint)
    DH.assign_DHT(DKareas, DH.dfint)


    ### 1.1 Check that the aggregation got all data:
    # Annual DH
    # print('\nOriginal data, annual DH:')
    # print(DH.DH[DH.DH.A.str.find('DK') != -1].pivot_table(index='A', columns='Y').sum() / 1e6)
    # print('\nNew data, annual DH:')
    # print(DH.dfDH.sum() / 1e6)


    ## Plot original vs aggregated data
    year = '2050'
    DH.plot_original_data(year, DKareas, plot_density=True)
    DH.plot_aggregated_data(year, DKareas, True)


    ### 1.2 Save .inc files
    incfiles = {}
    bodies = {'DH' : DH.dfDH,
              'DH_VAR_T' : DH.dfDHT}
    for file in ['DH', 'DH_VAR_T']:
        incfiles[file] = IncFile(prefix=read_lines(file+'_prefix.inc', 
                                                file_path='Data/IncFilePreSuf'),
                                body=bodies[file],
                                suffix=read_lines(file+'_suffix.inc',
                                                file_path='Data/IncFilePreSuf'),
                                path='Output',
                                name=file)

    for file in incfiles.keys():
        incfiles[file].save()

    return DH

#%% ------------------------------- ###
###          2. VRE Data            ###
### ------------------------------- ###

#%% ------------------------------- ###
###          3. Industry            ###
### ------------------------------- ###

def generate_industry_data(area):
    IND = Industry()

    ### 1.2 Assign Original Region
    IND.assign_original_region()

    # Assign fraction of emissions in region
    IND.assign_emission_fractions() 

    incfiles = IND.create_industry_data(areas, True)
    
    # Prepare inc-files
    ind_areas = incfiles['INDUSTRY_DH'].body['A'].unique()
    incfiles['INDUSTRY_CCCRRRAAA'].body = '\n'.join(list(ind_areas))
    incfiles['INDUSTRY_RRRAAA'].body = '\n'.join(list("%s . %s"%(area.split('_')[0], area) for area in ind_areas))
    incfiles['INDUSTRY_AAA'].body = '\n'.join(list(ind_areas))
    incfiles['INDUSTRY_GKFX'].body_prepare(['A', 'G'], ['Y'])
    incfiles['INDUSTRY_DH'].body_prepare(['DHUSER', 'A'], ['Y'])
    incfiles['INDUSTRY_DH_VAR_T'].body_prepare(['S', 'T'], ['A', 'DHUSER'])
    incfiles['INDUSTRY_DE'].body_prepare(['DEUSER', 'R'], ['Y'])
    incfiles['INDUSTRY_AGKN'].body = '\n'.join([f"AGKN('{row['A']}', '{row['G']}') = YES;" for i,row in incfiles['INDUSTRY_AGKN'].body.iterrows()])
    # INDUSTRY_INDUSTRY_AAA
    incfiles['INDUSTRY_INDUSTRY_AAA'] = incfiles['INDUSTRY_AAA']
    incfiles['INDUSTRY_INDUSTRY_AAA'].prefix = incfiles['INDUSTRY_INDUSTRY_AAA'].prefix.replace('SET AAA', 'SET INDUSTRY_AAA')
    incfiles['INDUSTRY_INDUSTRY_AAA'].name = 'INDUSTRY_INDUSTRY_AAA'
    
    
    for file in ['INDUSTRY_GKFX', 'INDUSTRY_DH', 'INDUSTRY_DH_VAR_T',
                 'INDUSTRY_DE', 'INDUSTRY_AGKN', 'INDUSTRY_CCCRRRAAA',
                 'INDUSTRY_RRRAAA', 'INDUSTRY_AAA', 'INDUSTRY_AAA',
                 'INDUSTRY_DISLOSS_E_AG']: 
        incfiles[file].save()


    return incfiles

# Plot data
# IND.plot_original_data()
# IND.plot_aggregated_data(incfiles, areas, 'GKFX')

#%% ------------------------------- ###
###        X. Generate Data         ###
### ------------------------------- ###

if __name__ == '__main__':

    ### X.1 Load the desired spatial resolution
    choice = 'nuts3'
    the_index, areas, c = prepared_geofiles(choice)
    areas = areas[areas[the_index].str.find('DK') != -1]

    ### X.2 Generate Data
    DH = generate_heat_data(areas)
    
    incfiles = generate_industry_data(areas) # Note: No possiblity to meet demand in LT areas! (only storage investments allowed)