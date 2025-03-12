"""
Full-Load Hours of VRE

A better plotting of VRE full-load hours

Created on 12.03.2025
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###             0. CLI              ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import geopandas as gpd
import xarray as xr
from Submodules.utils import cmap
from offshore_wind import load_profiles
import click

@click.command()
@click.argument('weather-year', type=int, required=False, default=2023)
@click.option('--dark-style', is_flag=True, required=False, help='Dark plot style')
@click.option('--plot-ext', type=str, default='.pdf', required=False, help='The extension of the plot, defaults to ".pdf"')
@click.pass_context
def CLI(ctx, weather_year: int, dark_style: bool, plot_ext: str):
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
    
    # Load profiles
    offshore_profiles, geo, offshore_geo = load_profiles(weather_year=weather_year)
    onshore_profiles = xr.load_dataset('Output/VRE/wind_%d_DK.nc'%weather_year)
    pv_profiles = xr.load_dataset('Output/VRE/pv_%d_DK.nc'%weather_year)
    
    # Find FLH
    offshore_profiles = offshore_profiles.sum(dim='time') / (offshore_profiles.max(dim='time'))
    onshore_profiles = onshore_profiles.sum(dim='time') / (onshore_profiles.max(dim='time'))
    pv_profiles = pv_profiles.sum(dim='time') / (pv_profiles.max(dim='time'))

    # Fix similarity of index and column name in onshore geofile
    geo.index.name = 'ind'
    
    # Combine with geofiles
    offshore_profiles = gpd.GeoDataFrame(offshore_profiles.to_dataframe().merge(offshore_geo, on='Name'))
    onshore_profiles = gpd.GeoDataFrame(onshore_profiles.to_dataframe().merge(geo, on='NAME_2'))
    pv_profiles = gpd.GeoDataFrame(pv_profiles.to_dataframe().merge(geo, on='NAME_2'))

    fig, ax = plt.subplots(dpi=400)
    offshore_profiles.plot(ax=ax, 
                            cmap=cmap,
                            vmin=1e3,
                            vmax=5e3,
                            column='specific generation',
                            hatch='///////',
                            legend=True)
    onshore_profiles.plot(ax=ax, 
                            cmap=cmap,
                            vmin=1e3,
                            vmax=5e3,
                            column='specific generation',
                            legend=False)
    ax.axes.set_axis_off()
    fig.savefig('Output/Figures/wind_flh.png', transparent=True, bbox_inches='tight')
    
    
    fig, ax = plt.subplots(dpi=400)
    pv_profiles.plot(ax=ax, 
                            cmap=cmap,
                            vmin=1e3,
                            vmax=2e3,
                            column='specific generation',
                            legend=True)
    ax.axes.set_axis_off()
    fig.savefig('Output/Figures/pv_flh.png', transparent=True, bbox_inches='tight')
        
        
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
