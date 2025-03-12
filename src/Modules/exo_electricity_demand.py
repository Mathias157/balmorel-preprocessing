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

import click
from Submodules.utils import convert_names, transform_xrdata 
import xarray as xr
from pybalmorel import IncFile


#%% ------------------------------- ###
###      1. Make .inc Files         ###
### ------------------------------- ###

# Main function
@click.command()
@click.option("--conversion-file", type=str, required=True, help="The conversion dictionary")
@click.option("--el-dataset", type=str, required=True, help="The xarray electricity dataset")
@click.option("--show-difference", type=bool, required=False, help="Show dataset before and after conversion")
def main(conversion_file: str, 
         el_dataset: str, 
         show_difference: bool = False):
    """
        Main function to process and convert dataset names, and create .inc files.
    Args:
        conversion_file (str): Path to the file containing conversion mappings.
        el_dataset (str): Path to the dataset file to be processed.
        show_difference (bool, optional): Flag to indicate whether to print the 
                                            dataset before and after conversion. 
                                            Defaults to False.
    Returns:
        None
    """
    
    # 1.1 Format Dataset    
    ## Load dataset
    el_dataset = xr.load_dataset(el_dataset) # converts from string path to xr.Dataset
    dataset, new_dataset = convert_names(conversion_file, el_dataset, 
                                         'electricity_demand_mwh', convert_seasons_and_terms=True)
    
    if show_difference:
        print('Before: \n', dataset, '\n\n')
        print('After: \n', new_dataset, '\n\n')
        
    # 1.2 Make .inc-files
    out_path = 'Output'
    ## 1.2.1 DE
    DE = IncFile(name='DE', path=out_path,
                prefix='\n'.join([
                    "* Data from Energinet Dataservice 2023",
                    "TABLE   DE1(RRR,DEUSER,YYY)   'Annual electricity consumption (MWh)'", 
                    "",
                ]),
                suffix='\n'.join([
                    ";",
                    "DE(YYY,RRR,DEUSER)=DE1(RRR,DEUSER,YYY);",
                    "DE('2050',RRR,DEUSER) = DE('2023', RRR, DEUSER);",
                    "DE1(RRR,DEUSER,YYY) = 0;",
                ])
    )
    ### Sum to annual electricity demands
    DE.body = (
        transform_xrdata(new_dataset,
                        'electricity_demand_mwh',
                        sets_to_sum=['S', 'T'])
        .to_dataframe()
    ) 
    DE.body_prepare(['R', 'DEUSER'],
                    'Y',
                    values='electricity_demand_mwh')
    DE.save()
    
    ## 1.2.2 DE_VAR_T
    DE_VAR_T = IncFile(name='DE_VAR_T', path=out_path,
                       prefix='\n'.join(["* Data from Energinet Dataservice 2023",
                                        "TABLE DE_VAR_T1(DEUSER,SSS,TTT,RRR) 'Variation in electricity demand'",
                                        "",
                        ]),
                       suffix='\n'.join(["",
                                        ";",
                                        "PARAMETER DE_VAR_T(RRR,DEUSER,SSS,TTT) 'Variation in electricity demand';",                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
                                        "DE_VAR_T(RRR,DEUSER,SSS,TTT) =  DE_VAR_T1(DEUSER,SSS,TTT,RRR); ",
                                        "DE_VAR_T1(DEUSER,SSS,TTT,RRR) = 0;"
                        ]),
                       )
    DE_VAR_T.body = (
        transform_xrdata(new_dataset,
                         'electricity_demand_mwh')
        .to_dataframe()
    )
    DE_VAR_T.body_prepare(['DEUSER', 'S', 'T'],
                          'R',
                          values='electricity_demand_mwh')
    DE_VAR_T.save()
    

if __name__ == '__main__':
    main()