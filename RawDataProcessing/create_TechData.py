#%%
"""
Created on 24/04/2023

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)

This script creates input data for technoeconomic assumptions.
Most technologies come from the technology catalogue of the Danish Energy Agency:
    - District Heating and Power Generation, June 2022 https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-generation-electricity-and
    - Renewable Fuels, March 2023 https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-renewable-fuels
    - Energy Storage, January 2020 https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-energy-storage

"""

import matplotlib.pyplot as plt
from matplotlib import rc
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon, Point, LineString
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Proj
from Modules.geofiles import *

### Plot settings
style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

def get_value(search_series, search_strings, y0, y1, den, y0_dif):
    """
    Gets value by interpolation
    """
    idx = search_series == search_series
    for string in search_strings:
        idx = idx & (search_series.str.find(string) != -1)
        
    C0 = temp.loc[idx & (temp.year == y0), 'val'].values[0]
    C1 = temp.loc[idx & (temp.year == y1), 'val'].values[0]
    a = (C1 - C0) / den
    CY = C0 + y0_dif*a
    return CY

### ------------------------------- ###
###          0. ASSUMPTIONS         ###
### ------------------------------- ###

### 0.1 Choose technologies in power and heat
techs_to_add = ['Gas turbine, combined cycle - extraction - natural gas - large']

### 0.2 Choose spatial resolution
# choice = 'BalmorelVREAreas'
choice = 'NordpoolReal'

### 0.3 Choose Yearly Resolution (Will interpolate when data not available)
y_start = 2020
y_stop = 2050
y_step = 5 # years

### 0.4 Which estimate to use
est = 'ctrl' # 'ctrl' for mean estimate, 'lower' for lower and 'upper' for upper

### 0.X Other configurations



#%% ------------------------------- ###
###           1. Load Data          ###
### ------------------------------- ###

### 1.1 Configurations
## GDATA string
GDATASTRING1 = "Generation type Fuel type   Cv-value for CHP-Ext Cb-value for CHP  Fuel efficiency   CH4-factor (mg/MJ) NOx-factor (mg/MJ) Degree of desulphoring Investment cost (MMoney/MW)(default value) Annual operating and maintenance costs (kMoney/MW)(default value) Variable operating and maintenance cost relative to output (Money/MWh) (default value) Variable operating and maintenance cost relative to input (Money/MWh)(default value) Technology available for investments from this year Economic lifetime (years) Capacity is a variable to be found for each year (1/0) Technology investment expires from this year (blank or 0 implies no expiration) Year when a unit is mothballed Hours to load storage Hours to unload storage Combination technology                                                                                                                       Combination technology, maximum share of capacity Combination technology, minimum share of production Combination technology, maximum share of production Combination technology, capacity reserved for specific subunit Combination technology, capacity limited by input capacity Loss when loading a storage (MWh loss/MWh loading input) Stationary loss from storage (MWh loss per time period/MWh energy content in storage) Unit commitment: the unit participates in unit commitment (0/1) Standard size of unit type (MW) Unit commitment: minimum production (share of nominal capacity) Unit commitment: startup cost (Money) Unit commitment: fixed hourly cost (Money/MW) Unit commitment: fixed hourly fuel use (MWh) Unit commitment: shutdown cost (Money) Unit commitment: minimum down time (hours) Unit commitment: minimum up time (hours) Unit commitment: duration of shut down process (hours) Unit commitment: duration of start up process (hours) Unit commitment: ramp-up limit (% of capacity/h) Unit commitment: ramp-down limit (% of capacity/h) CHP turbine can be bypassed for heat production Technology group           SubTechnology group Technology allowed to be decomissioned ([0;1]) 'Forced Outage Rate (fraction)' 'Annual planned maintenance (hours)'"
GDATASTRING2 = "GDTYPE	GDFUEL	GDCV	GDCB	GDFE	GDCH4	GDNOX	GDDESO2	GDINVCOST0	GDOMFCOST0	GDOMVCOST0	GDOMVCOSTIN	GDFROMYEAR	GDLIFETIME	GDKVARIABL	GDLASTYEAR	GDMOTHBALL	GDSTOHLOAD	GDSTOHUNLD	GDCOMB	GDCOMBGUP	GDCOMBGSHAREK1	GDCOMBFUP	GDCOMBFSHAREK1	GDCOMBGSHARELO	GDCOMBGSHAREUP	GDCOMBFSHARELO	GDCOMBFSHAREUP	GDCOMBSK	GDCOMBSLO	GDCOMBSUP	GDCOMBKRES	GDCOMBFCAP	GDLOADLOSS	GDSTOLOSS	GDUC	GDUCUNITSIZE	GDUCGMIN	GDUCUCOST	GDUCCOST0	GDUCF0	GDUCDCOST	GDUCDTMIN	GDUCUTMIN	GDUCDURD	GDUCDURU	GDUCRAMPU	GDUCRAMPD	GDBYPASSC	GDTECHGROUP	GDSUBTECHGROUP	GDDECOM	GDFOR	GDPLANMAINT".split('\t')

