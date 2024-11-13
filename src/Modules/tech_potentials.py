"""
TITLE

Description

Created on 21.10.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###             0. CLI              ###
### ------------------------------- ###

import matplotlib.pyplot as plt
from pybalmorel import IncFile
import pandas as pd
import click
from geofiles import prepared_geofiles

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
@click.argument('frac', type=float, required=True)
def ptes(frac: float):
    """
    Calculate technology potential for Pit Thermal Energy Storage
    
    Args:
        frac (float): Fraction of land that is available for PTES
    """
    
    # Techno-economic data
    typical_volumes = [50e3, 500e3] # m3 Typical volume sizes for PTES, according to DEA https://ens.dk/sites/ens.dk/files/Analyser/technology_data_catalogue_for_energy_storage.pdf
    typical_capacities = [5e3, 40e3] # MWh Typical energy storage capacities 
    land_use = ((3*2 + 106)**2) / (75000*0.1) # m2 / MWh  Based on course exercise from energy storage and conversion
    
    # Get municipalities
    ind, geo, c = prepared_geofiles('DKmunicipalities_names')
    geo = geo.to_crs(6933) # To a projected crs
    
    # Areas in m2
    areas = pd.DataFrame({'PIT . PTES' : geo.area})
    
    # Potential in MWh
    potential = areas / land_use * frac
    
    # Print or return the potential
    print(potential)
    
    create_subtechgroupkpot(potential, land_use)
    
#%% ------------------------------- ###
###            2. Utils             ###
### ------------------------------- ###

@click.pass_context
def plot_style(ctx, fig: plt.figure, ax: plt.axes, name: str, legend: bool = True):
    
    ax.set_facecolor(ctx.obj['fc'])
    
    if legend:
        ax.legend(loc='center', bbox_to_anchor=(.5, 1.15), ncol=3)
    
    fig.savefig(name + ctx.obj['plot_ext'], bbox_inches='tight', transparent=True)
    
    return fig, ax

V_truncated_pyramid = lambda a, b, h: h/3*(a**2 + b**2 + a*b) 

def create_subtechgroupkpot(df: pd.DataFrame, PTES_land_use: float):
    """Create subtechgroupkpot dataframe based on df with CCCRRRAAA in index and technology groups in the columns

    Args:
        df (pd.DataFrame): Dataframe containing MW/MWh potentials for capacity expansion of technologies (columns) per CCCRRRAAA (index) 
    """
    
    f = IncFile(name='SUBTECHGROUPKPOT2', path='Output',
                prefix="TABLE SUBTECHGROUPKPOT(CCCRRRAAA, TECH_GROUP, SUBTECH_GROUP)  'Subtechnology group capacity restriction by geography (MWh)'\n* A %0.2f m2/MWh for PTES was assumed with 1 pct of municipal regions available for capacity expansion\n"%(PTES_land_use),
                body=df,
                suffix='\n;')
    f.body.index.name = ''
    f.save()

#%% ------------------------------- ###
###             3. Main             ###
### ------------------------------- ###
if __name__ == '__main__':
    CLI()
