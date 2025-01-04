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
    # Options not to be included
    # This was copy pasted from the outcommented print statements below
    other_vre = [
        "GNR_WT-SP277-HH100_ONS_LS_L-RG2_Y-2020",
        "GNR_WT-SP277-HH100_ONS_LS_L-RG2_Y-2030",
        "GNR_WT-SP277-HH100_ONS_LS_L-RG2_Y-2040",
        "GNR_WT-SP277-HH100_ONS_LS_L-RG2_Y-2050",
        "GNR_WT-SP277-HH100_ONS_LS_L-RG3_Y-2020",
        "GNR_WT-SP277-HH100_ONS_LS_L-RG3_Y-2030",
        "GNR_WT-SP277-HH100_ONS_LS_L-RG3_Y-2040",
        "GNR_WT-SP277-HH100_ONS_LS_L-RG3_Y-2050",
        "DK2-OFF1_WT_WIND_OFF_L-RG2_Y-2020",
        "DK1-OFF1_WT_WIND_OFF_L-RG2_Y-2020",
        "DK2-OFF1_WT_WIND_OFF_L-RG2_Y-2030",
        "DK1-OFF1_WT_WIND_OFF_L-RG2_Y-2030",
        "DK2-OFF1_WT_WIND_OFF_L-RG2_Y-2040",
        "DK1-OFF1_WT_WIND_OFF_L-RG2_Y-2040",
        "DK2-OFF1_WT_WIND_OFF_L-RG2_Y-2050",
        "DK1-OFF1_WT_WIND_OFF_L-RG2_Y-2050",
        "DK2-OFF1_WT_WIND_OFF_L-RG1_Y-2020",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2020",
        "DK2-OFF1_WT_WIND_OFF_L-RG1_Y-2030",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2030",
        "DK2-OFF1_WT_WIND_OFF_L-RG1_Y-2040",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2040",
        "DK2-OFF1_WT_WIND_OFF_L-RG1_Y-2050",
        "DK1-OFF1_WT_WIND_OFF_L-RG1_Y-2050",
        "GNR_PV_SUN_LS-8-MW_RG2_Y-2020",       
        "GNR_PV_SUN_LS-8-MW_RG2_Y-2030",
        "GNR_PV_SUN_LS-8-MW_RG2_Y-2040",    
        "GNR_PV_SUN_LS-8-MW_RG2_Y-2050",
    ]
    
    solar_heating = [
        'GNR_SH_SUN_LS_Y-2020',
        'GNR_SH_SUN_LS_Y-2030',
        'GNR_SH_SUN_LS_Y-2040',
        'GNR_SH_SUN_LS_Y-2050',
    ]
    
    hydrogen_options = [
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
        "GNR_TG-MeOH-2050_H2", 
        "GNR_TG-MeOH-2050",    
        "GNR_eNH3-2050"
    ]
    
    # Small scale investments
    small_scale = [
        "GNR_HS_HEAT_PIT_L-CEN_E-70_Y-2050",
        "GNR_HS_HEAT_WTR-TANK_SS_E-95_Y-2010",
        "GNR_ES_ELEC_BAT-LITHIO-PEAK_E-86_Y-2050",
        "GNR_ES_ELEC_BAT-LITHIO-GRID_E-86_Y-2050",
        "GNR_PV_SUN_LS-8-MW_RG1_Y-2050",
        "GNR_WT-SP277-HH100_ONS_LS_L-RG1_Y-2050",
        "GNR_HP_ELEC_AIR-WTR_COP-365_SS-4-KW_Y-2050",
        "GNR_HP_ELEC_GROUND-WTR_COP-400_SS-10-KW_Y-2050",
        # "GNR_CC_NGAS_BP_E-51_SS-10-MW_Y-2020",
        # "GNR_CC_NGAS_BP_E-53_SS-10-MW_Y-2030",
        # "GNR_CC_NGAS_BP_E-54_SS-10-MW_Y-2040",
        # "GNR_CC_NGAS_BP_E-55_SS-10-MW_Y-2050",
        # "GNR_CC_NGASCCS_BP_E-51_SS-10-MW_Y-2020", 
        # "GNR_CC_NGASCCS_BP_E-53_SS-10-MW_Y-2030",
        "GNR_BO_ELEC_E-100_SS-3-KW-FEED_Y-2050", 
        # "GNR_CC_NGASCCS_BP_E-54_SS-10-MW_Y-2040", 
        "GNR_CC_NGASCCS_BP_E-55_SS-10-MW_Y-2050",
        # "GNR_CC_NGASCCS_CND_E-51_SS-10-MW_Y-2020",
        # "GNR_CC_NGASCCS_CND_E-53_SS-10-MW_Y-2030",
        # "GNR_CC_NGASCCS_CND_E-54_SS-10-MW_Y-2040",
        "GNR_CC_NGASCCS_CND_E-55_SS-10-MW_Y-2050",
        # "GNR_GT_NGAS_BP_E-37_SS-5-MW_Y-2020",
        # "GNR_GT_NGAS_BP_E-39_SS-5-MW_Y-2030",
        # "GNR_GT_NGAS_BP_E-40_SS-5-MW_Y-2040",
        "GNR_ST_MSW_CND_E-24_SS-35-MW-FEED_Y-2050",
        "GNR_ST_MSW_BP_E-24_SS-35-MW-FEED_Y-2050",
        # "GNR_GT_NGAS_BP_E-40_SS-5-MW_Y-2050",
        # "GNR_ST_STRW_BP_E-17_SS-20-MW-FEED_Y-2020",
        # "GNR_ST_STRW_BP_E-17_SS-20-MW-FEED_Y-2030",
        # "GNR_ST_STRW_BP_E-17_SS-20-MW-FEED_Y-2040",
        "GNR_ST_STRW_BP_E-17_SS-20-MW-FEED_Y-2050",
        "GNR_ST_STRW_CND_E-17_SS-20-MW-FEED_Y-2050",
        # "GNR_ST_WOODCHI_BP_E-16_SS-20-MW-FEED_Y-2020",
        # "GNR_ST_WOODCHI_BP_E-16_SS-20-MW-FEED_Y-2030",
        # "GNR_ST_WOODCHI_BP_E-16_SS-20-MW-FEED_Y-2040",
        "GNR_ST_WOODCHI_BP_E-16_SS-20-MW-FEED_Y-2050",
        # "GNR_ST_WOODPEL_BP_E-17_SS-20-MW-FEED_Y-2020",
        # "GNR_ST_WOODPEL_BP_E-17_SS-20-MW-FEED_Y-2030",
        # "GNR_ST_WOODPEL_BP_E-17_SS-20-MW-FEED_Y-2040",
        # "GNR_ST_WOODPEL_BP_E-17_SS-20-MW-FEED_Y-2050",
        # "GNR_ST_WOODCHI_CND_E-16_SS-20-MW-FEED_Y-2020", 
        # "GNR_ST_WOODCHI_CND_E-16_SS-20-MW-FEED_Y-2030", 
        # "GNR_ST_WOODCHI_CND_E-16_SS-20-MW-FEED_Y-2040", 
        "GNR_ST_WOODCHI_CND_E-16_SS-20-MW-FEED_Y-2050", 
        # "GNR_ST_STRW_CND_E-17_SS-20-MW-FEED_Y-2020",
        # "GNR_ST_STRW_CND_E-17_SS-20-MW-FEED_Y-2030",
        "GNR_BO_WOODPEL_E-85_SS-8-KW-FEED_Y-2050",
        # "GNR_ST_STRW_CND_E-17_SS-20-MW-FEED_Y-2040",
    ]
    
    medium_scale = [
        "GNR_HS_HEAT_PIT_L-CEN_E-70_Y-2050",
        "GNR_HS_HEAT_WTR-TANK_SS_E-95_Y-2010",
        "GNR_ES_ELEC_BAT-LITHIO-PEAK_E-86_Y-2050",
        "GNR_ES_ELEC_BAT-LITHIO-GRID_E-86_Y-2050",
        "GNR_PV_SUN_LS-8-MW_RG1_Y-2050",
        "GNR_WT-SP277-HH100_ONS_LS_L-RG1_Y-2050",
        "GNR_HP_ELEC_AIR-WTR_COP-365_SS-4-KW_Y-2050",
        "GNR_HP_ELEC_GROUND-WTR_COP-400_SS-10-KW_Y-2050",
        # "GNR_BO_ELEC_E-99_MS-1-MW-FEED_Y-2020",
        # "GNR_BO_ELEC_E-99_MS-1-MW-FEED_Y-2030",
        # "GNR_BO_ELEC_E-99_MS-1-MW-FEED_Y-2040",
        "GNR_BO_ELEC_E-99_MS-1-MW-FEED_Y-2050",
        # "GNR_BO_NGAS_E-105_MS-5-MW_Y-2020",
        # "GNR_BO_NGAS_E-106_MS-5-MW_Y-2030",
        # "GNR_BO_NGAS_E-106_MS-5-MW_Y-2040",
        # "GNR_BO_NGAS_E-106_MS-5-MW_Y-2050",
        # "GNR_ST_MSW_BP_E-23_MS-80-MW-FEED_Y-2020",
        # "GNR_ST_MSW_BP_E-24_MS-80-MW-FEED_Y-2030",
        # "GNR_ST_MSW_BP_E-24_MS-80-MW-FEED_Y-2040",
        "GNR_ST_MSW_BP_E-24_MS-80-MW-FEED_Y-2050",
        "GNR_ST_MSW_CND_E-24_MS-80-MW-FEED_Y-2050", 
        "GNR_CC_NGASCCS_CND_E-55_SS-10-MW_Y-2050",
        "GNR_ST_NGASCCS_BP_E-7_MS-15-MW_Y-2020",
        # "GNR_ST_NGAS_BP_E-7_MS-15-MW_Y-2020",
        # "GNR_ST_STRW_BP_E-25_MS-80-MW-FEED_Y-2020",
        # "GNR_ST_STRW_BP_E-25_MS-80-MW-FEED_Y-2030",
        # "GNR_ST_STRW_BP_E-25_MS-80-MW-FEED_Y-2040",
        "GNR_ST_STRW_BP_E-25_MS-80-MW-FEED_Y-2050",
        "GNR_ST_STRW_CND_E-25_MS-80-MW-FEED_Y-2050",
        # "GNR_ST_WOODCHI_BP_E-29_MS-80-MW-FEED_Y-2020",
        # "GNR_ST_WOODCHI_BP_E-29_MS-80-MW-FEED_Y-2030",
        # "GNR_ST_WOODCHI_BP_E-29_MS-80-MW-FEED_Y-2040",
        "GNR_ST_WOODCHI_BP_E-29_MS-80-MW-FEED_Y-2050",
        "GNR_ST_WOODCHI_CND_E-29_MS-80-MW-FEED_Y-2050",
        # "GNR_ST_WOODPEL_BP_E-30_MS-80-MW-FEED_Y-2020",
        # "GNR_ST_WOODPEL_BP_E-30_MS-80-MW-FEED_Y-2030",
        # "GNR_ST_WOODPEL_BP_E-30_MS-80-MW-FEED_Y-2040",
        # "GNR_ST_WOODPEL_BP_E-30_MS-80-MW-FEED_Y-2050",
        # "GNR_ST_WOODCHI_CND_E-29_MS-80-MW-FEED_Y-2020",
        # "GNR_ST_WOODCHI_CND_E-29_MS-80-MW-FEED_Y-2030",
        # "GNR_ST_WOODCHI_CND_E-29_MS-80-MW-FEED_Y-2040",
        # "GNR_ST_STRW_CND_E-25_MS-80-MW-FEED_Y-2020",
        # "GNR_ST_STRW_CND_E-25_MS-80-MW-FEED_Y-2030",
        # "GNR_ST_STRW_CND_E-25_MS-80-MW-FEED_Y-2040",
    ]
        
    large_scale = [
        # "GNR_BO_MSW_E-106_LS-35-MW-FEED_Y-2030",
        # "GNR_BO_MSW_E-106_LS-35-MW-FEED_Y-2040",
        # "GNR_BO_MSW_E-106_LS-35-MW-FEED_Y-2050",
        "GNR_HP_ELEC_AIR-WTR_COP-360_LS_Y-2050",
        "GNR_HP_ELEC_GROUND-WTR_COP-410_LS-4-MW_Y-2050",
        "GNR_HS_HEAT_PIT_L-DEC_E-70_Y-2050",
        "GNR_HS_HEAT_WTR-TANK_LS_E-95_Y-2010",
        "GNR_BO_ELEC_E-99_LS-10-MW-FEED_Y-2050",
        "GNR_ES_ELEC_BAT-LITHIO-PEAK_E-86_Y-2050",
        "GNR_ES_ELEC_BAT-LITHIO-GRID_E-86_Y-2050",
        "GNR_PV_SUN_LS-8-MW_RG1_Y-2050",
        "GNR_WT-SP277-HH100_ONS_LS_L-RG1_Y-2050",
        # "GNR_ST_MSW_CND_E-23_LS-220-MW-FEED_Y-2020",
        # "GNR_ST_MSW_CND_E-24_LS-220-MW-FEED_Y-2030",
        # "GNR_ST_MSW_CND_E-25_LS-220-MW-FEED_Y-2040",
        "GNR_ST_MSW_CND_E-25_LS-220-MW-FEED_Y-2050",
        # "GNR_BO_MSW_E-106_LS-35-MW-FEED_Y-2020",
        # "GNR_ST_MSW_BP_E-23_LS-220-MW-FEED_Y-2020",
        # "GNR_ST_MSW_BP_E-24_LS-220-MW-FEED_Y-2030",
        # "GNR_ST_MSW_BP_E-25_LS-220-MW-FEED_Y-2040",
        "GNR_ST_MSW_BP_E-25_LS-220-MW-FEED_Y-2050",
        # "GNR_ST_WOODCHI_CND_E-29_LS-600-MW-FEED_Y-2020",
        # "GNR_ST_WOODCHI_CND_E-29_LS-600-MW-FEED_Y-2030",
        # "GNR_ST_WOODCHI_CND_E-29_LS-600-MW-FEED_Y-2040",
        "GNR_ST_WOODCHI_CND_E-29_LS-600-MW-FEED_Y-2050",
        # "GNR_ST_WOODPEL_CND_E-33_LS-800-MW-FEED_Y-2020",
        # "GNR_ST_WOODPEL_CND_E-33_LS-800-MW-FEED_Y-2030",
        # "GNR_ST_WOODPEL_CND_E-33_LS-800-MW-FEED_Y-2040",
        # "GNR_ST_WOODPEL_CND_E-33_LS-800-MW-FEED_Y-2050",
        # "GNR_ST_STRW_CND_E-31_LS-132-MW-FEED_Y-2020",
        # "GNR_ST_STRW_CND_E-31_LS-132-MW-FEED_Y-2030",
        # "GNR_ST_STRW_CND_E-31_LS-132-MW-FEED_Y-2040",
        "GNR_ST_STRW_CND_E-31_LS-132-MW-FEED_Y-2050",
        # "GNR_ST_NGAS_CND_E-47_LS-400-MW_Y-2020",
        # "GNR_ST_NGASCCS_CND_E-47_LS-400-MW_Y-2020",
        # "GNR_GT_NGAS_CND_E-42_LS-40-MW_Y-2020",
        # "GNR_GT_NGAS_CND_E-43_LS-40-MW_Y-2030",
        # "GNR_GT_NGAS_CND_E-44_LS-40-MW_Y-2040",
        # "GNR_GT_NGAS_CND_E-44_LS-40-MW_Y-2050",
        # "GNR_CC_NGAS_CND_E-59_LS-100-MW_Y-2020",
        # "GNR_CC_NGAS_CND_E-61_LS-100-MW_Y-2030",
        # "GNR_CC_NGAS_CND_E-62_LS-100-MW_Y-2040",
        # "GNR_CC_NGAS_CND_E-63_LS-100-MW_Y-2050",
        # "GNR_CC_NGASCCS_CND_E-59_LS-100-MW_Y-2020",
        # "GNR_CC_NGASCCS_CND_E-61_LS-100-MW_Y-2030",
        # "GNR_CC_NGASCCS_CND_E-62_LS-100-MW_Y-2040",
        "GNR_CC_NGASCCS_CND_E-63_LS-100-MW_Y-2050",
        # "GNR_ST_NGAS_EXT_E-47_LS-400-MW_Y-2020",
        # "GNR_ST_NGASCCS_EXT_E-47_LS-400-MW_Y-2020",
        # "GNR_ST_STRW_BP_E-31_LS-132-MW-FEED_Y-2020",
        # "GNR_ST_STRW_BP_E-31_LS-132-MW-FEED_Y-2030",
        # "GNR_ST_STRW_BP_E-31_LS-132-MW-FEED_Y-2040",
        "GNR_ST_STRW_BP_E-31_LS-132-MW-FEED_Y-2050",
        # "GNR_ST_WOODCHI_BP_E-29_LS-600-MW-FEED_Y-2020",
        # "GNR_ST_WOODCHI_BP_E-29_LS-600-MW-FEED_Y-2030",
        # "GNR_ST_WOODCHI_BP_E-29_LS-600-MW-FEED_Y-2040",
        "GNR_ST_WOODCHI_BP_E-29_LS-600-MW-FEED_Y-2050",
        # "GNR_ST_WOODPEL_BP_E-33_LS-800-MW-FEED_Y-2020",
        # "GNR_ST_WOODPEL_BP_E-33_LS-800-MW-FEED_Y-2030",
        # "GNR_ST_WOODPEL_BP_E-33_LS-800-MW-FEED_Y-2040",
        # "GNR_ST_WOODPEL_BP_E-33_LS-800-MW-FEED_Y-2050",
        # "GNR_GT_NGAS_BP_E-42_LS-40-MW_Y-2020",
        # "GNR_GT_NGAS_BP_E-43_LS-40-MW_Y-2030",
        # "GNR_GT_NGAS_BP_E-44_LS-40-MW_Y-2040",
        # "GNR_GT_NGAS_BP_E-44_LS-40-MW_Y-2050",
        # "GNR_BO_STRW_E-102_LS-6-MW_Y-2020",
        # "GNR_BO_STRW_E-102_LS-6-MW_Y-2030",
        # "GNR_BO_STRW_E-102_LS-6-MW_Y-2040",
        "GNR_BO_STRW_E-102_LS-6-MW_Y-2050",
        # "GNR_BO_WOODCHI_E-115_LS-7-MW_Y-2020",
        # "GNR_BO_WOODCHI_E-115_LS-7-MW_Y-2030",
        # "GNR_BO_WOODCHI_E-115_LS-7-MW_Y-2040",
        "GNR_BO_WOODCHI_E-115_LS-7-MW_Y-2050",
        # "GNR_BO_WOODPEL_E-100_LS-6-MW_Y-2020",
        # "GNR_BO_WOODPEL_E-100_LS-6-MW_Y-2030",
        # "GNR_BO_WOODPEL_E-100_LS-6-MW_Y-2040",
        # "GNR_BO_WOODPEL_E-100_LS-6-MW_Y-2050",
        # "GNR_CC_NGAS_EXT_E-59_LS-100-MW_Y-2020",
        # "GNR_CC_NGAS_EXT_E-61_LS-100-MW_Y-2030",
        # "GNR_CC_NGAS_EXT_E-62_LS-100-MW_Y-2040",
        # "GNR_CC_NGAS_EXT_E-63_LS-100-MW_Y-2050",
        # "GNR_CC_NGASCCS_EXT_E-59_LS-100-MW_Y-2020",
        # "GNR_CC_NGASCCS_EXT_E-61_LS-100-MW_Y-2030",
        # "GNR_CC_NGASCCS_EXT_E-62_LS-100-MW_Y-2040",
        "GNR_CC_NGASCCS_EXT_E-63_LS-100-MW_Y-2050",
    ]
    
    # 2. Base and Hydrogen investments
    temp = AGKN.query(
        "~A.str.contains('IDVU') and ~A.str.contains('IND')"
    )
    
    # Get options from previous study's AGKN
    # unique_options = pd.Series(list(temp.G) + small_scale).unique() # Get unique options from previous study
    # exclude_options = other_vre + hydrogen_options + solar_heating + medium_scale + large_scale
    # base_small_options = [option for option in unique_options if option not in exclude_options]
    # # unique_options = pd.Series(list(temp.G) + medium_scale).unique() # Get unique options from previous study
    # exclude_options = other_vre + hydrogen_options + solar_heating + small_scale + large_scale
    # base_medium_options = [option for option in unique_options if option not in exclude_options]
    # # unique_options = pd.Series(list(temp.G) + large_scale).unique() # Get unique options from previous study
    # exclude_options = other_vre + hydrogen_options + solar_heating + medium_scale + small_scale
    # base_large_options = [option for option in unique_options if option not in exclude_options]
    # Get chosen options
    exclude_options = other_vre + hydrogen_options + solar_heating
    base_small_options = [option for option in small_scale if option not in exclude_options]
    base_medium_options = [option for option in medium_scale if option not in exclude_options]
    base_large_options = [option for option in large_scale if option not in exclude_options]
    
    
    # Use this to inspect offshore and hydrogen investment options
    if print_options:
        print('\nCaptured areas:\n%s'%('\n'.join(temp.A.unique())))
        print('Investment options here:\n%s'%('\n'.join(temp.G.unique())))
        print('\nBase options without offshore or hydrogen:\n%s'%('\n'.join(base_small_options)))

    # Remove cavern
    h2_caverns = [
        'GNR_H2S_H2-CAVERN_Y-2030',
        'GNR_H2S_H2-CAVERN_Y-2040',
        'GNR_H2S_H2-CAVERN_Y-2050'
    ]
    hydrogen_options_without_caverns = [option for option in hydrogen_options if option not in h2_caverns]


    return base_small_options, hydrogen_options_without_caverns, h2_caverns, base_medium_options, base_large_options

