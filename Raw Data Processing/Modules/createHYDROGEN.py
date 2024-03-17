"""
Created on 17.03.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pybalmorel.functions import IncFile, read_lines

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

# From Kountouris et al 2024
XH2LOSS = 2.5e-08   # MWh/Mwh
XH2COST = 1e-6      # €/Mwh
XH2INVCOST = 0.3    # €/MW - new onshore pipe 
# XH2INVCOST = 0.5    # €/MW - new offshore pipe
# XH2INVCOST = 0.01   # €/MW - repurposed onshore pipe
# XH2INVCOST = 0.2    # €/MW - repurposed offshore pipe


class Hydrogen:
    
    def __init__(self, choice: str) -> None:
        
        # Read pre-calculated distances
        self.grid = pd.read_parquet('Data/Shapefiles/Distances/%s_Distances.gzip'%choice.upper()) 

    def create_hydrogen_data(self):
        
        incfiles = {}
        incfilenames = ['HYDROGEN_XH2COST', 'HYDROGEN_XH2INVCOST',
                        'HYDROGEN_XH2LOSS', 'HYDROGEN_DISLOSS_H2',
                        'HYDROGEN_AGKN'] 
        for name in incfilenames:
            incfiles[name] = IncFile(name=name,
                                    path='Output',
                                    body=pd.DataFrame(),
                                    prefix=read_lines(name+'_prefix.inc',
                                                      file_path='Data/IncFilePreSuf'),
                                    suffix=read_lines(name+'_suffix.inc',
                                                      file_path='Data/IncFilePreSuf'))
        

   
H2 = Hydrogen('NUTS2') 

#%%
the_index, areas, c = prepared_geofiles('nuts3')

#%%


