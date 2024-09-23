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
import xarray as xr
from Submodules.utils import convert_names, transform_xrdata
from Submodules.municipal_template import DataContainer
from pybalmorel import IncFile
    
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

# 1.1 Data class containing heat data in xarray format
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

#%% ------------------------------- ###
###      2. .inc File Functions     ###
### ------------------------------- ###

# 2.1 Auxillary Functions

## 2.1.1 Wrapper for creating .inc files
def create_incfile(unique_processing):
    """The general wrapper for creating and saving .inc files, 
    because the creating of the IncFile class and saving it is the same every time.
    The unique processing of the .body content differs, however. 

    Args:
        unique_processing (func): The unique processing per case
        **incfile_kwargs: Keyword arguments to pass to IncFile
    """
    def wrapper(**kwargs):
        # Get name, prefix, suffix and path from the keyword arguments and send to IncFile
        incfile_kwargs = {k: kwargs[k] for k in ['name', 'prefix', 'suffix', 'path']}
        inc_file = IncFile(**incfile_kwargs)
        # If there are remaining keyword arguments, input them to unique_processing
        unique_processing(inc_file, **{k: v for k, v in kwargs.items() if k not in incfile_kwargs})
        inc_file.save()
    return wrapper

# 2.2 Make Annual Heat Demand .inc-files

## 2.2.1 Create DH.inc
@create_incfile
def create_DH(incfile, new_dataset: xr.Dataset):
    incfile.body = (
        transform_xrdata(new_dataset,
                        'heat_demand_mwh',
                        {'DHUSER' : 'RESH'})
        .to_dataframe()
        .reset_index()
    ) 
    print('Total district heating demand: ', round(incfile.body['heat_demand_mwh'].sum() / 1e6, 2) , ' TWh')
    ### Assign area suffix
    incfile.body.A = incfile.body.A + '_A'
    incfile.body_prepare(['DHUSER', 'A'],
                    'Y',
                    values='heat_demand_mwh')

## 2.2.2 Create INDUSTRY_DH.inc
@create_incfile
def create_INDUSTRY_DH(incfile, new_dataset: xr.Dataset):
    incfile.body = (
        transform_xrdata(new_dataset,
                        'heat_demand_mwh',
                        {'DHUSER' : ['IND-PHL',
                                     'IND-PHM',
                                     'IND-PHH']})
        .to_dataframe()
        .reset_index()
    ) 
    print('Total industry process heat demand: ', round(incfile.body['heat_demand_mwh'].sum() / 1e6, 2) , ' TWh')
    ### Assign area suffix
    idx = incfile.body.query('DHUSER == "IND-PHL"').index
    incfile.body.loc[idx, 'A'] = incfile.body.loc[idx, 'A'].values + '_IND-LT-NODH'
    idx = incfile.body.query('DHUSER == "IND-PHM"').index
    incfile.body.loc[idx, 'A'] = incfile.body.loc[idx, 'A'].values + '_IND-MT-NODH'
    idx = incfile.body.query('DHUSER == "IND-PHH"').index
    incfile.body.loc[idx, 'A'] = incfile.body.loc[idx, 'A'].values + '_IND-HT-NODH'
    incfile.body_prepare(['DHUSER', 'A'],
                    'Y',
                    values='heat_demand_mwh')
    
## 2.2.3 Create INDIVUSERS_DH.inc
@create_incfile
def create_INDIVUSERS_DH(incfile, new_dataset: xr.Dataset):
    incfile.body = (
        transform_xrdata(new_dataset,
                        'heat_demand_mwh',
                        {'DHUSER' : 'RESIDENTIAL'})
        .to_dataframe()
        .reset_index()
    ) 
    print('Total individual heat demand: ', round(incfile.body['heat_demand_mwh'].sum() / 1e6, 2) , ' TWh')
    ### Assign area suffix
    incfile.body.A = incfile.body.A + '_IDVU-SPACEHEAT'
    incfile.body_prepare(['DHUSER', 'A'],
                    'Y',
                    values='heat_demand_mwh')

# 2.3 Make Time Variation Heat Demand .inc-files

## 2.3.1 DH_VAR_T.inc


## 2.3.2 INDUSTRY_DH_VAR_T.inc
@create_incfile
def create_INDUSTRY_DH_VAR_T(incfile):
    incfile.body = '\n'.join([
        "* Assume that heat demand profile of industry correlates exactly to electricity demand profile",
        "DH_VAR_T(AAA,'IND-PHH',SSS,TTT)$(SUM((S,T), DE_VAR_T(RRR,'PII',SSS,TTT))) = DE_VAR_T(RRR,'PII',SSS,TTT);",
        "DH_VAR_T(AAA,'IND-PHM',SSS,TTT)$(SUM((S,T), DE_VAR_T(RRR,'PII',SSS,TTT))) = DE_VAR_T(RRR,'PII',SSS,TTT);",
        "DH_VAR_T(AAA,'IND-PHL',SSS,TTT)$(SUM((S,T), DE_VAR_T(RRR,'PII',SSS,TTT))) = DE_VAR_T(RRR,'PII',SSS,TTT);"
    ])

