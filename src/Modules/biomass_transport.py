"""
TITLE

Description

Created on 11.10.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###             0. CLI              ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from Submodules.municipal_template import DataContainer
from grids import get_distance_matrix
import xarray as xr
import click
from pybalmorel import IncFile
from Submodules.utils import convert_names

@click.group()
@click.option('--dark-style', is_flag=True, required=False, help='Dark plot style')
@click.option('--plot-ext', type=str, default='.pdf', required=False, help='The extension of the plot, defaults to ".pdf"')
@click.pass_context
def CLI(ctx, dark_style: bool, plot_ext: str):
    """
    Description of the CLI
    """
    
    # Set global style of plot
    if dark_style:
        plt.style.use('dark_background')
        fc = 'none'
    else:
        fc = 'white'

    # Store global options in the context object
    ctx.ensure_object(dict)
    ctx.obj['fc'] = fc
    ctx.obj['plot_ext'] = plot_ext


#%% ------------------------------- ###
###           1. Commands           ###
### ------------------------------- ###

@CLI.command()
@click.argument('transport-cost', type=float)
def transport(transport_cost: float):
    """Producing transport costs for fuels

    Args:
        transport_cost (_type_): the cost of transport in €/GJ/km
    """
    
    # Load connectivity
    f = xr.load_dataset("Data/BalmorelData/municipal_connectivity.nc")
    f, fnew = convert_names('Modules/Submodules/exo_grid_conversion_dictionaries.pkl',
                      f, 'connection')
    
    # Get Distance Matrix
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
    
    # Get cost matrix
    C = d * transport_cost / 1e3
    C.index.name=''
    C.columns.name=''
    C = C.astype('object')

    # Yes.. lazy and slow for loop to disable regions not connected
    for reg1 in C.index:
        for reg2 in C.columns:
            if fnew.connection.loc[reg1, reg2].data == 0:
                C.loc[reg1, reg2] = ''
    
    # Make IncFile
    C.index = 'STRAW . ' + pd.Series(C.index) 
    f = IncFile(name='FUELTRANSPORT_COST', path='Output',
                prefix="TABLE FUELTRANSPORT_COST(FFF, IRRRE, IRRRI) 'Cost of transporting one GJ of fuel F from region IRRRE to IRRRI'\n",
                body=C,
                suffix='\n;\nFUELTRANSPORT_COST("WOOD", IRRRE, IRRRI) = FUELTRANSPORT_COST("STRAW", IRRRE, IRRRI);\n')
    f.save()


#%% ------------------------------- ###
###            2. Utils             ###
### ------------------------------- ###

@click.pass_context
def plot_style(ctx, fig: plt.figure, ax: plt.axes, name: str):
    
    ax.set_facecolor(ctx.obj['fc'])
    ax.legend(loc='center', bbox_to_anchor=(.5, 1.15), ncol=3)
    
    fig.savefig(name + ctx.obj['plot_ext'], bbox_inches='tight', transparent=True)
    
    return fig, ax

#%% ------------------------------- ###
###             3. Main             ###
### ------------------------------- ###
if __name__ == '__main__':
    CLI()
