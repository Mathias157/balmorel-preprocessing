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

def simple_assumptions(h2_demand_per_jetfuel_mwh: float,
                       h2_demand_per_shipfuel_mwh: float,
                       year: int = 2019):
    
    
    # Load DKSTAT
    f  = load_transport_demand(include_bunkering=False) * 1e6 # MWh
    
    # Jet fuel
    jet_dem = f.loc['Jetpetroleum (fra 2016 inkl. flybenzin)', str(year)] * h2_demand_per_jetfuel_mwh

    # Shipping fuel
    ship_dem = f.loc['Fuelolie', str(year)] * h2_demand_per_shipfuel_mwh
    
    return jet_dem, ship_dem

def allocate_demand(national_h2_demand: float, year: int, distribution: dict):
    
    f = IncFile(name='TRANSPORT_TRANSDEMAND_Y', path='Output',
                prefix="\n".join([
                    "TABLE  TRANSDEMAND_Y1(RRR,YYY)   'Annual transport demand (MWh)'",
                    "* Simple assumptions on fixed conversion efficiencies to jet and shipping fuel, and that fuel is produced near ports",
                    ""
                ]),
                suffix="\n".join([
                    "",
                    ";",
                    "TRANSDEMAND_Y(YYY,RRR)  = TRANSDEMAND_Y1(RRR,YYY)*%0.4f; "%national_h2_demand,
                    "TRANSDEMAND_Y1(RRR,YYY)=0;",
                                        
                ]))
    
    f.body = pd.DataFrame(data=distribution, index=[year]).T.to_string()
    f.save()
    

#%% ------------------------------- ###
###            X. Main              ###
### ------------------------------- ###

@click.command()
@click.option('--h2-demand-per-jetfuel-mwh', type=float, required=True, help='Ratio of hydrogen demand in MWh per produced jet fuel in MWh')
@click.option('--h2-demand-per-shipfuel-mwh', type=float, required=True, help='Ratio of hydrogen demand in MWh per produced shipping fuel in MWh')
def main(h2_demand_per_jetfuel_mwh: float, h2_demand_per_shipfuel_mwh: float):
    jet_dem, ship_dem = simple_assumptions(h2_demand_per_jetfuel_mwh, h2_demand_per_shipfuel_mwh) 
    
    allocate_demand(jet_dem + ship_dem, 2050, {'Esbjerg' : 0.4,
                                               'Frederikshavn' : 0.3,
                                               'Fredericia' : 0.3})

if __name__ == '__main__':
    main()
