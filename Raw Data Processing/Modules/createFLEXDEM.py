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
from pybalmorel import IncFile
from pybalmorel.functions import read_lines
from Modules.geofiles import prepared_geofiles


#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

class FlexDem():
    def __init__(self) -> None:
        pass

    def load_traffic_data(self, path: str = r'Data\PyPSA-Eur-Sec Data\emobility',
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

    def create_general_demand(self, 
                         demand_pr_vehicle: float = 100*52/1000,
                         charger_capacity_pr_vehicle: float = 1.5/1000):
        
        # Normalise Traffic Count
        f = self.traffic_count.pivot_table(index=['day', 'hour'],
                            values='count')
        f = f / np.max(f)
                
        # Calculate 1 - Normalised Traffic Count
        inv_demand = 1 - f 
        self.inv_demand = inv_demand + (1 - inv_demand.max())

        # Plot
        ax = self.inv_demand.plot(legend=True)
        f.plot(ax=ax, legend=True)
        ax.legend(['1 - Normalised Traffic Count', 'Normalised Traffic Count'], bbox_to_anchor=(.5, 1),
                  loc='lower center', ncols=2)

        # Calculate annual demand
        self.annual_demand = self.n_vehicles['Cars 2009']*demand_pr_vehicle # In MWh
        
        # Calculate charging capacity pr. region
        self.charge_cap = self.n_vehicles['Cars 2009']*charger_capacity_pr_vehicle # In MW
        

    def create_charging_profile(self, area_choice: str = 'AntBalm'):
        
        # Load Areas
        the_index, areas, country_code = prepared_geofiles(area_choice)
        
        ### Create Charging Profiles
        # Create Normalised Max Limit on Charging
        FLEXDEM_MAXCONS = IncFile(name='FLEXDEM_MAXLIMIT',
                                path='Output',
                                prefix=read_lines('FLEXDEM_MAXLIMIT_prefix.inc', r'Data\IncFilePreSuf'),
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
        for country in areas[country_code].unique():
            try:
                print(country, 'total:\t%d MW'%(round(self.charge_cap.loc[country])))
                
                regions = areas[areas[country_code]==country].index
                N_regions = len(regions)
                for region in regions:
                    print(region, len(regions))
                    
                    # Uniform distribution of charger capacities
                    FLEXDEM_MAXCONS.suffix += "FLEXMAXLIMIT('ELECTRIC_VEHICLES', '%s', SSS, TTT) = %0.2f*FLEXMAXLIMIT('ELECTRIC_VEHICLES', '%s', SSS, TTT);\n"%(region, self.charge_cap.loc[country]/N_regions, region)
                
                    # Uniform distribution of demand
                    FLEXDEM_FLEXYDEMAND.body.loc[region, 'Value'] = self.annual_demand.loc[country] / N_regions 
                
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


FD = FlexDem()
FD.load_traffic_data()
FD.create_general_demand()
FD.create_charging_profile()