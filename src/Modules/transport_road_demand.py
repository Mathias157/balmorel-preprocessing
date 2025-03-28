"""
Created on 22.06.2024

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)

ASSUMPTIONS:
- Assumes one demand and charging capacity pr. electric vehicle
- Assumes a uniform distribution of EV demand within country regions (very bad for FR15-FR00 and UK00-UKNI) 
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import os 
import pandas as pd
import numpy as np
import geopandas as gpd
from pybalmorel import IncFile
from geofiles import prepared_geofiles
from Submodules.utils import cmap 
from format_dkstat import load_transport_demand
import matplotlib.pyplot as plt
import xarray as xr
import click

#%% ------------------------------- ###
###   1. Temporal Profile for Road  ###
### ------------------------------- ###

class FlexDem():
    def __init__(self) -> None:
        pass

    def load_traffic_data(self, path: str = './Data/PyPSA-Eur-Sec Data/emobility',
                          file: str = 'KFZ__count'):
        
        # Load PyPSA Data
        self.traffic_count = pd.read_csv(os.path.join(path, file), skiprows=2)
        self.n_vehicles = pd.read_csv(os.path.join(path, 'European_countries_car_ownership.csv'),
                                      skiprows=1, index_col=0)
        self.n_vehicles.columns = ['Cars/1000pop 1995', 'Cars/1000pop 2005', 
                                   'Cars/1000pop 2007', 'Cars/1000pop 2009',
                                    'Cars 1995', 'Cars 2005', 
                                    'Cars 2007', 'Cars 2009',
                                    '1000pop 1995', '1000pop 2005',
                                    '1000pop 2007', '1000pop 2009']


    def create_profile(self, plot: bool = False):
        # Normalise Traffic Count
        f = self.traffic_count.pivot_table(index=['day', 'hour'],
                            values='count')
        f = f / np.max(f)
                
        # Calculate 1 - Normalised Traffic Count
        inv_demand = 1 - f 
        self.inv_demand = inv_demand + (1 - inv_demand.max())

        # Plot
        if plot:
            ax = self.inv_demand.plot(legend=True)
            f.plot(ax=ax, legend=True)
            ax.legend(['1 - Normalised Traffic Count', 'Normalised Traffic Count'], bbox_to_anchor=(.5, 1),
                    loc='lower center', ncols=2)
            plt.show()


    def create_road_demand_from_Nvehicles(self, 
                         demand_pr_vehicle: float = 100*52/1000,
                         charger_capacity_pr_vehicle: float = 1.5):

        # Calculate annual demand
        self.annual_demand_from_Nvehicles = self.n_vehicles['Cars 2009']*demand_pr_vehicle # In MWh
        # print(self.annual_demand)
        
        # Convert to MW
        charger_capacity_pr_vehicle = charger_capacity_pr_vehicle / 1000
        
        # Calculate charging capacity pr. region
        self.charge_cap = self.n_vehicles['Cars 2009']*charger_capacity_pr_vehicle # In MW
        # print(self.charge_cap)
        
        
    def create_road_demand_from_dkstat(self, road_demand: xr.DataArray):
        # Using Danmarks statistik
        self.annual_demand = road_demand.data.sum()
        
        # Look at ratio between the two assumptions:
        # print('Ratio of energy demand from DKSTAT to energy demand from N vehicles:')
        # print(self.annual_demand_from_Nvehicles['Denmark'] / self.annual_demand)


    def create_flexdem_incfiles(self, road_demand: xr.Dataset, area_choice: str = 'dkmunicipalities_names'):
        
        # Load Areas
        the_index, areas, country_code = prepared_geofiles(area_choice)
        
        ### Create Charging Profiles
        # Create Normalised Max Limit on Charging
        FLEXDEM_MAXCONS = IncFile(name='FLEXDEM_FLEXMAXLIMIT',
                                path='Output',
                                prefix="TABLE FLEXMAXLIMIT1(SSS,TTT,FLEXUSER) 'Maximum flexible consumption wrt. season and term (%)'\n",
                                suffix="\n;\nFLEXMAXLIMIT(FLEXUSER, RRR, SSS, TTT) = FLEXMAXLIMIT1('S01',TTT,FLEXUSER);\nFLEXMAXLIMIT1(SSS,TTT,FLEXUSER)=0;\n\n* Scale charger capacities to regions:\n")

        # Make correct index
        ind = pd.MultiIndex.from_product((['S01'], ['T00%d'%i for i in range(1, 10)] + ['T0%d'%i for i in range(10, 100)] + ['T%d'%i for i in range(100, 169)]))
        ind.names = ['S', 'T']
        body = pd.DataFrame(data=self.inv_demand.values, index=ind, columns=['ELECTRIC_VEHICLES']).reset_index()

        # Insert to incfile and prepare
        FLEXDEM_MAXCONS.body = body
        FLEXDEM_MAXCONS.body_prepare(index=['S', 'T'],
                                    columns=None,
                                    values='ELECTRIC_VEHICLES')
        
        
        ### Create Total Demand
        FLEXDEM_FLEXYDEMAND = IncFile(name='FLEXDEM_FLEXYDEMAND',
                                      path='Output',
                                      prefix="TABLE FLEXYDEMAND(YYY,CCCRRRAAA,FLEXUSER) 'Flexible yearly demand node and user (MWh)'\n",
                                      suffix='\n;\n')
        FLEXDEM_FLEXYDEMAND.body = pd.DataFrame(columns=['Value'])
        
        # Scale to country capacities
        # for country in areas[country_code].unique():
        for country in ['Denmark']:
            try:
                print(country, '\nTotal charging capacity:\t%d MW'%(round(self.charge_cap.loc[country])))
                print('\nTotal energy demand:\t%d TWh'%round(self.annual_demand))
                
                # regions = areas[areas[country_code]==country].index
                regions = areas.index
                N_regions = len(regions) # Making an even distribution
                for region in regions:
                    
                    # Uniform distribution of charger capacities
                    FLEXDEM_MAXCONS.suffix += "FLEXMAXLIMIT('ELECTRIC_VEHICLES', '%s', SSS, TTT) = %0.2f*FLEXMAXLIMIT('ELECTRIC_VEHICLES', '%s', SSS, TTT);\n"%(region, self.charge_cap.loc[country]*road_demand.sel({the_index : region}).data / self.annual_demand, region)
                
                    # Uniform distribution of demand
                    FLEXDEM_FLEXYDEMAND.body.loc[region, 'Value'] = road_demand.sel({the_index : region}).data * 1e6 # MWh
                
            except KeyError:
                print('No EV data in %s'%country)
                    
        FLEXDEM_MAXCONS.save()
        
        FLEXDEM_FLEXYDEMAND.body['Year'] = '2050'
        FLEXDEM_FLEXYDEMAND.body['User'] = 'ELECTRIC_VEHICLES'
        FLEXDEM_FLEXYDEMAND.body.index.name = 'Region'
        FLEXDEM_FLEXYDEMAND.body_prepare(index=['Year', 'Region'],
                                         columns='User',
                                         values='Value')
        
        # Linear extrapolation down to 2030
        FLEXDEM_FLEXYDEMAND.suffix += "FLEXYDEMAND('2040',CCCRRRAAA,FLEXUSER) = 0.67*FLEXYDEMAND('2050',CCCRRRAAA,FLEXUSER);\n"
        FLEXDEM_FLEXYDEMAND.suffix += "FLEXYDEMAND('2030',CCCRRRAAA,FLEXUSER) = 0.33*FLEXYDEMAND('2050',CCCRRRAAA,FLEXUSER);\n"
        FLEXDEM_FLEXYDEMAND.save()


#%% ------------------------------- ###
###        2. Spatial Spread        ###
### ------------------------------- ###

def distribute_road_flex_electricity_demand(plot: bool, choice: str = 'dkmunicipalities_names'):
    # 2.1 Vehicle Counts on Roads from Ioannis' source 
    f = gpd.read_file('Data/Gas, Transport and Industry Data/gdf_all_ETISplus.geojson')

    id, geo, c = prepared_geofiles(choice)
    
    if plot: 
        fig, ax = plt.subplots()
        geo.plot(ax=ax, facecolor=[.6, .6, .6])
        f.plot(ax=ax, color=[.8, .1, .1], linewidth=f.vehicles/1e4)
        bounds = geo.total_bounds
        ax.set_xlim([bounds[0], bounds[2]])
        ax.set_ylim([bounds[1], bounds[3]])
        ax.axes.set_axis_off()
        fig.savefig('Output/Figures/traffic-gis-data.png', transparent=True)
    
    geo['traffic_count'] = 0
    for i, row in f.iterrows():
        idx = row.geometry.intersects(geo.geometry)
        muni = geo.loc[idx]
        if len(muni) != 0:
            for mun in muni.index:
                geo.loc[mun, 'traffic_count'] += float(row.vehicles) / len(muni.index)
            # print('%d intersects %d'%(i, muni.index))
    
    return geo

def distribute_dkstat_demand(geo: gpd.GeoDataFrame,
                      plot: bool = False):
    # National Transport Fuel Demand
    f = load_transport_demand(include_bunkering=False)
    # print(f)

    ## I choose road demand from 2019 since it seems in the average (assuming no change in mobility demand, avoiding too many electric vehicles)
    year = 2019
    road_demand_twh = f.loc[['Motorbenzin, blyfri (fra 2016 inkl. farvet benzin)',
                        'Diesel til vejtransport'], str(year)].sum()

    ## Distribute
    geo['flex_electricity_demand_twh'] = (
        geo.traffic_count
        # Normalise traffic count, so it can be used as distribution key
        .div(geo.traffic_count.sum())
        .mul(road_demand_twh)
        # Convert from ICE efficiency to mobility demand
        .mul(0.36)
        # Convert from mobility demand to electric demand
        .div(0.9)
    )
    
    if plot:
        ## Plot yearly tendencies
        fig, ax = plt.subplots()
        f.T.plot(ax=ax)
        ax.set_ylabel('Dansk Brændstofforbrug (TWh)')
        ax.legend(loc='center', bbox_to_anchor=(.5, 1.15))
        
        ## Plot distribution of demand
        fig2, ax2 = plt.subplots()
        geo.plot(ax=ax2, column='flex_electricity_demand_twh', cmap=cmap, legend=True)
        ax2.set_title('Semi-Flexible Electricity Demand for EVs (TWh)')
        ax2.axes.set_axis_off()
        fig2.savefig('Output/Figures/road-el-demand.png', transparent=True)

    road_demand = geo['flex_electricity_demand_twh'].to_xarray()
    road_demand = road_demand.assign_coords(year=year, user='road')
    print(road_demand.sel(NAME_2='Aabenraa').data, ' TWh')
    return road_demand


@click.command()
@click.option('--chargercap', type=float, required=True, help="Charging capacity in kW pr. vehicle")
@click.option('--plot-only', is_flag=True, default=False, help="Only plot")
def main(chargercap: float, plot_only: bool):
    # Distribute road demand to municipalities using the transport study
    geo = distribute_road_flex_electricity_demand(plot_only)
    road_demand = distribute_dkstat_demand(geo, plot_only)
    
    if not(plot_only):
        # Create demands
        FD = FlexDem()
        FD.load_traffic_data()
        FD.create_profile(plot=False)
        FD.create_road_demand_from_Nvehicles(charger_capacity_pr_vehicle=chargercap)
        FD.create_road_demand_from_dkstat(road_demand)
        FD.create_flexdem_incfiles(road_demand)


if __name__ == '__main__':
    main()