"""
Generate high/infinite transmission capacities 

Does what the title says, based on a clustering.gpkg file as outputted by the snakemake -s clustering command.

Created on 15.01.2025
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###             0. CLI              ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import click
import geopandas as gpd

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
@click.argument('cluster-file', required=True)
@click.option('--cap', type=float, default=1e6, required=False, help="An argument")
def trans(cluster_file: str, cap: float):
    
    # The cluster file
    gf = gpd.read_file(cluster_file)
    print(gf.columns)
    
    # The output
    f = open('ClusterOutput/transmisson_relaxation.inc', 'w')
        
    for cluster in gf.cluster_name.unique():
        
        nodes = gf.query('cluster_name == @cluster')['index'].unique()
        nodes_j = list(nodes.copy())
        # print('\nNodes in %s: %s'%(cluster, ', '.join(nodes)))
        
        
        for node_i in nodes:
            for node_j in [node_j for node_j in nodes_j if node_j != node_i]:
                f.write("XKFX(YYY,'%s','%s') = %0.2f;\n"%(node_i, node_j, cap))
                f.write("XKFX(YYY,'%s','%s') = %0.2f;\n"%(node_j, node_i, cap))
            nodes_j.remove(node_i)
            
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

#%% ------------------------------- ###
###             3. Main             ###
### ------------------------------- ###
if __name__ == '__main__':
    CLI()
