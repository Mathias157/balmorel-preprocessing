"""
Created on 14.09.2023

@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)

This script aggregates GKFX from Balmorel to less technologies
Most technologies come from the technology catalogue of the Danish Energy Agency:
    - District Heating and Power Generation, June 2022 https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-generation-electricity-and
    - Renewable Fuels, March 2023 https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-renewable-fuels
    - Energy Storage, January 2020 https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-energy-storage
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
        
style = 'report'

if style == 'report':
    plt.style.use('default')
    fc = 'white'
elif style == 'ppt':
    plt.style.use('dark_background')
    fc = 'none'

#%% ------------------------------- ###
###          1. Load Data           ###
### ------------------------------- ###

### 1.1 Balmorel Data
GKFX = pd.read_csv('Data/Technology Data/GKFX.csv', sep=';')
GDATA = pd.read_csv('Data/Technology Data/GDATA.csv', sep=';')
GDATA = GDATA.pivot_table(index=['Name'], columns=['Var'], values='Value', aggfunc=sum)
G = pd.Series(GKFX.G.unique())

### 1.2 DEA Catalogue
ELDH = pd.read_excel('./Data/Technology Data/technology_data_for_el_and_dh.xlsx', sheet_name='alldata_flat')

#%% ------------------------------- ###
###            2. Analyse           ###
### ------------------------------- ###
GDATA.GDOMFCOST0 = GDATA.GDOMFCOST0.astype(float)

### 2.1 How different are costs? (Note: Might only be due to yearly differences)
for type in GDATA.GDTYPE.unique():
    # Find all names according to this type
    idx = GDATA.GDTYPE == type 
    print('\n\n------------\nType: %s\n------------'%type)
    for fuel in GDATA.GDFUEL[idx].unique():
        idx2 = idx & (GDATA.GDFUEL[idx] == fuel)
        
        print('\nFuel: ', fuel)
        
        print('Mean: ', round(GDATA.GDOMFCOST0[idx2].mean(), 2))
        
        if np.isnan(GDATA.GDOMFCOST0[idx2].std()) & len(GDATA.loc[idx & idx2, 'GDOMFCOST0']):
            print('Sigm: Only one tech')
        else:
            print('Sigm: ', round(GDATA.GDOMFCOST0[idx2].std(), 2))
        
### 2.2 How many investment options?
print('\n\n------------\nInvestment options: ', len(GDATA[~GDATA.GDKVARIABL.isna()]), '\n------------')

### 2.3 Conclusion:
"""
# Actually, it was found that GKFX is BY FAR the largest contributor to model size!
# Model size did not reduce much by cleaning up investment options,
# but when GKFX was deleted, model size reduced from 
# 34,786 rows  34,181 columns  98,075 non-zeroes 
# to 
# 4,043 rows, 3,684 columns and 12,190 non-zeroes!
# NB: A small model with only DK and DE, only 2050 with a few timeslices in one season
"""

#%% ------------------------------- ###
###        3. Aggregate GKFX        ###
### ------------------------------- ###

### 3.1 Plot showing GHOB, GETOH and GBR being the largest contributors to model size
plot_analysis = False # Make the plot?
if plot_analysis:
    print('Amount of techs in GKFX: ', len(G))
    GKFX['C'] = GKFX.A.str[:2]
    GKFX_C = GKFX.groupby(by=['Y', 'C']).aggregate({'Val (MW)' : np.count_nonzero}) # Group by country
    GKFX_C.columns = ['Nr. of Techs']
    
    for Y in [2012, 2016, 2020, 2030, 2040, 2041, 2050]:
        fig, ax = plt.subplots(figsize=(10,1.5))
               
        data = GDATA.loc[GKFX[(GKFX.Y == Y)].G, 'GDTYPE'].hist(ax=ax, align='mid', bins=np.arange(16)-0.25, width=0.5) # Plot the distribution of GDTYPE in GKFX
                
        plt.xticks(axes=ax, rotation=90)
        ax.set_title(Y)
        ax.set_ylabel('Areas * Technologies')


### 3.2 Aggregation of GBPR
# In my Balmorel-Antares coupling studies, it is useful to keep the back pressure technologies
# I will therefore aggregate these
# NOTE: This does not account for the DISTRIBUTION (e.g., if largest capacity has different efficiency)
# OR the difference between areas

idx = GDATA.loc[GKFX.G, 'GDTYPE'] == 'GBPR'
GBPR = GDATA.loc[GKFX.G][idx].index.unique()
GDATANEW = pd.DataFrame(index=[], columns=GDATA.columns)
GDATANEW.columns.name = ''

for fuel in GDATA.loc[GBPR, 'GDFUEL'].unique():
    data = GDATA.loc[GBPR]
    data = data[data['GDFUEL'] == fuel]
    print('-------\n%s\n-------\n'%fuel)
    GDATANEW.loc['GNR_ST_%s_BP'%fuel, 'GDFUEL'] = fuel
    for col in GDATANEW.columns:
        try:
            nr = data[col].astype(float)
            print(col, 'mean: %0.2f'%(nr.mean()), '+- ', nr.std())
            GDATANEW.loc['GNR_ST_%s_BP'%fuel, col] = nr.mean()
        except:
            print(col, ' = a string')
GDATANEW = GDATANEW.fillna('')
    
# Save
with open('Output/ANTBALM_GDATA.inc', 'w') as f:
    f.write("TABLE GDATA(GGG,GDATASET)  'Technologies characteristics'\n")
    f.write(GDATANEW.to_string())
    f.write('\n;')

with open('Output/ANTBALM_GKFX.inc', 'w') as f:
    f.write('* Aggregate backpressure technologies to reduce model size (see script aggregate_techs.py by MBEROS)\n')
    for fuel in GDATA.loc[GBPR, 'GDFUEL'].unique():
        # Find new aggregated tech 
        idx = GDATANEW['GDFUEL'] == fuel
        aggtech = GDATANEW.index[idx][0]
        f.write("GKFX(YYY,AAA,'%s') = SUM(GGG, GKFX(YYY,AAA,GGG)$(GDATA(GGG,'GDTYPE') EQ GBPR AND GDATA(GGG,'GDFUEL') EQ %s)); \n"%(aggtech, fuel))
        f.write("GKFX(YYY,AAA,GGG)$(GDATA(GGG,'GDTYPE') EQ GBPR AND GDATA(GGG,'GDFUEL') EQ %s) = 0;\n"%(fuel))

with open('Output/ANTBALM_G.inc', 'w') as f:
    f.write("SET G(GGG) 'Technologies added from Balmorel-Antares Coupling Addon'\n")
    f.write('/\n')
    for tech in GDATANEW.index:
        f.write(tech)
        f.write('\n')
    f.write('/;')
    
with open('Output/ANTBALM_GGG.inc', 'w') as f:
    f.write("SET GGG 'Technologies added from Balmorel-Antares Coupling Addon'\n")
    f.write('/\n')
    for tech in GDATANEW.index:
        f.write(tech)
        f.write('\n')
    f.write('/;')
