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
from numpy import array
from matplotlib import colormaps
import pandas as pd
from pytz import timezone
from Submodules.municipal_template import DataContainer
from Submodules.utils import convert_coordname_elements, cmap
import click


#%% ------------------------------- ###
### 1. Load & Format Energinet Data ###
### ------------------------------- ###

@click.command()
@click.option('--plot-only', is_flag=True, default=False, help="Only output a plot")
@click.option('--plot-each-user', is_flag=True, default=False, help="Plot each user? Else, total will be plotted")
@click.option("--energinet-data-path", type=str, required=True, help="Path of data from https://www.energidataservice.dk/tso-electricity/consumptionindustry")
def main(energinet_data_path: str, plot_only: bool, plot_each_user: bool):
    # Read municipality timeseries
    f = pd.read_csv(energinet_data_path, sep=';', decimal=',')

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
    codes = pd.read_excel('Data/Timeseries/EU-27-LAU-2023-NUTS-2021.xlsx', sheet_name='DK')

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

    if plot_only:
        # Example on merging with other data
        x = DataContainer()
        x.muni = x.muni.merge(energinet_el)

        if plot_each_user:
            for user in x.muni.electricity_demand_mwh.coords['user']:
                fig, ax = plt.subplots()
                x.get_polygons().plot(
                    column=x.muni.electricity_demand_mwh.sum(dim=['year', 'week', 'hour']).sel(user=user).data,
                    legend=True,
                    ax=ax,
                    vmin=0,
                    vmax=1.5e6
                ).set_title(str(user.data))
                ax.axes.set_axis_off()
                fig.savefig('Output/Figures/exo_el_demand_%s.png'%str(user.values))
        else:
            fig, ax = plt.subplots()
            x.get_polygons().plot(
                column=x.muni.electricity_demand_mwh.sum(dim=['year', 'week', 'hour', 'user']).data / 1e6,
                legend=True,
                cmap=cmap,
                ax=ax
            ).set_title('Exogenous Electricity Demand (TWh)')
            ax.axes.set_axis_off()
            fig.savefig('Output/Figures/exo_el_demand_total.png')
        
    else:
        energinet_el.to_netcdf('Data/Timeseries/energinet_eldem.nc')

if __name__ == '__main__':
    main()