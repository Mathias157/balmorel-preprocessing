"""
Creating input for transport hydrogen demand

Simple assumptions:
- Just assuming that there's a hydrogen demand where ports are (but will jet fuel be produced here as well? Will shipping fuel?)
- Making a fixed assumption on H2/fuel efficiency from my 2024 paper
    E.g. for jet fuel:
        TG-FT:      No hydrogen demand (need to account for bio consumption!)
        TG-FT-H2:   34/55.4=0.614 MWh hydrogen / MWh jet fuel (need to account for bio consumption!)
        eFT:        100/42 =2.381 MWh hydrogen / MWh jet fuel (need to account for CCU consumption!)
    For shipping fuel:
        TG-MeOH:    33.8/82=0.412 MWh hydrogen / MWh MeOH (need to account for bio consumption!)
        eMeOH:      100/119=0.840 MWh hydrogen / MWh MeOH (need to account for CCU consumption!)
        eNH3:       100/86 =1.163 MWh hydrogen / MWh NH3

Created on 27.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import pandas as pd
from pybalmorel import IncFile
import click
from format_dkstat import load_transport_demand

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

def simple_assumptions(meoh_per_jetfuel: float,
                       year: int):
    
    
    # Load DKSTAT
    f  = load_transport_demand(include_bunkering=False) * 1e6 # MWh
    
    # Jet fuel
    jet_dem = f.loc['Jetpetroleum (fra 2016 inkl. flybenzin)', str(year)] / meoh_per_jetfuel

    # Shipping fuel
    ship_dem = f.loc['Fuelolie', str(year)]
    
    return jet_dem, ship_dem


#%% ------------------------------- ###
###            X. Main              ###
### ------------------------------- ###

@click.command()
@click.option('--meoh-per-jetfuel', type=float, required=True, help='Ratio of hydrogen demand in MWh per produced jet fuel in MWh')
@click.option('--jetfuel-demand', type=float, required=True, help='Jetfuel demand in MWh')
@click.option('--shipping-demand', type=float, required=True, help='Shipping fuel demand in MWh')
@click.option('--use-dkstat', is_flag=True, required=False, help="Use data from Danmarks statistik?")
@click.option('--year', type=int, required=False, default=2019, help='Year to collect demand from')
def main(meoh_per_jetfuel: float, jetfuel_demand: float, shipping_demand: float, use_dkstat: bool, year: int):

    if use_dkstat:
        jetfuel_demand, shipping_demand = simple_assumptions(meoh_per_jetfuel, jetfuel_demand, shipping_demand, year) 
    
    f = IncFile(name='HYDROGEN_SYNFUELDEMAND', path='Output',
                prefix="\n".join([
                    "TABLE SYNFUELDEMAND(YYY, SYNFUELUSER) 'Annual synthfuel demand in MWh'",
                    ""
                ]),
                body=pd.DataFrame({'TOTAL' : jetfuel_demand + shipping_demand, 'AVIATION' : jetfuel_demand}, index=[2050]),
                suffix="\n".join([
                    "",
                    ";",              
                ]))
    f.save()
    

if __name__ == '__main__':
    main()
