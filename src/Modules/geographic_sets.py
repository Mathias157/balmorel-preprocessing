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
###          1. Utilities           ###
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
    
    ## Add loading of offshore sets
    for file in ['CCCRRRAAA', 'RRRAAA', 'AAA']:
        with open('Output/%s.inc'%file, 'a+') as f:
            # content = f.read()
            f.write("\n".join([
                "",
                '$onmulti',
                f"$if     EXIST '../data/OFFSHORE_{file}.inc' $INCLUDE '../data/OFFSHORE_{file}.inc';",
                f"$if not EXIST '../data/OFFSHORE_{file}.inc' $INCLUDE '../../base/data/OFFSHORE_{file}.inc';",                          
                '$offmulti',
            ]))
    
    
    # 1.2 Create INDUSTRY sets
    f = combine_dicts([
        load_set('ind-lt_sets'),
        load_set('ind-mt_sets'),
        load_set('ind-ht_sets')
    ])
    create_incfiles(str(format_set(f, 3)), 'Output', 'INDUSTRY_')
    # Make INDUSTRY_INDUSTRY_AAA.inc
    with open('Output/INDUSTRY_AAA.inc', 'r') as f:
        file = f.read()
    file = file.replace("SET AAA(CCCRRRAAA)  'All areas'", "SET INDUSTRY_AAA(CCCRRRAAA)  'All areas'")
    with open('Output/INDUSTRY_INDUSTRY_AAA.inc', 'w') as f:
        f.write(file)
    
    # 1.3 Create INDIVUSERS sets
    f = combine_dicts([load_set('individual_sets')])
    create_incfiles(str(format_set(f, 1)), 'Output', 'INDIVUSERS_')
    # Make INDIVUSERS_INDIVUSERS_AAA.inc
    with open('Output/INDIVUSERS_AAA.inc', 'r') as f:
        file = f.read()
    file = file.replace("SET AAA(CCCRRRAAA)  'All areas'", "SET INDIVUSERS_AAA(CCCRRRAAA)  'Individual user areas'")
    with open('Output/INDIVUSERS_INDIVUSERS_AAA.inc', 'w') as f:
        f.write(file)
    

#%% ------------------------------- ###
###             2. Main             ###
### ------------------------------- ###

if __name__ == '__main__':
    main()