def industry_AGKN(AGKN: pd.DataFrame, print_options: bool = False):
    
    industry_options = {'LOWTEMP' : [],
                        'MIDTEMP' : [],
                        'HIGHTEMP' : []}
    area_names = {'LOWTEMP' : 'IND-LT',
                  'MIDTEMP' : 'IND-MT',
                  'HIGHTEMP' : 'IND-HT'}
    for heat_type in industry_options.keys():
        temp = AGKN.query(
            "A.str.contains('{}')".format(area_names[heat_type])
        )
        
        # Use this to inspect
        if print_options:
            print('\nCaptured areas:\n%s'%('\n'.join(temp.A.unique())))
            print('Investment options here:\n%s'%('\n'.join(temp.G.unique())))

        # Get base investment options and remove elements in wind_off_G from base_options (add hydrogen when the error arrives)
        industry_options[heat_type] = [option for option in temp.G.unique()]
    
    return industry_options

def individual_AGKN(AGKN: pd.DataFrame, print_options: bool = False):
       
    # Get individual investment options
    temp = AGKN.query(
        "A.str.contains('IDVU')"
    )
    
    ## Get rid of solar heating investments
    solar_heating = [
        'GNR_SH_SUN_SS-4-KW_Y-2020',
        'GNR_SH_SUN_SS-4-KW_Y-2030',
        'GNR_SH_SUN_SS-4-KW_Y-2040',
        'GNR_SH_SUN_SS-4-KW_Y-2050',
    ]
    
    # Get individual investment options
    individual_options = [option for option in temp.G.unique() if option not in solar_heating]
    
    # Use this to inspect 
    if print_options:
        print('\nCaptured areas:\n%s'%('\n'.join(temp.A.unique())))
        print('Investment options here:\n%s'%('\n'.join(temp.G.unique())))
        print('\nIndividual options without solar heating:\n%s'%('\n'.join(individual_options)))
        
    return individual_options

