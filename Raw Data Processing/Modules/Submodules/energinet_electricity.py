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

from pybalmorel import IncFile
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import xarray as xr
from pytz import timezone
from Modules.Submodules.municipal_template import DataContainer
from Modules.Submodules.utils import convert_coordname_elements

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
### 1. Load & Format Energinet Data ###
### ------------------------------- ###

# Read municipality timeseries
f = pd.read_csv(r'Data\Timeseries\ElConsumptionEnerginet2023.csv', sep=';', decimal=',')

## Record Timezone (UTC, i.e. similar to GMT)
time = pd.to_datetime(f.HourUTC) 
time = (
    time
    .dt.tz_localize(timezone('UTC'))
    .dt.tz_convert(timezone('GMT'))
)
## Convert time 
t = pd.DataFrame(
    {
        'year' : time.dt.year,
        'week' : time.dt.isocalendar().week.astype('int32'),
        'day' : time.dt.day_of_week + 1,
        'month' : time.dt.month,
        'hourclock' : time.dt.hour + 1
    }
)

## Create Balmorel friendly time
t['hour'] = t.day * 24 + t.hourclock - 24

## Merge
f = f.merge(t, left_index=True, right_index=True).query(
    'year == 2023 and not (week == 52 and month == 1)'
)

# Read code to translate municipality into name
codes = pd.read_excel(r'Data\Timeseries\EU-27-LAU-2023-NUTS-2021.xlsx', sheet_name='DK')

# Merge the codes dataframe with the f dataframe
f = f.merge(codes, left_on='MunicipalityNo', right_on='LAU CODE')

# Rename columns and choose only necessary columns
f2 = f.rename(columns={
    'LAU NAME NATIONAL' : 'municipality',
    'Branche' : 'user',
    'ConsumptionkWh' : 'electricity_demand_mwh'
})

f2['user'] = f2.user.replace({'Erhverv' : 'industry',
            'Offentligt' : 'public',
            'Privat' : 'residential'})
f2 = f2.pivot_table(index=['municipality', 'user', 'year', 'week', 'hour'],
                  values='electricity_demand_mwh') 

# Convert to xarray
energinet_el = f2.to_xarray()
energinet_el.electricity_demand_mwh.data = energinet_el.electricity_demand_mwh.data / 1e3 # to MWh


if __name__ == '__main__':
    # Example on merging with other data
    x = DataContainer()
    x.muni = x.muni.merge(energinet_el)


    for user in x.muni.electricity_demand_mwh.coords['user']:
        fig, ax = plt.subplots()
        x.get_polygons().plot(
            column=x.muni.electricity_demand_mwh.sum(dim=['year', 'week', 'hour']).sel(user=user).data,
            legend=True,
            ax=ax
        ).set_title(str(user.data))


    dataset = convert_coordname_elements(energinet_el,
                        'electricity_demand_mwh',
                        {'municipality' : 'R',
                            'user' : 'DEUSER',
                            'year' : 'Y',
                        'week' : 'S',
                        'hour' : 'T'},
                        {'user' : {'industry' : 'PII',
                                    'public' : 'OTHER',
                                    'residential' : 'RESE'}})
