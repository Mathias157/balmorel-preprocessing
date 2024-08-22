"""
Create electricity demand profiles for Denmark
Use Energinet data for municipalities:
https://www.energidataservice.dk/tso-electricity/consumptionindustry

Created on 22.08.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

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


f = pd.read_csv(r'Data\Timeseries\ElConsumptionEnerginet2023.csv', sep=';', decimal=',')


