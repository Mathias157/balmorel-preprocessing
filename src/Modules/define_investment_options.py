"""
TITLE

Description

Created on 25.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import pickle
import pandas as pd
from pybalmorel import IncFile
from pybalmorel.utils import symbol_to_df
import os
import gams
import click


def plot_style(style: str = 'report'):
    
    if style == 'report':
        plt.style.use('default')
        fc = 'white'
    elif style == 'ppt':
        plt.style.use('dark_background')
        fc = 'none'

    return fc

#%% ------------------------------- ###
###        1. Getting AGKN          ###
### ------------------------------- ###

def save_symbol_from_all_endofmodel(symbol: str,
                                   columns: list,
                                   param_or_set: str,
                                   path_to_allendofmodel: str = r'C:\Users\mberos\gitRepos\Balmorel\all_endofmodel.gdx'):
    ws = gams.GamsWorkspace()
    db = ws.add_database_from_gdx(os.path.abspath(path_to_allendofmodel)) # From one of Ioannis' scenarios
    f = symbol_to_df(db, symbol, columns, parameter_or_set=param_or_set)
    f.to_parquet('Data/BalmorelData/AGKN_fromKountouris2024.gzip')

def base_AGKN(AGKN: pd.DataFrame, print_options: bool = False):
    # 1. Special options
    wind_off_G = [
        "DK2-OFF1_WT_WIND_OFF_L-RG1_Y-2020",
        "DK2-OFF1_WT_WIND_OFF_L-RG2_Y-2020",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2020",
        "DK1-OFF1_WT_WIND_OFF_L-RG2_Y-2020",
        "DK2-OFF1_WT_WIND_OFF_L-RG1_Y-2030",
        "DK2-OFF1_WT_WIND_OFF_L-RG2_Y-2030",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2030",
        "DK1-OFF1_WT_WIND_OFF_L-RG2_Y-2030",
        "DK2-OFF1_WT_WIND_OFF_L-RG1_Y-2040",
        "DK2-OFF1_WT_WIND_OFF_L-RG2_Y-2040",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2040",
        "DK1-OFF1_WT_WIND_OFF_L-RG2_Y-2040",
        "DK2-OFF1_WT_WIND_OFF_L-RG1_Y-2050",
        "DK2-OFF1_WT_WIND_OFF_L-RG2_Y-2050",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2050",
        "DK1-OFF1_WT_WIND_OFF_L-RG2_Y-2050",
    ]
    
    h2_G = [
        'GNR_ELYS_ELEC_AEC_Y-2020',
        'GNR_ELYS_ELEC_AEC_Y-2030',
        'GNR_ELYS_ELEC_AEC_Y-2040',
        'GNR_ELYS_ELEC_AEC_Y-2050',
        'GNR_ELYS_ELEC_AEC_DH_Y-2020',
        'GNR_ELYS_ELEC_AEC_DH_Y-2030',
        'GNR_ELYS_ELEC_AEC_DH_Y-2040',
        'GNR_ELYS_ELEC_AEC_DH_Y-2050',
        'GNR_FC_H2_SOFCC_Y-2020',
        'GNR_FC_H2_SOFCC_Y-2030',
        'GNR_FC_H2_SOFCC_Y-2040',
        'GNR_FC_H2_SOFCC_Y-2050',
        'GNR_H2S_H2-TNKC_Y-2020',
        'GNR_H2S_H2-TNKC_Y-2030',
        'GNR_H2S_H2-TNKC_Y-2040',
        'GNR_H2S_H2-TNKC_Y-2050',
        'GNR_H2S_H2-CAVERN_Y-2030',
        'GNR_H2S_H2-CAVERN_Y-2040',
        'GNR_H2S_H2-CAVERN_Y-2050',
        'GNR_STEAM-REFORMING_E-70_Y-2020',
        'GNR_STEAM-REFORMING-CCS_E-70_Y-2020',
    ]
    
    # 2. Base and Hydrogen investments
    temp = AGKN.query(
        "~A.str.contains('IDVU') and ~A.str.contains('IND')"
    )
    # print('Captured areas:\n%s'%('\n'.join(temp.A.unique())))
    # print('Investment options here:\n%s'%('\n'.join(temp.G.unique())))

    # Get base investment options and remove elements in wind_off_G from base_options (add hydrogen when the error arrives)
    base_options = [option for option in temp.G.unique() if option not in wind_off_G and option not in h2_G]
    
    if print_options:
        print('Base options:\n%s'%('\n'.join(base_options)))

    return base_options

#%% ------------------------------- ###
###            X. Main              ###
### ------------------------------- ###

@click.command()
@click.option('--path-to-allendofmodel', type=str, required=False, help='A parameter')
def main(path_to_allendofmodel: str):
    
    # Load file
    f = pd.read_parquet(r'C:\Users\mberos\gitRepos\balmorel-preprocessing\src\Data\BalmorelData\AGKN_fromKountouris2024.gzip')
    f = f.query('A.str.contains("DK")')

    # Get base options for base AGKN
    base_options = base_AGKN(f)
    
    # Load base areas
    base_areas = pickle.load(open('Modules/Submodules/districtheat_sets.pkl', 'rb'))
    
    # Make table for base
    incfile = IncFile(name='AGKN', path='Output',
                      prefix='\n'.join([
                          "* Defining base investment options",
                          "SET BASE_INV_OPTIONS(GGG)",
                          "/",
                          "\n".join(base_options),
                          "/;",
                          ""
                      ]),
                      suffix='')
    incfile.body = "\n".join(["AGKN('%s',GGG) = BASE_INV_OPTIONS(GGG);"%area for area in base_areas.values()])
    incfile.save()

if __name__ == '__main__':
    main()