#%% ------------------------------- ###
###            2. Main              ###
### ------------------------------- ###

@click.command()
@click.option('--large-munis', type=str, required=True, help="The municipalities, where large scale investment options are allowed")
@click.option('--medium-munis', type=str, required=True, help="The municipalities, where medium scale investment options are allowed")
@click.option('--path-to-allendofmodel', type=str, required=False, help='A parameter')
def main(large_munis: str, medium_munis: str, path_to_allendofmodel: str):
    
    # Create file
    if not(os.path.exists('./Data/BalmorelData/AGKN_fromKountouris2024.gzip')):
        save_symbol_from_all_endofmodel('AGKN', ['A', 'G'], 'set', r'C:\Users\mathi\gitRepos\Balmorel\all_endofmodel.gdx')
    
    # Load files
    f = pd.read_parquet('./Data/BalmorelData/AGKN_fromKountouris2024.gzip')
    f = f.query('A.str.contains("DK")')

    # Make list of munis
    large_munis = large_munis.replace(' ', '').split(',')
    medium_munis = medium_munis.replace(' ', '').split(',')

    # 2.1 Get base options
    base_small_options, hydrogen_options, h2_caverns, base_medium_options, base_large_options = base_AGKN(f)
    
    ## Load base areas
    base_areas = pickle.load(open('Modules/Submodules/districtheat_sets.pkl', 'rb'))
    
    ## Make table for base
    incfile = IncFile(name='AGKN', path='Output',
                      prefix='\n'.join([
                          "* Defining small base investment options",
                          "SET BASE_INV_OPTIONS(GGG)",
                          "/",
                          "\n".join(base_small_options),
                          "/;",
                          "",
                          "",
                          "* Defining medium base investment options",
                          "SET MEDIUM_INV_OPTIONS(GGG)",
                          "/",
                          "\n".join(base_medium_options),
                          "/;",
                          "",
                          "",
                          "* Defining large base investment options",
                          "SET LARGE_INV_OPTIONS(GGG)",
                          "/",
                          "\n".join(base_large_options),
                          "/;",
                          "",
                          ""
                      ]),
                      suffix="\n".join([
                          "",
                          "$onmulti",
                          "$if     EXIST '../data/OFFSHORE_AGKN.inc'    $INCLUDE '../data/OFFSHORE_AGKN.inc';",
                          "$if not EXIST '../data/OFFSHORE_AGKN.inc' $INCLUDE '../../base/data/OFFSHORE_AGKN.inc';",
                          "$offmulti"
                      ]))
    incfile.body = "\n* Small scale options\n" + "\n".join(["AGKN('%s',GGG) = BASE_INV_OPTIONS(GGG);"%area for area in base_areas.values() if area not in medium_munis + large_munis]) + "\n"
    incfile.body += "\n* Medium scale options\n" + "\n".join(["AGKN('%s',GGG) = MEDIUM_INV_OPTIONS(GGG);"%area for area in base_areas.values() if area in medium_munis]) + "\n"
    incfile.body += "\n* Large scale options\n" + "\n".join(["AGKN('%s',GGG) = LARGE_INV_OPTIONS(GGG);"%area for area in base_areas.values() if area in large_munis]) + "\n"
    incfile.save()
    
    # 2.2 Get hydrogen options
    incfile = IncFile(name='HYDROGEN_AGKN', path='Output',
                      prefix='\n'.join([
                          "* Defining hydrogen investment options",
                          "SET H2_INV_OPTIONS(GGG)",
                          "/",
                          "\n".join(hydrogen_options),
                          "/;",
                          ""
                      ]),
                      suffix='')
    incfile.body = "\n".join([f"AGKN('{area}',GGG) = AGKN('{area}',GGG) + H2_INV_OPTIONS(GGG);" for area in base_areas.values()])
    # Add cavern option in Viborg (Lille Torup)
    incfile.body += "\n\n* Add cavern investment option in Viborg\n" + "\n".join([f"AGKN('Viborg_A','{g}') = YES;" for g in h2_caverns])
    incfile.save()
    
    
    # 2.3 Get industry options
    industry_options = industry_AGKN(f)
    
    ## Prepare .inc file
    incfile = IncFile(name='INDUSTRY_AGKN', 
                      path='Output',
                      prefix='', suffix='')
    
    ## Make tables
    temp_area_dict = {'LOWTEMP' : 'lt',
                      'MIDTEMP' : 'mt',
                      'HIGHTEMP' : 'ht'}

    for heat_type in industry_options.keys():
        incfile.prefix += "SET %s_INV_OPTIONS(GGG)\n/\n"%heat_type
        temp = pd.DataFrame(industry_options[heat_type])
        temp = temp.to_string(header=None, index=None, formatters={col: '{{:<{}}}'.format(temp[col].str.len().max()).format for col in temp.columns}, line_width=0)
        temp = '\n'.join([line.lstrip() for line in temp.split('\n')])
        incfile.prefix += temp
        incfile.prefix += "\n/;\n"
    
        ## Load industry heat area
        temp_area = pickle.load(open('Modules/Submodules/ind-%s_sets.pkl'%temp_area_dict[heat_type], 'rb'))
        incfile.body += "\n\n"
        incfile.body += "\n".join(["AGKN('%s',GGG) = %s_INV_OPTIONS(GGG);"%(area, heat_type) for area in temp_area.values()])
        
    incfile.save()


    # 2.4 Get individual options
    individual_options = individual_AGKN(f)
    
    ## Load individual areas
    individual_areas = pickle.load(open('Modules/Submodules/individual_sets.pkl', 'rb'))
    
    ## Make table for individual
    incfile = IncFile(name='INDIVUSERS_AGKN', path='Output',
                      prefix='\n'.join([
                          "* Defining individual user investment options",
                          "SET INDIVUSERS_INV_OPTIONS(GGG)",
                          "/",
                          "\n".join(individual_options),
                          "/;",
                          ""
                      ]),
                      suffix='')
    incfile.body = "\n".join(["AGKN('%s',GGG) = INDIVUSERS_INV_OPTIONS(GGG);"%area for area in individual_areas.values()])
    incfile.save()

if __name__ == '__main__':
    main()