## Placeholder GDATA file
GDATA = pd.DataFrame(data={}, columns=GDATASTRING2)

## Dictionary for converting terminology
eldh2balm = {'type' : 'GDTYPE'}

eldh2TYPE = {'back pressure' : 'GBPR',
            'extraction' : 'GEXT',
            'renewable power' : 'REN'}
eldh2TECH = {'Gas turbine, combined cycle' : 'CCGT'}

## Read all data
felDH = pd.read_excel('./Data/Technology Data/technology_data_for_el_and_dh.xlsx', sheet_name='alldata_flat')

## Read shapefile data
the_index, areas, country_code = prepared_geofiles(choice)
areas = areas[(areas[country_code] == 'DK') | (areas[country_code] == 'DE')] # Testing DK and DE
areas.plot()



#%% ------------------------------------- ###
###  2. Create Techs (Non-Area Specific)  ###
### ------------------------------------- ###
GDATA = pd.DataFrame(data={}, columns=GDATASTRING2)


## IMPLEMENT PRICEYEAR CALCULATION! The data exist
# Do PriceyearModel - Priceyeardata ... calibrate inflation

y_range = np.arange(y_start, y_stop + 1, y_step) # Specified Balmorel simulation years
for tech in techs_to_add:
    idx = felDH.technology == tech    
    y_data = felDH[idx].year.unique() # Actual data for years in tech
    # print(y_data)
    
    if True:
        carrier_output = 'MWh_e' # Only electricity producers for now
        
    for y in y_range:
        
        # Check difference from data years
        y_dif = y - y_data
        
        # Years for interpolation (works if y is a year with available data as well)
        y0_dif = min(y_dif[y_dif > 0])
        y1_dif = max(y_dif[y_dif <= 0])
        y0 = y_data[y_dif == y0_dif][0]
        y1 = y_data[y_dif == y1_dif][0]
        den = y1 - y0 # Denominator
        
        # Get data
        temp = felDH[(felDH.technology == tech) & ((felDH.year == y0) | (felDH.year == y1)) & (felDH.est == est)]
        search_series = pd.Series(temp.par)

        ## Technology name
        tech_name = 'GNR_GT_NGAS_EXT_Y-%d'%y
        GDATA.loc[tech_name, :] = '' # All empty to avoid NaNs when inserting data later
        # print(y)
        
        ## Investment Cost
        idx = search_series.str.find('Nominal investment (*total)') != -1
        C0 = temp.loc[idx & (temp.year == y0), 'val'].values[0]
        C1 = temp.loc[idx & (temp.year == y1), 'val'].values[0]
        a = (C1 - C0) / den
        CY = C0 + y0_dif*a
        CY = get_value(search_series, ['Nominal investment (*total)'], y0, y1, den, y0_dif)
        # print(CY)
        
        GDATA.loc[tech_name, 'GDINVCOST0'] = CY
        
        ## Fixed OM
        idx = search_series.str.find('Fixed O&M (*total)') != -1
        C0 = temp.loc[idx & (temp.year == y0), 'val'].values[0]/1e3 
        C1 = temp.loc[idx & (temp.year == y1), 'val'].values[0]/1e3 
        a = (C1 - C0) / den
        CY = C0 + y0_dif*a
        CY = get_value(search_series, ['Fixed O&M (*total)'], y0, y1, den, y0_dif) / 1e3 # in k€/MW
        # print(CY)
        
        GDATA.loc[tech_name, 'GDOMFCOST0'] = CY    
        
        
        ## Variable OM
        idx = (search_series.str.find('Variable O&M (*total)') != -1) & (search_series.str.find(carrier_output) != -1)
        C0 = temp.loc[idx & (temp.year == y0), 'val'].values[0]
        C1 = temp.loc[idx & (temp.year == y1), 'val'].values[0]
        a = (C1 - C0) / den
        CY = C0 + y0_dif*a
        CY = get_value(search_series, ['Variable O&M (*total)', carrier_output], y0, y1, den, y0_dif)
        # print(CY)
        
        GDATA.loc[tech_name, 'GDOMVCOST0'] = CY    
    
        ## Cv
        idx = search_series.str.find('Cv coefficient') != -1
        C0 = temp.loc[idx & (temp.year == y0), 'val'].values[0]
        C1 = temp.loc[idx & (temp.year == y1), 'val'].values[0]
        a = (C1 - C0) / den
        CY = C0 + y0_dif*a
        CY = get_value(search_series, ['Cv coefficient'], y0, y1, den, y0_dif)
        # print(CY)
        
        GDATA.loc[tech_name, 'GDCV'] = CY

        ## Cb
        idx = search_series.str.find('Cb coefficient') != -1
        C0 = temp.loc[idx & (temp.year == y0), 'val'].values[0]
        C1 = temp.loc[idx & (temp.year == y1), 'val'].values[0]
        a = (C1 - C0) / den
        CY = C0 + y0_dif*a
        CY = get_value(search_series, ['Cb coefficient'], y0, y1, den, y0_dif)
        # print(CY)
        
        GDATA.loc[tech_name, 'GDCB'] = CY
        
        ## Efficiency 
        idx = search_series.str.find('Electrical efficiency (net, annual average)') != -1
        C0 = temp.loc[idx & (temp.year == y0), 'val'].values[0]
        C1 = temp.loc[idx & (temp.year == y1), 'val'].values[0]
        a = (C1 - C0) / den
        CY = C0 + y0_dif*a
        CY = get_value(search_series, ['Electrical efficiency (net, annual average)'], y0, y1, den, y0_dif)
        # print(CY)
        
        GDATA.loc[tech_name, 'GDFE'] = CY
        
        ## Lifetime 
        idx = search_series.str.find('Technical lifetime') != -1
        C0 = temp.loc[idx & (temp.year == y0), 'val'].values[0]
        C1 = temp.loc[idx & (temp.year == y1), 'val'].values[0]
        a = (C1 - C0) / den
        CY = C0 + y0_dif*a
        CY = get_value(search_series, ['Technical lifetime'], y0, y1, den, y0_dif)
        # print(CY)
        
        GDATA.loc[tech_name, 'GDLIFETIME'] = round(CY)
        
        ## Invest available from year
        GDATA.loc[tech_name, 'GDFROMYEAR'] = y
        
        ## Invest no longer available from year
        GDATA.loc[tech_name, 'GDLASTYEAR'] = round(y + y_step - 1)
        
        ### Save all necessary GDATA components
        # G = '_'.join(('GNR', ))
        ### Make interpolation between cost projection data using y_step  


