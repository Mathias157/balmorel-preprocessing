"""
TITLE

Description

Created on 24.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import os
import pickle
import pandas as pd
from Submodules.utils import combine_dicts
from pybalmorel.interactive.dashboard.eel_dashboard import create_incfiles

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

def load_set(file: str):
    return pickle.load(open(os.path.join('Modules', 'Submodules', '%s.pkl'%file), 'rb'))

def format_set(combined_dict: dict, set_dimension: int):
    
    all_areas = pd.concat([pd.DataFrame(combined_dict.values())[i] for i in range(set_dimension)], ignore_index=True)
    all_areas = {area : [] for area in all_areas}
    
    ## Prepare format that create_incfiles expects
    geo_nodes = {
        'countries' : {'DENMARK' : list(combined_dict.keys())},
        'regions' : combined_dict,
        'areas' : all_areas
    }
    
    return geo_nodes

def main():
    
    # Maybe wait with this one until you have VRE areas too
    # 1.1 Create base .inc files 
    f = combine_dicts([load_set('districtheat_sets')])
    create_incfiles(str(format_set(f, 1)), 'Output')
    
    
    # 1.2 Create INDUSTRY sets
    f = combine_dicts([
        load_set('ind-lt_sets'),
        load_set('ind-mt_sets'),
        load_set('ind-ht_sets')
    ])
    create_incfiles(str(format_set(f, 3)), 'Output', 'INDUSTRY_')
    
    # 1.3 Create INDIVUSERS sets
    f = combine_dicts([load_set('individual_sets')])
    create_incfiles(str(format_set(f, 1)), 'Output', 'INDIVUSERS_')
    
    
    # AGKN - Allowed investments how to do?
    # Hack for now
    # with open('./Output/AGKN.inc', 'w') as f:
    #     for a in areas.index:
    #         f.write("""
    #                 AGKN('%s', GGG) = AGKN('DK2_Large',GGG) + AGKN('DK2_NoDH',GGG);
    #                 AGKN('%s', 'GNR_ST_NUCL_CND_E-33') = YES;
    #                 AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GWND)  = YES  ;
    #                 AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GHSTO) = YES  ;          
    #                 AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GESTO) = YES  ;          
    #                 AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GESTOS) = YES ;          
    #                 AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GSOLE) = YES  ;          
    #                 AGKN('%s', GGG)$(GDATA(GGG,"GDTYPE") EQ GSOLH) = YES  ;          
    #                 """%tuple(8*[a + '_A']))
    #                 #.replace(' ', '')%tuple(8*[a + '_A']))


if __name__ == '__main__':
    main()
