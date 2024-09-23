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
from pybalmorel import IncFile
import textwrap
import xarray as xr
from Submodules.utils import convert_names, transform_xrdata
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
    heat = DistrictHeatAAU()
    heat.combine_data()
    dataset = heat.data
    
    # 1.1 Format Dataset
    conversion_file = 'Modules/Submodules/exo_heat_dem_conversion_dictionaries.pkl'
    dataset, new_dataset = convert_names(conversion_file, dataset, 'heat_demand_mwh')
    
    ## Drop dimensions
    new_dataset = (
        new_dataset
        .drop_dims(['lat', 'lon'])
        .drop_vars('polygons')
    )
    
    show_difference = True
    if show_difference:
        print('Before: \n', dataset, '\n\n')
        print('After: \n', new_dataset, '\n\n')
        
    # 1.2 Make .inc-files
    out_path = 'Output'
    ## 1.2.1 DH.inc
    DH = IncFile(name='DH',
        prefix=textwrap.dedent("""* Data from Varmeplan 2021 (AAU)
        PARAMETER DH(YYY,AAA,DHUSER)  'Annual brutto heat consumption';
        TABLE DH1(DHUSER,AAA,YYY)   
        """),
        suffix=textwrap.dedent("""
        ;
        DH(YYY,AAA,DHUSER)  = DH1(DHUSER,AAA,YYY);                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
        DH1(DHUSER,AAA,YYY) = 0;
        DH('2050',AAA,DHUSER) = DH('2019', AAA, DHUSER);
        """),
        path=out_path
    )
    DH.body = (
        transform_xrdata(new_dataset,
                        'heat_demand_mwh',
                        {'DHUSER' : 'RESH'})
        .to_dataframe()
        .reset_index()
    ) 
    print('Total district heating demand: ', round(DH.body['heat_demand_mwh'].sum() / 1e6, 2) , ' TWh')
    ### Assign area suffix
    DH.body.A = DH.body.A + '_A'
    DH.body_prepare(['DHUSER', 'A'],
                    'Y',
                    values='heat_demand_mwh')
    DH.save()
    
    ## 1.2.2 INDUSTRY_DH.inc
    INDUSTRY_DH = IncFile(name='INDUSTRY_DH',
        prefix=textwrap.dedent("""* Data from Varmeplan 2021 (AAU), Danmarks statistik on industrial energy consumption pr. type
        PARAMETER DH(YYY,AAA,DHUSER)  'Annual brutto heat consumption';
        TABLE DH1_IND(DHUSER,AAA,YYY)  
        """),
        suffix=textwrap.dedent("""
        ;
        DH(YYY,AAA,DHUSER)$DH1_IND(DHUSER,AAA,YYY)  = DH1_IND(DHUSER,AAA,YYY);
        DH('2050',AAA,DHUSER)$DH1_IND(DHUSER,AAA,'2019') = DH('2019', AAA, DHUSER)$DH1_IND(DHUSER,AAA,'2019');
        DH1_IND(DHUSER,AAA,YYY)=0;
        """),
        path=out_path
    )
    INDUSTRY_DH.body = (
        transform_xrdata(new_dataset,
                        'heat_demand_mwh',
                        {'DHUSER' : ['IND-PHL',
                                     'IND-PHM',
                                     'IND-PHH']})
        .to_dataframe()
        .reset_index()
    ) 
    print('Total industry process heat demand: ', round(INDUSTRY_DH.body['heat_demand_mwh'].sum() / 1e6, 2) , ' TWh')
    ### Assign area suffix
    idx = INDUSTRY_DH.body.query('DHUSER == "IND-PHL"').index
    INDUSTRY_DH.body.loc[idx, 'A'] = INDUSTRY_DH.body.loc[idx, 'A'].values + '_IND-LT-NODH'
    idx = INDUSTRY_DH.body.query('DHUSER == "IND-PHM"').index
    INDUSTRY_DH.body.loc[idx, 'A'] = INDUSTRY_DH.body.loc[idx, 'A'].values + '_IND-MT-NODH'
    idx = INDUSTRY_DH.body.query('DHUSER == "IND-PHH"').index
    INDUSTRY_DH.body.loc[idx, 'A'] = INDUSTRY_DH.body.loc[idx, 'A'].values + '_IND-HT-NODH'
    INDUSTRY_DH.body_prepare(['DHUSER', 'A'],
                    'Y',
                    values='heat_demand_mwh')
    INDUSTRY_DH.save()
    
    ## 1.2.3 INDIVUSERS_DH.inc
    INDIVUSERS_DH = IncFile(name='INDIVUSERS_DH',
        prefix=textwrap.dedent("""* Data from Varmeplan 2021 (AAU)
        TABLE DH1_INDIVHEATING(DHUSER,AAA,YYY) 
        """),
        suffix=textwrap.dedent("""
        ;              
        INDIVHEATING_GROUP_DHSHARE(YYY,DHUSER,RRR,INDIVUSERS_GROUP)$(NOT INDIVHEATING_GROUP_DHSHARE(YYY,DHUSER,RRR,INDIVUSERS_GROUP))=                                                         INDIVHEATING_GROUP_DHSHARE('2016',DHUSER,RRR,INDIVUSERS_GROUP);                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
        LOOP(INDIVUSERS_GROUP$(NOT INDIVUSERS_GROUP_NEW(INDIVUSERS_GROUP)),                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
        DH1_INDIVHEATING_GROUP(DHUSER,AAA,YYY)$(INDIVUSERS_GROUP_A(AAA,DHUSER,INDIVUSERS_GROUP)  AND INDIVUSERS_DEMANDTYPE_A(AAA,DHUSER,'HOTWATER') AND INDIVUSERS_DHUSER(DHUSER) ) =          SUM(RRR$RRRAAA(RRR,AAA),INDIVHEATING_GROUP_DHSHARE(YYY,DHUSER,RRR,INDIVUSERS_GROUP)*SUM(IAAA_INDIV$(RRRAAA(RRR,IAAA_INDIV) AND INVDATA_INDIVUSERS(IAAA_INDIV,'IDVU-HOTWTR')),DH1_INDIVHEATING(DHUSER,IAAA_INDIV,YYY))) ;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
        DH1_INDIVHEATING_GROUP(DHUSER,AAA,YYY)$(INDIVUSERS_GROUP_A(AAA,DHUSER,INDIVUSERS_GROUP)  AND INDIVUSERS_DEMANDTYPE_A(AAA,DHUSER,'SPACEHEATING') AND INDIVUSERS_DHUSER(DHUSER) ) =      SUM(RRR$RRRAAA(RRR,AAA),INDIVHEATING_GROUP_DHSHARE(YYY,DHUSER,RRR,INDIVUSERS_GROUP)*SUM(IAAA_INDIV$(RRRAAA(RRR,IAAA_INDIV) AND INVDATA_INDIVUSERS(IAAA_INDIV,'IDVU-SPACEHEAT')),DH1_INDIVHEATING(DHUSER,IAAA_INDIV,YYY))) ;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
        );                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
        DH(YYY,AAA,DHUSER)$DH1_INDIVHEATING_GROUP(DHUSER,AAA,YYY)  = DH1_INDIVHEATING_GROUP(DHUSER,AAA,YYY);                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
        $label NO_INDIVUSERS_AAA   
        """),
        path=out_path
    )
    INDIVUSERS_DH.body = (
        transform_xrdata(new_dataset,
                        'heat_demand_mwh',
                        {'DHUSER' : 'RESIDENTIAL'})
        .to_dataframe()
        .reset_index()
    ) 
    print('Total individual heat demand: ', round(INDIVUSERS_DH.body['heat_demand_mwh'].sum() / 1e6, 2) , ' TWh')
    ### Assign area suffix
    INDIVUSERS_DH.body.A = INDIVUSERS_DH.body.A + '_IDVU-SPACEHEAT'
    INDIVUSERS_DH.body_prepare(['DHUSER', 'A'],
                    'Y',
                    values='heat_demand_mwh')
    INDIVUSERS_DH.save()