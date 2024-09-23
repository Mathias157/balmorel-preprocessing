"""
Created on 17.03.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely import Point
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
XH2INVCOST = 0.55    # €/MW - new onshore pipe 
# XH2INVCOST = 0.9    # €/MW - new offshore pipe
# XH2INVCOST = 0.15   # €/MW - repurposed onshore pipe
# XH2INVCOST = 0.2    # €/MW - repurposed offshore pipe


class Hydrogen:
    
    def __init__(self, choice: str) -> None:
        
        # Read pre-calculated distances
        self.grid = pd.read_parquet('Data/Shapefiles/Distances/%s_Distances.gzip'%choice.upper()) 

        # Gas storage DK1
        self.gasstorage = gpd.GeoDataFrame({'geometry' : Point(9.416895889014997, 56.64039606410427)},
                                       index=['Lille Torup'], crs='EPSG:4326')
        

    def create_hydrogen_data(self, areas: gpd.GeoDataFrame, the_index: str) -> dict:
        
        incfiles = {}
        incfilenames = ['HYDROGEN_XH2INVCOST',
                        'HYDROGEN_XH2LOSS',
                        'HYDROGEN_AGKN'] 
        
        for name in incfilenames:
            incfiles[name] = IncFile(name=name,
                                    path='Output',
                                    body=pd.DataFrame(),
                                    prefix=read_lines(name+'_prefix.inc',
                                                      file_path='Data/IncFilePreSuf'),
                                    suffix=read_lines(name+'_suffix.inc',
                                                      file_path='Data/IncFilePreSuf'))

        # Make investment and loss 
        incfiles['HYDROGEN_XH2INVCOST'].body = self.grid[self.grid.Y == '2050']
        incfiles['HYDROGEN_XH2LOSS'].body = self.grid[self.grid.Y == '2050']
        incfiles['HYDROGEN_XH2INVCOST'].body.loc[:, 'Value'] = incfiles['HYDROGEN_XH2INVCOST'].body['Value']*XH2INVCOST
        incfiles['HYDROGEN_XH2LOSS'].body.loc[:, 'Value']    = incfiles['HYDROGEN_XH2LOSS'].body['Value']*XH2LOSS 
        incfiles['HYDROGEN_XH2INVCOST'].body.loc[:, 'Y'] = incfiles['HYDROGEN_XH2INVCOST'].body['Y'].str.replace('2050', '2030')
        incfiles['HYDROGEN_XH2LOSS'].body.loc[:, 'Y']    = incfiles['HYDROGEN_XH2LOSS'].body['Y'].str.replace('2050', '2030') 

        # Find salt-cavern investment option
        saltcavern = areas[areas.geometry.contains(self.gasstorage.geometry[0])][the_index].iloc[0]
        incfiles['HYDROGEN_AGKN'].body = "AGKN('%s_A', 'GNR_H2S_H2-CAVERN_Y-2030') = YES;\n"%saltcavern
        incfiles['HYDROGEN_AGKN'].body = "AGKN('%s_A', 'GNR_H2S_H2-CAVERN_Y-2040') = YES;\n"%saltcavern
        incfiles['HYDROGEN_AGKN'].body = "AGKN('%s_A', 'GNR_H2S_H2-CAVERN_Y-2050') = YES;\n"%saltcavern
        
        return incfiles


