"""
Create Empty Sets for Aggregated Model

The clustered model will include exogenous heat and electricity demands from addons in DE, DE_VAR_T, DH, DH_VAR_T etc.
Thus, this script is needed to 1) create empty files for INDUSTRY_DH, INDIVUSERS_DH etc., 
and 2) to create the INDUSTRY_INDUSTRY_AAA and INDIVUSERS_INDIVUSERS_AAA etc. files required for categorising sets.

Created on 04.10.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###        0. Script Settings       ###
### ------------------------------- ###

import click
from typing import Tuple
from pybalmorel import IncFile
import geopandas as gpd

#%% ------------------------------- ###
###        1. 
### ------------------------------- ###

def create_empty_set_files(addons: list, empty_files: list):

    for addon in addons:
        for file in empty_files:
           f = IncFile(name=addon+'_'+file, path='ClusterOutput')
           f.save()
           
def create_category_files(addons: list, clustering: gpd.GeoDataFrame, category_files: list, **kwargs):
    
    for addon in addons:
        for file in category_files:
            file = file.replace('*', addon)
            
            if file == addon+'_AAA':
                suffixes = kwargs['suffixes'][addon]
                f = IncFile(name=addon+'_'+file, path='ClusterOutput',
                            prefix=f"SET {addon}_AAA(CCCRRRAAA) 'All areas'\n/\n",
                            suffix='\n/\n;')
                
                for suffix in suffixes: 
                    new_suffix = clustering['cluster_name'].unique() + '_' + suffix
                    f.body += '\n'.join([new for new in new_suffix]) + '\n'

                f.save()

#%% ------------------------------- ###
###            X. Main              ###
### ------------------------------- ###

@click.command()
@click.option('--clusterfile', type=str, required=True, help="The name of the clusterfile")
# @click.option('--addons', type=(str, list), required=False, help='The addons that require empty set files and categories')
def main(clusterfile: str,
         addons: Tuple[list, str] = ['INDUSTRY', 'HYDROGEN', 'INDIVUSERS'],
         empty_files: Tuple[list, str] = ['DE', 'DE_VAR_T', 'DH', 'DH_VAR_T', 
                                          'CCCRRRAAA', 'RRRAAA', 'AAA', 'AGKN',
                                          'DISLOSS_E_AG']):
    
    # Create empty sets
    create_empty_set_files(addons, empty_files)

    # Create categories
    if not('2nd-order' in clusterfile):
        print('Reading %s'%clusterfile)
        clusters = gpd.read_file(clusterfile)
        create_category_files([addon for addon in addons if addon != 'HYDROGEN'], 
                            clusters,
                            ['*_AAA'],
                            suffixes={'INDUSTRY' : ['IND-LT-NODH', 'IND-MT-NODH', 'IND-HT-NODH'],
                                        'INDIVUSERS' : ['IDVU-SPACEHEAT']})

if __name__ == '__main__':
    main()