GDATA.loc[:, 'GDKVARIABL'] = 1 # All techs can be invested in

# Quick hack for testing
GDATA.loc[:, 'GDTYPE'] = 'GEXT'
GDATA.loc[:, 'GDFUEL'] = 'NATGAS'
GDATA.loc[:, 'GDTECHGROUP'] = 'COMBINEDCYCLE'





#%% ------------------------------------- ###
###    3. Create Techs (Area Specific)    ###
### ------------------------------------- ###



### 3.X Save GDATA
with open('./Output/GDATA.inc', 'w') as f:
    f.write("TABLE GDATA(GGG,GDATASET)  'Technologies characteristics'\n")
    f.write("* Most technologies come from the technology catalogue of the Danish Energy Agency:\n")
    f.write("* - District Heating and Power Generation, June 2022 https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-generation-electricity-and\n")
    f.write("* - Renewable Fuels, March 2023 https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-renewable-fuels\n")
    f.write("* - Energy Storage, January 2020 https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-energy-storage\n")
    dfAsString = GDATA.to_string(header=True, index=True)
    f.write(dfAsString)
    # f.write('\n;')

### 3.X Save GGG
with open('./Output/GGG.inc', 'w') as f:
    f.write("SET GGG  'All generation technologies'\n")
    f.write('/\n')
    f.write('\n'.join(GDATA.index))
    # f.write('\n/;')  

#%% ------------------------------------- ###
###            4. Create AGKN             ###
### ------------------------------------- ###

### 4.1 Hack, all techs can be invested everywhere
with open('./Output/AGKN.inc', 'w') as f:
    # f.write("SET GGG  'All generation technologies'\n")
    for A in areas[the_index]:
        for G in GDATA.index:
            f.write("AGKN('%s_A', '%s') = YES;\n"%(A, G))
    # f.write('/\n')
    # f.write('\n/;')  

