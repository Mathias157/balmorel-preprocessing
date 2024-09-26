#%%
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 22:51:15 2022

@author: Mathias Berg Rosendal, PhD, DTU Management

Use electricity transmission cost data from DEA2021:
https://ens.dk/en/our-services/projections-and-models/technology-data/technology-catalogue-transport-energy
A map of the extisting transmission grids:
https://energinet.dk/media/gqjj2xpk/eksisterende-net-2021.pdf <- DK

This is used to create demand files for Balmorel.

Assumption of how much a certain kV of transmission line can transmit of power
comes from: https://wise-answer.com/how-much-power-can-a-transmission-line-carry/
765 kV => 2200-2400 MW
500 kV => 900 MW
345 kV => 400 MW
*300 kV => 300 MW
*132 kV => 100 MW
*220 kV => 200 MW
GET A BETTER SOURCE!!! Look in power grid course material?
* = derived from three data assumptions (2nd degree assumption)


Power grid is manually drawed from: https://energinet.dk/media/ouufo5ll/eksisterende-net-2021.jpeg
NEED automatic source! (ENTSO-E data)

Works with the environment.yaml distributed in XXX
"""

import pickle
import pandas as pd
import geopandas as gpd
import shapely
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from Modules.geofiles import prepared_geofiles
from scipy.spatial import distance_matrix
from Submodules.municipal_template import DataContainer
from Submodules.utils import convert_names
import yaml
from pybalmorel import IncFile
        
        
#%% ----------------------------- ###
###     2. Calculate Distances    ###
### ----------------------------- ###

def get_distance_matrix(areas: gpd.GeoDataFrame):
    # Convert to geocentric coordinates for meter units
    areas = areas.to_crs(4328)

    ### 2.1 Calculate Distances
    # Use distance_matrix
    d = pd.DataFrame(
        distance_matrix(areas.geometry.apply(lambda polygon: (polygon.centroid.x, polygon.centroid.y)).tolist(),
                        areas.geometry.apply(lambda polygon: (polygon.centroid.x, polygon.centroid.y)).tolist()),
        index=areas.index,
        columns=areas.index
    )
    
    return d

def get_connections(areas: pd.DataFrame):
    X = pd.DataFrame(np.zeros((len(areas), len(areas))).astype(int),
                index=areas.loc[:, the_index],
                columns=areas.loc[:, the_index])
    X.index.name = 'IRRRE'
    X.columns.name = 'IRRRI'

def create_grid_incfiles(d: pd.DataFrame,
                         X: pd.DataFrame,
                         XE_cost: float,
                         XCOST_E: float,
                         XLOSS_E: float,
                         DCOST_E: float,
                         DLOSS_E: float,
                         carrier: str):
    
    if carrier == 'electricity':
        carrier_symbol = 'X'
        prefix = ''
    else:
        carrier_symbol = 'XH2'
        prefix = 'HYDROGEN_'
    
    ### 4.1 Transmission - ASSUMPTIONS
    # It is assumed that costs are symmmetrical
    D = d.sum().sum()/2  # Total, modelled length
    L = (d > 0).sum().sum()/2 # Total modelled lines

    XE = X * d * XE_cost # € pr. MW
    # XE = d * 3.1/2 # seems like 1.65 €/MW/m 

    ### 4.2 XINVCOST.inc
    # Remove names
    XE.columns.name = ''
    XE.index.name = ''

    # Add year
    XE.index = '2016 . ' + XE.index

    # Delete zeros
    XE = XE.replace(0, '')
    

    with open('./Output/%s%sINVCOST.inc'%(prefix, carrier_symbol), 'w') as f:
        f.write("TABLE %sINVCOST(YYY,IRRRE,IRRRI)        'Investment cost in new %s transmission capacity (Money/MW)'\n"%(carrier_symbol, carrier.capitalize()))
        dfAsString = XE.to_string(header=True, index=True)
        f.write(dfAsString)
        f.write('\n;')
        f.write("\n%sINVCOST(YYY,IRRRE,IRRRI) = %sINVCOST('2016',IRRRE,IRRRI);"%(carrier_symbol, carrier_symbol))
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
            
    ### 4.3 Energy losses
    XL = XLOSS_E * d

    ## Transmission
    # Adjust
    XL.columns.name = ''
    XL.index.name = ''
    XL = XL.replace(0, '')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    with open('./Output/%s%sLOSS.inc'%(prefix, carrier_symbol), 'w') as f:
        f.write("TABLE %sLOSS(IRRRE,IRRRI)        '%s transmission loss between regions (fraction)'\n"%(carrier_symbol, carrier.capitalize()))
        dfAsString = XL.to_string(header=True, index=True)
        f.write(dfAsString)
        f.write('\n;')



    ### 4.4 XCOST.inc                   
    xcost_e = X * XCOST_E
    xcost_e.index.name = ''
    xcost_e.columns.name = ''
    xcost_e = (
        xcost_e.astype(str)
        .replace(0, '')
    )

    with open('./Output/%s%sCOST.inc'%(prefix, carrier_symbol), 'w') as f:
        f.write("TABLE %sCOST(IRRRE,IRRRI)  '%s transmission cost between regions (Money/MWh)'\n"%(carrier_symbol, carrier.capitalize()))
        dfAsString = xcost_e.to_string(header=True, index=True)
        f.write(dfAsString)
        f.write('\n;')



    if carrier == 'electricity':
        ### 4.5 Distribution
        ## DISLOSS_E
        disloss_e = pd.DataFrame(data={'' : [DLOSS_E]*len(X.index)}, index=X.columns) # create losses
        disloss_e.index.name = ''
        disloss_e.columns.name = ''

        with open('./Output/%sDISLOSS_E.inc'%prefix, 'w') as f:
            f.write("PARAMETER DISLOSS_E(RRR)  'Loss in electricity distribution'              \n")
            f.write('/')
            dfAsString = disloss_e.to_string(header=True, index=True)
            f.write(dfAsString)
            f.write('\n/;')
            
            
        ## DISCOST_E
        discost_e = pd.DataFrame(data={'' : [DCOST_E]*len(X.index)}, index=X.columns) # create losses
        discost_e.index.name = ''
        discost_e.columns.name = ''

        with open('./Output/%sDISCOST_E.inc'%prefix, 'w') as f:
            f.write("PARAMETER DISCOST_E(RRR)  'Cost of electricity distribution (Money/MWh)'\n")
            f.write('/')
            dfAsString = discost_e.to_string(header=True, index=True)
            f.write(dfAsString)
            f.write('\n/;')

def create_tech_specific_distribution_loss(wind_offshore_loss: dict,
                                           industry_loss: float,
                                           individual_loss: float):
    # Offshore wind
    # RG1 = 0.1
    # RG2 and RG3 = 0.2
    f = IncFile(name='DISLOSS_E_AG', path='Output',
                prefix='\n'.join([
                        "PARAMETER DISLOSS_E_AG(AAA,GGG)  'Loss in electricity distribution associated to specific technology in a particular area';",
                        "*Source for offshore losses: https://www.sciencedirect.com/science/article/pii/S0378779605002609",
                        ""
                    ]),
                body='\n'.join([
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDTECHGROUP') EQ WINDTURBINE_OFFSHORE AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG1']};",
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDSUBTECHGROUP') EQ RG2_OFF1 AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG2']};",
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDSUBTECHGROUP') EQ RG2_OFF2 AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG2']};",
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDSUBTECHGROUP') EQ RG2_OFF3 AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG2']};",
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDSUBTECHGROUP') EQ RG2_OFF4 AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG2']};",
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDSUBTECHGROUP') EQ RG2_OFF5 AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG2']};",
                        "*Offshore type 3                                                                                         ",
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDSUBTECHGROUP') EQ RG3_OFF1 AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG3']};",
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDSUBTECHGROUP') EQ RG3_OFF2 AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG3']};",
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDSUBTECHGROUP') EQ RG3_OFF3 AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG3']};",
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDSUBTECHGROUP') EQ RG3_OFF4 AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG3']};",
                        f"DISLOSS_E_AG(IA,G)$(GDATA(G,'GDSUBTECHGROUP') EQ RG3_OFF5 AND (AGKN(IA,G) OR SUM(Y, GKFX(Y,IA,G))))={wind_offshore_loss['RG3']};",
                    ]))
    f.save()    

    
    # Industry
    set = pickle.load(open('Modules/Submodules/ind-ht_sets.pkl', 'rb'))
    f = IncFile(name='INDUSTRY_DISLOSS_E_AG', path='Output',
                prefix='\n'.join([
                        "PARAMETER DISLOSS_E_AG_IND(AAA,GGG)  'Loss in electricity distribution associated to specific technology in a particular area' ;",
                        ""
                    ]),
                suffix='\n'.join([
                    "",
                    "DISLOSS_E_AG(IA,G)$DISLOSS_E_AG_IND(IA,G)= DISLOSS_E_AG_IND(IA,G);",
                    "DISLOSS_E_AG_IND(IA,G)=0;" 
                ])
                )   
    for temp_area in ['-LT', '-MT', '-HT']:
        for area in set.values():
            replaced_area = area.replace('-HT', temp_area)
            f.body += f"DISLOSS_E_AG_IND('{replaced_area}',G)$((GDATA(G,'GDTYPE') EQ GETOH OR  GDATA(G,'GDTYPE') EQ GESTO OR GDATA(G,'GDTYPE') EQ GESTOS)  AND (SUM(Y,GKFX(Y,'{replaced_area}',G)) OR AGKN('{replaced_area}',G)))={industry_loss};\n"
    f.save()
    
    # Individual
    set = pickle.load(open('Modules/Submodules/individual_sets.pkl', 'rb'))
    f = IncFile(name='INDIVUSERS_DISLOSS_E_AG', path='Output',
                prefix='\n'.join([
                        "PARAMETER DISLOSS_E_AG_INDIVUSERS(AAA,GGG)  'Loss in electricity distribution associated to specific technology in a particular area' ;",
                        ""
                    ]),
                suffix='\n'.join([
                    "",
                    "DISLOSS_E_AG(IA,G)$DISLOSS_E_AG_INDIVUSERS(IA,G)= DISLOSS_E_AG_INDIVUSERS(IA,G);",
                    "DISLOSS_E_AG_INDIVUSERS(IA,G)=0;"
                ])
                )   
    f.body += "\n".join([f"DISLOSS_E_AG_INDIVUSERS('{area}',G)$((GDATA(G,'GDTYPE') EQ GETOH OR  GDATA(G,'GDTYPE') EQ GESTO OR GDATA(G,'GDTYPE') EQ GESTOS)  AND (SUM(Y,GKFX(Y,'{area}',G)) OR AGKN('{area}',G)))={individual_loss};" for area in set.values()])
    f.save()                                                                                                                                                                                                                                                                      



def main():
    
    # 1. Load Inputs
    # Load configuration from snakeconfig.yaml
    with open('assumptions.yaml', 'r') as file:
        config = yaml.safe_load(file)

    XE_cost = config['grid_assumptions']['electricity']['investment_cost'] # €/MW/m high bound
    XT = config['grid_assumptions']['electricity']['lifetime'] # Lifetime of grid elements
    XLOSS_E = config['grid_assumptions']['electricity']['transmission_loss'] # fraction of loss pr. m, From Balmorel DK1-DK2 line
    XCOST_E = config['grid_assumptions']['electricity']['transmission_cost'] # €/MWh Transmission costs
    DLOSS_E = config['grid_assumptions']['electricity']['distribution_loss'] # Distribution loss
    DCOST_E = config['grid_assumptions']['electricity']['distribution_cost'] # €/MWh distribution cost 
    XH2E_cost = config['grid_assumptions']['hydrogen']['investment_cost'] # €/MW/m high bound
    XH2T = config['grid_assumptions']['hydrogen']['lifetime'] # Lifetime of grid elements
    XH2LOSS_E = config['grid_assumptions']['hydrogen']['transmission_loss'] # fraction of loss pr. m, From Balmorel DK1-DK2 line
    XH2COST_E = config['grid_assumptions']['hydrogen']['transmission_cost'] # €/MWh Transmission costs
    
    # 2. Get Distance Matrix
    x = DataContainer()
    geofile = x.get_polygons()
    geofile.index = (
        geofile
        .index
        .str.replace('Æ', 'Ae')
        .str.replace('Ø', 'Oe')
        .str.replace('Å', 'Aa')
        .str.replace('æ', 'ae')
        .str.replace('ø', 'oe')
        .str.replace('å', 'aa')
    )
    d = get_distance_matrix(geofile)
    
    # 3. Get connections
    f = xr.load_dataset("Data/BalmorelData/municipal_connectivity.nc")
    f, fnew = convert_names('Modules/Submodules/exo_grid_conversion_dictionaries.pkl',
                      f, 'connection')
    ## Convert to dataframe
    X = (
        fnew
        .to_dataframe()
        .pivot_table(
            index='IRRRE', 
            columns='IRRRI', 
            values='connection',
            aggfunc='sum'
        )
    )
    ## Check validity
    assert np.all(X < 2), 'Double connection counts for some reason?'
    
    # 4. Generate .inc files
    create_grid_incfiles(d, X, XE_cost, XCOST_E, XLOSS_E, DCOST_E, DLOSS_E, 'electricity')
    create_grid_incfiles(d, X, XH2E_cost, XH2COST_E, XH2LOSS_E, DCOST_E, DLOSS_E, 'hydrogen')


    # 5. Generate tech specific distribution loss
    wind_offshore_loss = {'RG1' : 0.1, 'RG2' : 0.2, 'RG3' : 0.2}
    industry_loss = config['grid_assumptions']['electricity']['industry_technologies'] # €/MWh Transmission costs
    individual_loss = config['grid_assumptions']['electricity']['individual_technologies'] # €/MWh Transmission costs
    
    create_tech_specific_distribution_loss(wind_offshore_loss, industry_loss, individual_loss)

if __name__ == '__main__':
    
    run_old_script = False
    if not(run_old_script):
        main()
        
    else:
        #%%     
        style = 'report'

        if style == 'report':
            plt.style.use('default')
            fc = 'white'
        elif style == 'ppt':
            plt.style.use('dark_background')
            fc = 'none'

        #%% ----------------------------- ###
        ###         0. ASSUMPTIONS        ###
        ### ----------------------------- ###

        # 0.1 Choice of spatial aggregation
        # choice = 'DK municipalities'
        # choice = 'NUTS3'
        # choice = 'NUTS2'
        # choice = 'NordpoolReal'
        # choice = 'BalmorelVREAreas'
        choice = 'Antbalm'

        # 0.2 Parameters
        growth = 10 # Maximum growth of areas with no grid connection in km
        growth_step = 1 # Step towards maximum growth in km
        # transmission
        # From DEA 2021, 111 'Main distribution grid' (no data for transmission? these costs are for 50/60 kV)
        XE_cost = 3.1 # €/MW/m high bound
        XE_cost = 150/1e3 # €/MW/m repurposed H2 onshore 
        # XE_cost = 2.511 # €/MW/m low bound
        # XE_cost = 2.175 # €/MW/m actual transmission data: Maxwell Brown, Wesley Cole, Kelly Eurek, Jonathon Becker, David Bielen, Ilya Chernyakhovskiy, Stuart Cohen, Allister Frazier, Pieter Gagnon, Nathaniel Gates, et al. Regional energy deployment system (reeds) model documentation: Version 2019. Technical report, National Renewable Energy Lab.(NREL), Golden, CO (United States), 2020.
        XE_substation_cost = 76000 # €/MW very high bound
        # XE_substation_cost = 4476 # €/MW low bound
        # XE_substation_cost = 0 # No cost
        XE_FOM = 21.7/1e3 # €/MW/m/year
        Xsub = 99 # Amount of substations (assumed similar to today ~ one pr. municipality)
        XT = 40 # Lifetime of grid elements
        XT = 50 # Lifetime of H2 pipes

        XLOSS_E = 3.318383e-08 # fraction of loss pr. m, From Balmorel DK1-DK2 line
        XCOST_E = 0.0001 # €/MWh Transmission costs
        DLOSS_E = 0.05 # Distribution loss
        DCOST_E = 5 # €/MWh distribution cost 

        ### See more assumptions in sections
        # 2.2 - Manual adjustments to links between regions
        # 2.5 - Automatic XKFX through power line input data does not work for regions that do not touch! (e.g. across sea)
        # 4.1 - Assumed symmetrical lines
        # 4.3 - Assuming same distribution loss in all regions!!!

        #%% ----------------------------- ###
        ###        1. Read files          ###
        ### ----------------------------- ###

        ### 1.1 Load geodata
        the_index, areas, country_code = prepared_geofiles(choice)
        # areas = areas[(areas[country_code] == 'DK') | (areas[country_code] == 'DE')] # Testing DK and DE


        if 'nuts' in choice.lower():
            areas = areas[areas.CNTR_CODE == 'DK']
        elif 'nordpool' == choice.lower():
            # idx = ((areas.index.str.find('DK') != -1) | (areas.index.str.find('SE') != -1) | (areas.index.str.find('NO') != -1)) & (areas.index.str.find('IT') == -1)
            idx = (areas.index.str.find('DK') != -1) 
            areas = areas[idx]
        elif 'nordpoolreal' == choice.lower():
            areas = areas[areas.RRR != 'RU']
        elif 'antbalm' == choice.replace(' ', '').lower():
            areas = areas[(areas.ADMIN != 'Russia')]
            
        ### 1.2 Load power grid data
        PL = pd.read_csv("Data/Power Grid/entsoe/links.csv", quotechar="'")
        PL.geometry = PL.geometry.apply(lambda x: shapely.wkt.loads(x))
        PL = gpd.GeoDataFrame(PL)

        # Filter no voltage away
        idx = PL.voltage.isna()
        PL = PL[~idx]

        # Plot
        fig, ax = plt.subplots(1)
        areas.plot(ax=ax)
        PL.plot(ax=ax, color='k')
        # plt.xlim([7, 16])
        # plt.ylim([54, 59])
        # plt.xlim([7, 16])
        # plt.ylim([54, 59])

        ### 1.3 Assume capacities 
        kVtoMW = {132 : 100, 220 : 200,
                300 : 300, 380 : 400,
                500 : 900, 750 : 2200}


        # Assert capacities
        for kV in kVtoMW:
            idx = PL.voltage == kV
            PL.loc[idx, 'Cap (MW)'] = kVtoMW[kV]


        #%% ----------------------------- ###
        ###     2. Calculate Distances    ###
        ### ----------------------------- ###

        def get_distance_matrix2(areas: gpd.GeoDataFrame,
                                choice: str):
            # Convert to geocentric coordinates for meter units
            if choice.lower().replace(' ','') == 'nordpoolreal':
                areas.crs = 4326 

            areas = areas.to_crs(4328)

            ### 2.1 Calculate Distances
            # Use distance_matrix
            d = pd.DataFrame(
                distance_matrix(areas.geometry.apply(lambda polygon: (polygon.centroid.x, polygon.centroid.y)).tolist(),
                                areas.geometry.apply(lambda polygon: (polygon.centroid.x, polygon.centroid.y)).tolist()),
                index=areas.index,
                columns=areas.index
            )
            
            return d
        d = get_distance_matrix2(areas, choice)

        #%% ----------------------------- ###
        ###        3. Create XKFX         ###
        ### ----------------------------- ###

        use_buffering = False    
        max_dist = 500000 # m

        ### 3.1 Create matrix for possible grid connections, using buffering and touching
        if use_buffering:
            X = pd.DataFrame(np.zeros((len(areas), len(areas))).astype(int),
                            index=areas.loc[:, the_index],
                            columns=areas.loc[:, the_index])
            X.index.name = 'IRRRE'
            X.columns.name = 'IRRRI'

            # Use touches or intersects for areas not separated
            buffering = 1 # minimum 0.000001 to take care of invalid geometries
            for i,a in areas.iterrows():
                # Index for touching regions
                idx = areas.touches(a.geometry.buffer(buffering))
                
                # Assign possible links
                X.loc[a[the_index], areas.loc[idx, the_index]] = 1

            # MAYBE ADD THAT IF NO ONE IS TOUCHING, THE CLOSEST ONES SHOULD BE CONNECTED?
            # Could solve over-seas-interconnector issue    
            # However, won't solve if several regions on each side of ocean!

        ### 3.2 Using max distance
        else:
            X = d.copy().values
            mask1 = X > max_dist
            mask2 = X <= max_dist 
            X[mask1] = 0 
            X[mask2] = 1
            X = pd.DataFrame(X, columns=areas.index, index=areas.index)

        ### 3.3 Manual Adjustments - ASSUMPTIONS
        # Find those with no grids
        no_grids = list(X.columns[~X.any()])

        # Semi-manual expansion 
        # for a in no_grids:
        #     A = areas.loc[areas.loc[:,the_index] == a, :]
        #     for step in np.arange(0, growth, growth_step):
        #         temp = areas[areas.overlaps(A.geometry.buffer(step*1e4))]
        #         if not(len(temp) == 0):
        #             temp.plot()
        #             print(temp)

        ## Manual
        if choice.lower().replace(' ', '') == 'dkmunicipalities':
            # Skærbæk-Fyn
            X.loc['DK_5_8_1', 'DK_5_13_1'] = 1
            # Nyborg-Sjælland
            X.loc['DK_4_13_1', 'DK_5_15_1'] = 1
            # Guldborgsund-Vordingborg
            X.loc['DK_4_3_1', 'DK_4_17_1'] = 1
            # Vordingborg-Næstved
            X.loc['DK_4_9_1', 'DK_4_17_1'] = 1
            # Lolland-Langeland
            X.loc['DK_4_8_1', 'DK_5_12_1'] = 1
            # Langeland-Svendborg
            X.loc['DK_5_12_1', 'DK_5_18_1'] = 1
            # Sønderborg-Faaborg-Midtfyn
            X.loc['DK_5_6_1', 'DK_5_17_1'] = 1
            # Samsø-Kalundborg
            X.loc['DK_2_13_1', 'DK_4_5_1'] = 1
            # Samsø-Midtjylland
            X.loc['DK_2_10_1', 'DK_2_13_1'] = 1
            # Frederikshavn-Læsø
            X.loc['DK_3_3_1', 'DK_3_6_1'] = 1
            # Haderslev-Assens
            X.loc['DK_5_3_1', 'DK_5_9_1'] = 1
            # Skive-Morsø
            X.loc['DK_2_16_1', 'DK_3_8_1'] = 1
            # Morsø-Thisted
            X.loc['DK_3_8_1', 'DK_3_10_1'] = 1
            # Morsø-Vesthimmerland
            X.loc['DK_2_16_1', 'DK_3_11_1'] = 1
            
            
        elif choice.lower() == 'nuts3':
            # Fyn
            X.iloc[2, 7] = 1
            X.iloc[2, 8] = 1
            X.iloc[2, 9] = 1   
            
            # Bornholm
            # X.iloc[4, 8] = 1
        elif choice.lower() == 'nuts2':
            X.iloc[0, 3] = 1
        elif choice.lower() == 'nordpool':
            X.iloc[0, 1] = 1

        # Symmetry
        for i,row in X.iterrows():
            X.loc[:,i] = X.loc[i, :]

        ### 2.3 Plot for inspection
        fig, ax = plt.subplots(facecolor=fc)
        areas.plot(ax=ax, zorder=2, edgecolor='k')

        line_center_x = []
        line_center_y = []
        for a in X.index:
            idx = X[a] == 1
            # temp = 
            # print(areas.set_index(the_index)[idx].plot())
            A = areas.loc[areas.loc[:,the_index] == a, :]
            
            # Plot centroid lines
            for i,l in areas[idx].iterrows():
                
                p, = ax.plot([A.geometry.centroid.x, l.geometry.centroid.x],
                        [A.geometry.centroid.y, l.geometry.centroid.y], 'r-')

        #%%

        ### 2.4 Create XKFX
        XKFX = X.copy()*0

        ### 2.5 Find intersects between power grid data and polygons
        areas = areas.to_crs(4326) # Back from meter-precise crs
        for i,line in PL.iloc[:].iterrows():
            
            # Intersects between areas and line i    
            idx = areas.geometry.intersects(line.geometry)
            
            # Make overlay - how to make XKFX between disconnected polygons..?
            # OV = gpd.GeoDataFrame({'geometry' : areas[idx].geometry.union(line.geometry)})
            
            # Find touching regions within line intersects
            for j,poly in areas[idx].iterrows():
                idx2 = areas[idx].touches(areas[idx].geometry[j])
                As = areas[idx][idx2].loc[:,the_index] # The names of the areas touching area j (poly)
                XKFX.loc[poly[the_index],As] = XKFX.loc[poly[the_index],As] + line['Cap (MW)']
            # for j,poly in OV.iterrows():
            #     idx2 = OV.touches(OV[idx].geometry[j])
            #     As = OV[idx2].loc[:,the_index] # The names of the areas touching area j (poly)
            #     XKFX.loc[poly.name,As] = XKFX.loc[poly.name,As] + line['Cap (MW)']


        ### 2.6 Save XKFX
        XKFX.columns.name = ''
        XKFX.index.name = ''
        XKFX.index = '2016 . ' + XKFX.index 
        XKFX = XKFX.astype(str).replace('0', '')
        with open('./Output/XKFX.inc', 'w') as f:
            f.write("TABLE XKFX(YYY,IRRRE,IRRRI)  'Initial transmission capacity between regions'\n")
            dfAsString = XKFX.to_string(header=True, index=True)
            f.write(dfAsString)
            f.write('\n;\n')
            f.write("XKFX(YYY,IRRRE,IRRRI)$(YYY.VAL GT 2016) = XKFX('2016',IRRRE,IRRRI);")

        """
        What's missing in the municipality model, due to lacking method of connecting overseas regions:

        * Storebælt
        XKFX(YYY,'DK_4_13_1','DK_5_15_1') = 600;
        XKFX(YYY,'DK_5_15_1', 'DK_4_13_1') = 590;  

        * Frederikshavn-Læsø
        XKFX(YYY,'DK_3_6_1','DK_3_3_1') = 740;
        XKFX(YYY,'DK_3_3_1', 'DK_3_6_1') = 740; 

        * Fredericia-Middelfart
        XKFX(YYY,'DK_5_8_1','DK_5_13_1') = 1200;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             
        XKFX(YYY,'DK_5_13_1','DK_5_8_1') = 1200;


        * Slagelse-Lolland
        XKFX(YYY,'DK_4_13_1','DK_4_8_1') = 400;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
        XKFX(YYY,'DK_4_8_1','DK_4_13_1') = 400;


        * Guldborgssund-Vordingborg
        XKFX(YYY,'DK_4_3_1','DK_4_17_1') = 400;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
        XKFX(YYY,'DK_4_17_1','DK_4_3_1') = 400;
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                    
        * Morsø-Skive
        XKFX(YYY,'DK_3_8_1','DK_2_16_1') = 200;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
        XKFX(YYY,'DK_2_16_1','DK_3_8_1') = 200;


        * Morsø-Thisted
        XKFX(YYY,'DK_3_8_1','DK_3_10_1') = 200;                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
        XKFX(YYY,'DK_3_10_1','DK_3_8_1') = 200;
                                                
        """


        #%% ----------------------------- ###
        ###         4. Save Costs         ###
        ### ----------------------------- ###


        ### 4.1 Transmission - ASSUMPTIONS
        # It is assumed that costs are symmmetrical
        D = d.sum().sum()/2  # Total, modelled length
        L = (d > 0).sum().sum()/2 # Total modelled lines

        XE = X * d * XE_cost # € pr. MW
        # XE = d * 3.1/2 # seems like 1.65 €/MW/m 

        ### 4.2 XINVCOST.inc
        # Remove names
        XE.columns.name = ''
        XE.index.name = ''

        # Add year
        XE.index = '2016 . ' + XE.index

        # Delete zeros
        XE = XE.replace(0, '')

        with open('./Output/XINVCOST.inc', 'w') as f:
            f.write("TABLE XINVCOST(YYY,IRRRE,IRRRI)        'Investment cost in new transmission capacity (Money/MW)'\n")
            dfAsString = XE.to_string(header=True, index=True)
            f.write(dfAsString)
            f.write('\n;')
            f.write("\nXINVCOST(YYY,IRRRE,IRRRI) = XINVCOST('2016',IRRRE,IRRRI);")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                
        ### 4.3 Energy losses
        XL = XLOSS_E * d

        ## Transmission
        # Adjust
        XL.columns.name = ''
        XL.index.name = ''
        XL = XL.replace(0, '')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
        with open('./Output/XLOSS.inc', 'w') as f:
            f.write("TABLE XLOSS(IRRRE,IRRRI)        'Transmission loss between regions (fraction)'\n")
            dfAsString = XL.to_string(header=True, index=True)
            f.write(dfAsString)
            f.write('\n;')



        ### 4.4 XCOST.inc                   
        xcost_e = X * XCOST_E
        xcost_e.index.name = ''
        # xcost_e.columns.name = ''
        xcost_e = xcost_e.replace(0, '')

        with open('./Output/XCOST.inc', 'w') as f:
            f.write("TABLE XCOST(IRRRE,IRRRI)  'Transmission cost between regions (Money/MWh)'\n")
            dfAsString = xcost_e.to_string(header=True, index=True).replace(the_index, '')
            f.write(dfAsString)
            f.write('\n;')




        ### 4.5 Distribution
        ## DISLOSS_E
        disloss_e = pd.DataFrame(data={'' : [DLOSS_E]*len(areas.index)}, index=areas.index) # create losses
        disloss_e.index.name = ''
        disloss_e.columns.name = ''

        with open('./Output/DISLOSS_E.inc', 'w') as f:
            f.write("PARAMETER DISLOSS_E(RRR)  'Loss in electricity distribution'              \n")
            f.write('/')
            dfAsString = disloss_e.to_string(header=True, index=True).replace(the_index, '')
            f.write(dfAsString)
            f.write('\n/;')
            
            
        ## DISCOST_E
        discost_e = pd.DataFrame(data={'' : [DCOST_E]*len(areas.index)}, index=areas.index) # create losses
        discost_e.index.name = ''
        discost_e.columns.name = ''

        with open('./Output/DISCOST_E.inc', 'w') as f:
            f.write("PARAMETER DISCOST_E(RRR)  'Cost of electricity distribution (Money/MWh)'\n")
            f.write('/')
            dfAsString = discost_e.to_string(header=True, index=True).replace(the_index, '')
            f.write(dfAsString)
            f.write('\n/;')
            
            

                
            
            
            
            
            
            
            
            
        #%% This was used to create individual statements:
        for ind in d:
            if 'NOS' in ind:
                idx = d.loc[ind] < 1000000
                d0 = d.loc[ind, idx]
                print('* %s'%ind)
                for indI in d0.index:
                    # print("XH2INVCOST('2030','%s','%s') \t= %0.2f * %0.4f;"%(ind, indI, d0[indI], XE_cost))
                    # print("XH2INVCOST('2030','%s','%s') \t= %0.2f * %0.4f;"%(indI, ind, d0[indI], XE_cost))
                    print("XH2LOSS('%s','%s') \t= %0.2f * 2.3e-05;"%(ind, indI, d0[indI]))
                    print("XH2LOSS('%s','%s') \t= %0.2f * 2.3e-05;"%(indI, ind, d0[indI]))