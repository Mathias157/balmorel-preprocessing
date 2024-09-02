"""
Create electricity demand profiles for Denmark
Use Energinet data for municipalities:
https://www.energidataservice.dk/tso-electricity/consumptionindustry
Convert LAU code to municipality name with: 
LAU – NUTS 2021, EU-27 and EFTA / available candidate countries
https://ec.europa.eu/eurostat/web/nuts/local-administrative-units
Note: The dataset above also contains population

Created on 22.08.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import xarray as xr
from pytz import timezone
from Modules.Submodules.municipal_template import DataContainer
from Modules.Submodules.energinet_electricity import energinet_el

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###   1. Merge Electricity Demand   ###
### ------------------------------- ###

x = DataContainer()
x.muni = x.muni.merge(energinet_el)
for user in x.muni.electricity_demand_mwh.coords['user']:
    fig, ax = plt.subplots()
    x.get_polygons().plot(
        column=x.muni.electricity_demand_mwh.sum(dim=['year', 'week', 'hour']).sel(user=user).data,
        legend=True,
        ax=ax
    ).set_title(str(user.data))

