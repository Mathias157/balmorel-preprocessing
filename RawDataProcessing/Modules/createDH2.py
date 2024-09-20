"""
TITLE

Description

Created on 20.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
from Submodules.municipal_template import DataContainer
try:
    import cmcrameri
    cmap = cmcrameri.cm.cmaps['roma_r']
    cmap = cmcrameri.cm.cmaps['vik']
    colors = [cmap(i) for i in range(256)]
except ModuleNotFoundError:
    print('cmrameri package not installed, using default colourmaps')
    cmap = matplotlib.colormaps['viridis']
    colors = [cmap(i) for i in range(256)]

style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###          1. Data Class          ###
### ------------------------------- ###

class DistrictHeatAAU:
    def __init__(self) -> None:
        self.district_heat = xr.load_dataset('Data/AAU Kommuneplan/districtheat_exo_heatdem.nc')
        self.industry = xr.load_dataset('Data/AAU Kommuneplan/industry_exo_heatdem.nc')
        self.annual_industry_demand = xr.load_dataset('Data/Danmarks Statistik/industry_demand.nc')
        
    def combine_data(self, plot: bool = False):
        data = DataContainer()
        data.muni = data.muni.merge(self.district_heat)
        data.muni = data.muni.merge(self.industry)
        data.muni = data.muni.merge(self.annual_industry_demand)


        ## Get industry demands per municipality, per heat type 
        data.muni.heat_demand_mwh.loc[{'user': 'industry_phl'}] = data.muni.heat_demand_normalised.sel(year=2019, user='industry_phl') * data.muni.energy_demand_type_mwh.sel(year=2018, user='other') / data.muni.energy_demand_type_mwh.sel(year=2018).sum() * data.muni.energy_demand_mun_mwh.sel(year=2018)
        data.muni.heat_demand_mwh.loc[{'user': 'industry_phm'}] = data.muni.heat_demand_normalised.sel(year=2019, user='industry_phm') * data.muni.energy_demand_type_mwh.sel(year=2018, user='other') / data.muni.energy_demand_type_mwh.sel(year=2018).sum() * data.muni.energy_demand_mun_mwh.sel(year=2018)
        data.muni.heat_demand_mwh.loc[{'user': 'industry_phh'}] = data.muni.heat_demand_normalised.sel(year=2019, user='industry_phh') * data.muni.energy_demand_type_mwh.sel(year=2018, user='other') / data.muni.energy_demand_type_mwh.sel(year=2018).sum() * data.muni.energy_demand_mun_mwh.sel(year=2018)

        ## Drop year 2018, user electricity, other and district heat from industry data
        data.muni = data.muni.drop_vars(['energy_demand_mun_mwh',
                        'energy_demand_type_mwh',
                        'heat_demand_normalised'])
        data.muni = data.muni.sel(year=[2019], user=['district_heating', 'individual',
                                    'industry_phl', 'industry_phm', 'industry_phh'])

        self.data = data.muni

        if plot:
            # Plot it
            temp = data.muni.heat_demand_mwh.sel(year=2019, user='district_heating').data
            temp += data.muni.heat_demand_mwh.sel(year=2019, user='individual').data
            temp += data.muni.heat_demand_mwh.sel(year=2019, user='industry_phl').data.astype(float)
            temp += data.muni.heat_demand_mwh.sel(year=2019, user='industry_phm').data.astype(float)
            temp += data.muni.heat_demand_mwh.sel(year=2019, user='industry_phh').data.astype(float)

            fig, ax = plt.subplots()
            data.get_polygons().plot(ax=ax,
                                    column=temp,
                                    cmap=cmap,
                                    vmin=0,
                                    vmax=6e6,
                                    legend=True).set_title('sum')
            fig.savefig(f'Output/Figures/Heat/total_heatdemand.png',
                        transparent=True,
                        bbox_inches='tight')
            
            for user in ['district_heating', 'individual', 'industry_phl',
                        'industry_phm', 'industry_phh']:
                fig, ax = plt.subplots()
                a = data.get_polygons().plot(ax=ax,
                                            cmap=cmap,
                                            vmin=0,
                                            vmax=6e6,
                                            column=data.muni.heat_demand_mwh.sel(year=2019, user=user).data,
                                            legend=True).set_title(user)
                fig.savefig(f'Output/Figures/Heat/{user}_heatdemand.png',
                            transparent=True,
                            bbox_inches='tight')

if __name__ == '__main__':
    a = DistrictHeatAAU()
    a.combine_data()
    print(a.data)