#%% ------------------------------- ###
###             3. Main             ###
### ------------------------------- ###
def main(show_difference: bool = False):
    heat = DistrictHeatAAU()
    heat.combine_data()
    dataset = heat.data
    
    # 3.1 Format Dataset
    conversion_file = 'Modules/Submodules/exo_heat_dem_conversion_dictionaries.pkl'
    dataset, new_dataset = convert_names(conversion_file, dataset, 'heat_demand_mwh')
    
    ## Drop dimensions
    new_dataset = (
        new_dataset
        .drop_dims(['lat', 'lon'])
        .drop_vars('polygons')
    )
    
    if show_difference:
        print('Before: \n', dataset, '\n\n')
        print('After: \n', new_dataset, '\n\n')
        
    out_path = 'Output'
    
    # 3.2 Create .inc files
    ## 3.2.1 DH.inc
    create_DH(new_dataset=new_dataset, name='DH', path=out_path, 
                prefix='\n'.join([
                    "* Data from Varmeplan 2021 (AAU)",
                    "PARAMETER DH(YYY,AAA,DHUSER)  'Annual brutto heat consumption';",
                    "TABLE DH1(DHUSER,AAA,YYY)"
                ]),
                suffix='\n'.join([
                    ";",
                    "DH(YYY,AAA,DHUSER)  = DH1(DHUSER,AAA,YYY);",
                    "DH1(DHUSER,AAA,YYY) = 0;",
                    "DH('2050',AAA,DHUSER) = DH('2019', AAA, DHUSER);"
                ])
)
    
    ## 3.2.2 INDUSTRY_DH.inc
    create_INDUSTRY_DH(new_dataset=new_dataset, 
                       name='INDUSTRY_DH', 
                       path=out_path,
                       prefix='\n'.join([
                           "* Data from Varmeplan 2021 (AAU), Danmarks statistik on industrial energy consumption pr. type",
                           "PARAMETER DH(YYY,AAA,DHUSER)  'Annual brutto heat consumption';",
                           "TABLE DH1_IND(DHUSER,AAA,YYY)"
                       ]),
                       suffix='\n'.join([
                           ";",
                           "DH(YYY,AAA,DHUSER)$DH1_IND(DHUSER,AAA,YYY)  = DH1_IND(DHUSER,AAA,YYY);",
                           "DH('2050',AAA,DHUSER)$DH1_IND(DHUSER,AAA,'2019') = DH('2019', AAA, DHUSER)$DH1_IND(DHUSER,AAA,'2019');",
                           "DH1_IND(DHUSER,AAA,YYY)=0;"
                       ]))
    
    
    ## 3.2.3 INDIVUSERS_DH.inc
    create_INDIVUSERS_DH(new_dataset=new_dataset, 
                         name='INDIVUSERS_DH', 
                         path=out_path,
                         prefix='\n'.join([
                             "* Data from Varmeplan 2021 (AAU)",
                             "TABLE DH1_INDIVHEATING(DHUSER,AAA,YYY)"
                         ]),
                         suffix='\n'.join([
                             ";",
                             "INDIVHEATING_GROUP_DHSHARE(YYY,DHUSER,RRR,INDIVUSERS_GROUP)$(NOT INDIVHEATING_GROUP_DHSHARE(YYY,DHUSER,RRR,INDIVUSERS_GROUP))=                                                         INDIVHEATING_GROUP_DHSHARE('2016',DHUSER,RRR,INDIVUSERS_GROUP);",
                             "LOOP(INDIVUSERS_GROUP$(NOT INDIVUSERS_GROUP_NEW(INDIVUSERS_GROUP)),",
                             "DH1_INDIVHEATING_GROUP(DHUSER,AAA,YYY)$(INDIVUSERS_GROUP_A(AAA,DHUSER,INDIVUSERS_GROUP)  AND INDIVUSERS_DEMANDTYPE_A(AAA,DHUSER,'HOTWATER') AND INDIVUSERS_DHUSER(DHUSER) ) =          SUM(RRR$RRRAAA(RRR,AAA),INDIVHEATING_GROUP_DHSHARE(YYY,DHUSER,RRR,INDIVUSERS_GROUP)*SUM(IAAA_INDIV$(RRRAAA(RRR,IAAA_INDIV) AND INVDATA_INDIVUSERS(IAAA_INDIV,'IDVU-HOTWTR')),DH1_INDIVHEATING(DHUSER,IAAA_INDIV,YYY))) ;",
                             "DH1_INDIVHEATING_GROUP(DHUSER,AAA,YYY)$(INDIVUSERS_GROUP_A(AAA,DHUSER,INDIVUSERS_GROUP)  AND INDIVUSERS_DEMANDTYPE_A(AAA,DHUSER,'SPACEHEATING') AND INDIVUSERS_DHUSER(DHUSER) ) =      SUM(RRR$RRRAAA(RRR,AAA),INDIVHEATING_GROUP_DHSHARE(YYY,DHUSER,RRR,INDIVUSERS_GROUP)*SUM(IAAA_INDIV$(RRRAAA(RRR,IAAA_INDIV) AND INVDATA_INDIVUSERS(IAAA_INDIV,'IDVU-SPACEHEAT')),DH1_INDIVHEATING(DHUSER,IAAA_INDIV,YYY))) ;",
                             ");",
                             "DH(YYY,AAA,DHUSER)$DH1_INDIVHEATING_GROUP(DHUSER,AAA,YYY)  = DH1_INDIVHEATING_GROUP(DHUSER,AAA,YYY);",
                             "$label NO_INDIVUSERS_AAA"
                         ]))
    
    ## 1.3 Make Heat Variation Profiles
    create_INDUSTRY_DH_VAR_T(name='INDUSTRY_DH_VAR_T', path=out_path,
                                prefix='', suffix='')
    
    

if __name__ == '__main__':
    main()