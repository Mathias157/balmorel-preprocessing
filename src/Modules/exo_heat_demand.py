"""
Exogenous Heat Demands

Create exogenous heat demands using data from various places

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
import pickle
from Submodules.utils import convert_names, transform_xrdata, save_dict_set, cmap
from Submodules.municipal_template import DataContainer
from pybalmorel import IncFile
import click

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
                                    column=temp/1e6,
                                    cmap=cmap,
                                    vmin=0,
                                    vmax=6,
                                    legend=True).set_title('Exogenous Heat Demand (TWh)')
            ax.axes.set_axis_off()
            fig.savefig(f'Output/Figures/exo_heat_demand_total.png',
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
                fig.savefig(f'Output/Figures/exo_heat_demand_{user}.png',
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
    save_dict_set('Modules/Submodules/districtheat_sets.pkl', incfile.body.loc[:, ['A']], 'A', '_A', 'R') # Save region-to-area dictionary

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
    save_dict_set('Modules/Submodules/ind-lt_sets.pkl', incfile.body.loc[idx, ['A']], 'A', '_IND-LT-NODH', 'R') # Save region-to-area dictionary
        
    idx = incfile.body.query('DHUSER == "IND-PHM"').index
    incfile.body.loc[idx, 'A'] = incfile.body.loc[idx, 'A'].values + '_IND-MT-NODH'
    save_dict_set('Modules/Submodules/ind-mt_sets.pkl', incfile.body.loc[idx, ['A']], 'A', '_IND-MT-NODH', 'R') # Save region-to-area dictionary

    idx = incfile.body.query('DHUSER == "IND-PHH"').index
    incfile.body.loc[idx, 'A'] = incfile.body.loc[idx, 'A'].values + '_IND-HT-NODH'    
    save_dict_set('Modules/Submodules/ind-ht_sets.pkl', incfile.body.loc[idx, ['A']], 'A', '_IND-HT-NODH', 'R') # Save region-to-area dictionary

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
    save_dict_set('Modules/Submodules/individual_sets.pkl', incfile.body.loc[:, ['A']], 'A', '_IDVU-SPACEHEAT', 'R') # Save region-to-area dictionary

    incfile.body_prepare(['DHUSER', 'A'],
                    'Y',
                    values='heat_demand_mwh')

# 2.3 Make Time Variation Heat Demand .inc-files

## 2.3.1 DH_VAR_T.inc
# See format_balmorel_data, the very similar future gas profiles are used

## 2.3.2 INDUSTRY_DH_VAR_T.inc
@create_incfile
def create_INDUSTRY_DH_VAR_T(incfile, el_new_dataset: xr.Dataset, A_suffix: str):
    incfile.body = (
        transform_xrdata(el_new_dataset,
                         'electricity_demand_mwh')
        .to_dataframe()
        .reset_index()
    )
    incfile.body.loc[:, 'A'] = incfile.body.loc[:, 'A'].values + A_suffix
    incfile.body_prepare(['S', 'T'],
                          ['A'], values='electricity_demand_mwh')


## 2.3.3 INDIVUSERS_DH_VAR_T.inc
# See format_balmorel_data, the very similar future gas profiles are used


#%% ------------------------------- ###
###             3. Main             ###
### ------------------------------- ###

@click.command()
@click.option('--plot-only', is_flag=True, default=False, help="Only output a plot")
def main(plot_only: bool, show_difference: bool = False):
    heat = DistrictHeatAAU()
    
    if plot_only:
        heat.combine_data(plot_only)
    else:
        heat.combine_data()
        dataset = heat.data
        
        # 3.1 Format Dataset
        conversion_file = 'Modules/Submodules/exo_heat_dem_conversion_dictionaries.pkl'
        
        ## 3.1.1 Heat Demand
        dataset, new_dataset = convert_names(conversion_file, dataset, 'heat_demand_mwh')
        
        ### Drop dimensions
        new_dataset = (
            new_dataset
            .drop_dims(['lat', 'lon'])
            .drop_vars('polygons')
        )
        
        if show_difference:
            print('###\nHeat Dataset\n###')
            print('Before: \n', dataset, '\n\n')
            print('After: \n', new_dataset, '\n\n')
        
        ## 3.1.2 Electricity Profile for Industry
        eldem = (
            xr.load_dataset('Data/Timeseries/energinet_eldem.nc')
            .sel(user='industry')
            .assign_coords(user='industry_phh')
            .rename({'week' : 'S', 'hour' : 'T'})
        )
        eldataset, el_new_dataset = convert_names(conversion_file, eldem, 'electricity_demand_mwh', convert_seasons_and_terms=True)

        if show_difference:
            print('###\nElectricity Dataset\n###')
            print('Before: \n', eldataset, '\n\n')
            print('After: \n', el_new_dataset, '\n\n')
            
            
        # 3.2 Create .inc files
        out_path = 'Output'
        ## 3.2.1 DH.inc
        create_DH(new_dataset=new_dataset, name='DH', path=out_path, 
                    prefix='\n'.join([
                        "* Data from Varmeplan 2021 (AAU)",
                        "PARAMETER DH(YYY,AAA,DHUSER)  'Annual brutto heat consumption';",
                        "TABLE DH1(DHUSER,AAA,YYY)",
                        ""
                    ]),
                    suffix='\n'.join([
                        "",
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
                            "TABLE DH1_IND(DHUSER,AAA,YYY)",
                            ""
                        ]),
                        suffix='\n'.join([
                            "",
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
                                "TABLE DH1_INDIVHEATING(DHUSER,AAA,YYY)",
                                ""
                            ]),
                            suffix='\n'.join([
                                "",
                                ";",
                                "DH1_INDIVHEATING(DHUSER,AAA,'2050') = DH1_INDIVHEATING(DHUSER,AAA,'2019');",
                                "DH(YYY,AAA,DHUSER)$DH1_INDIVHEATING(DHUSER,AAA,YYY)  = DH1_INDIVHEATING(DHUSER,AAA,YYY);",
                                "DH1_INDIVHEATING(DHUSER,AAA,YYY)=0;"
                            ]))
        
        ## 3.3 Make Heat Variation Profiles
        
        ### 3.3.1 INDUSTRY_DH_VAR_T
        #### High process heat
        create_INDUSTRY_DH_VAR_T(el_new_dataset=el_new_dataset, 
                                name='INDUSTRY_DH_VAR_T', 
                                A_suffix='_IND-HT-NODH',
                                path=out_path,
                                prefix="TABLE DH_VAR_T_IND(SSS,TTT,AAA)\n",
                                suffix='\n'.join(["",
                                                ";",
                                                "* Collect series to other heat series, if there is a industry heat series",
                                                "DH_VAR_T(AAA,'IND-PHH',SSS,TTT)$(SUM((S,T), DH_VAR_T_IND(S,T,AAA))) = DH_VAR_T_IND(SSS,TTT,AAA);",
                                                "DH_VAR_T_IND(SSS,TTT,AAA)=0;",
                                                "$if     EXIST '../data/INDUSTRY_DH_VAR_T2.inc' $INCLUDE '../data/INDUSTRY_DH_VAR_T2.inc';",
                                                "$if not EXIST '../data/INDUSTRY_DH_VAR_T2.inc' $INCLUDE '../../base/data/INDUSTRY_DH_VAR_T2.inc';",
                                                "$if     EXIST '../data/INDUSTRY_DH_VAR_T3.inc' $INCLUDE '../data/INDUSTRY_DH_VAR_T3.inc';",
                                                "$if not EXIST '../data/INDUSTRY_DH_VAR_T3.inc' $INCLUDE '../../base/data/INDUSTRY_DH_VAR_T3.inc';"
                                ]))
        #### Medium process heat
        create_INDUSTRY_DH_VAR_T(el_new_dataset=el_new_dataset, 
                                name='INDUSTRY_DH_VAR_T2', 
                                A_suffix='_IND-MT-NODH',
                                path=out_path,
                                prefix="TABLE DH_VAR_T_INDMT(SSS,TTT,AAA)\n",
                                suffix='\n'.join(["",
                                                ";",
                                                "* Collect series to other heat series, if there is a industry heat series",
                                                "DH_VAR_T(AAA,'IND-PHM',SSS,TTT)$(SUM((S,T), DH_VAR_T_INDMT(S,T,AAA))) = DH_VAR_T_INDMT(SSS,TTT,AAA);",
                                                "DH_VAR_T_INDMT(SSS,TTT,AAA)=0;"
                                ]))
        #### Low process heat
        create_INDUSTRY_DH_VAR_T(el_new_dataset=el_new_dataset, 
                                name='INDUSTRY_DH_VAR_T3', 
                                A_suffix='_IND-LT-NODH',
                                path=out_path,
                                prefix="TABLE DH_VAR_T_INDLT(SSS,TTT,AAA)\n",
                                suffix='\n'.join(["",
                                                ";",
                                                "* Collect series to other heat series, if there is a industry heat series",
                                                "DH_VAR_T(AAA,'IND-PHL',SSS,TTT)$(SUM((S,T), DH_VAR_T_INDLT(S,T,AAA))) = DH_VAR_T_INDLT(SSS,TTT,AAA);",
                                                "DH_VAR_T_INDLT(SSS,TTT,AAA)=0;"
                                ]))


if __name__ == '__main__':
    main()