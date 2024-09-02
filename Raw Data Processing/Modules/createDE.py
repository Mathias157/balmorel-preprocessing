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
from Modules.Submodules.municipal_template import DataContainer

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

# Read municipality timeseries
f = pd.read_csv(r'Data\Timeseries\ElConsumptionEnerginet2023.csv', sep=';', decimal=',')

# Read code to translate municipality into name
codes = pd.read_excel(r'Data\Timeseries\EU-27-LAU-2023-NUTS-2021.xlsx', sheet_name='DK')

# Merge the codes dataframe with the f dataframe
f = pd.merge(f, codes, left_on='MunicipalityNo', right_on='LAU CODE')


x = DataContainer()

# %%

f2 = f.rename(columns={
    'LAU NAME NATIONAL' : 'municipality',
    'Branche' : 'user',
    'HourUTC' : 'time',
    'ConsumptionkWh' : 'electricity_demand_mwh'
}).pivot_table(index=['municipality', 'user', 'time'],
                  values='electricity_demand_mwh',
                  aggfunc=lambda x: np.mean(x)/1e3)


# %% 

f3 = f2.to_xarray()
f3 = xr.Dataset(        
    {
        "energy_demand_mun_mwh" : (
            ('year', 'municipality', 'user', 'time'),
            np.expand_dims(f3.electricity_demand_mwh.data, axis=0)
        ) 
    },
    coords={'year' : [2022],
            'municipality' : f3.coords['municipality'],
            'user' : f3.coords['user'],
            'time' : f3.coords['time']
    }
)

x.muni = x.muni.merge(f3)

#%%

for user in x.muni.electricity_demand_mwh.coords['user']:
    fig, ax = plt.subplots()
    x.get_polygons().plot(
        column=x.muni.electricity_demand_mwh.sum(dim='time').sel(user=user).data,
        legend=True,
        ax=ax
    ).set_title(str(user.data))

