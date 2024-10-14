"""
TITLE

Description

Created on 14.10.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###             0. CLI              ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
from shapely import Point
import numpy as np
import geopandas as gpd
import xarray as xr
import click
from geofiles import prepared_geofiles
from Submodules.utils import store_balmorel_input, join_to_gpd
from pybalmorel import IncFile

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
@click.pass_context
@click.argument('cutout', type=str)
def cmd1(ctx, cutout: str):
        "A command in the CLI"
        
        temperature = xr.load_dataset(cutout).temperature
        the_index, geofile, c = prepared_geofiles('DKmunicipalities_names')

        agg_temperatures = aggregate_temperatures(temperature, geofile)
        print(agg_temperatures)

#%% ------------------------------- ###
###            2. Utils             ###
### ------------------------------- ###

def aggregate_temperatures(temperature: xr.DataArray, 
                           geofile: gpd.GeoDataFrame,
                           aggfunc: str = 'mean'):
        
        agg_temperatures = xr.DataArray(dims=['municipality', 'time'],
                                        coords={'municipality' : geofile.index.values,
                                              'time' : temperature.coords['time'].data},
                                      name='temperature')
        
        for municipality in geofile.index:
                # Get the bounds of the municipality
                x0, y0, x1, y1 = geofile.loc[municipality, 'geometry'].bounds
                
                # Get the coordinates inside the municipality
                snapshot = (
                        temperature.loc[:, y0:y1+0.25, x0:x1+0.25] # Order of coordinates: time, latitude, longitude. Add buffer equal to grid resolution to ensure the snapshot is not empty
                        .isel(time=0)                    # A snapshot in time, we just need coordinates at this point
                        .to_dataframe() 
                        .reset_index()
                )
                coords = gpd.points_from_xy(snapshot['x'], snapshot['y'])
                idx = coords.within(geofile.loc[municipality, 'geometry'])
                
                if len(coords[idx]) == 0:
                        centroid_distances = (
                                geofile
                                # .to_crs('EPSG:4093')
                                .loc[municipality, 'geometry']
                                .centroid
                                .distance(coords)
                        )
                        coords = coords[centroid_distances == centroid_distances.min()]
                        print('No points within %s!'%municipality, 'The closest point was %0.2f m away..'%(centroid_distances.min()))
                else:
                        coords = coords[idx]
                
                # The mean temperature of coordinates in the municipality
                aggregated_temperature = getattr(temperature.loc[:, coords.y, coords.x], aggfunc)(dim=['x', 'y'])

                # Store it
                aggregated_temperature = aggregated_temperature.assign_coords({'municipality' : municipality})
                agg_temperatures.loc[municipality, :] = aggregated_temperature

                # Report it
                meanstd = temperature.loc[:, coords.y, coords.x].std(dim=['x', 'y']).mean()
                print('Mean standard deviation of temperature data inside %s:'%municipality, float(meanstd))
                
        return agg_temperatures

@click.pass_context
def plot_style(ctx, fig: plt.figure, ax: plt.axes, name: str):
        
        ax.set_facecolor(ctx.obj['fc'])
        ax.legend(loc='center', bbox_to_anchor=(.5, 1.15), ncol=3)
        
        fig.savefig(name + ctx.obj['plot_ext'], bbox_inches='tight', transparent=True)
        
        return fig, ax

def load_profiles_from_balmorel(ctx):
    # Load DH_VAR_T
    df = store_balmorel_input('DH_VAR_T', ['A', 'DHUSER', 'S', 'T', 'Value'], 
                        ctx.obj['model_path'], ctx.obj['scenario'], ctx.obj['load_again'], 
                        lambda x: x.loc[x.A.str.contains('DK_')].query("DHUSER == 'RESH'"))
    
    ## Join municipal codes ('A') to names ('NAME_2')
    df = join_to_gpd(df, 'A', ctx.obj['mun'], 'NAME_2', 
                    ['A_old', 'DHUSER', 'S', 'T', 'Value', 'A'], '_A')
    
    return df

@click.pass_context
def heat_profiles_func(ctx, df):
    
        
    ### Save DH_VAR_T.inc
    incfile = IncFile(name='DH_VAR_T', path='Output',
                    prefix='\n'.join([
                            "PARAMETER DH_VAR_T(AAA,DHUSER,SSS,TTT) 'Variation in heat demand';",
                            "TABLE DH_VAR_T1(SSS,TTT,AAA,DHUSER)",
                            ""
                    ]),
                    body=df,
                    suffix='\n'.join([
                            "",
                            ";",
                            "DH_VAR_T(AAA,'RESH',SSS,TTT) = DH_VAR_T1(SSS,TTT,AAA,'RESH');",
                            "DH_VAR_T1(SSS,TTT,AAA,DHUSER) = 0;",
                            "DH_VAR_T('Herlev_A','RESH',SSS,TTT) = DH_VAR_T('Ballerup_A','RESH',SSS,TTT);"
                    ]))
    incfile.body_prepare(['S', 'T'],
                        ['A', 'DHUSER'])
    incfile.save()
    
    ### Save INDIVUSERS_DH_VAR_T
    df['A'] = df.A.str.replace('_A', '_IDVU-SPACEHEAT')
    df['DHUSER'] = 'RESIDENTIAL'
    incfile = IncFile(name='INDIVUSERS_DH_VAR_T', path='Output',
                    prefix='\n'.join([
                    "TABLE DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER)",
                    ""
                    ]),
                    body=df,
                    suffix='\n'.join([
                        "",
                        ";",
                        "DH_VAR_T(AAA,DHUSER,SSS,TTT)$(SUM((S,T), DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER))) = DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER);",
                        "DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER) = 0;",
                        "DH_VAR_T('Herlev_A','RESIDENTIAL',SSS,TTT) = DH_VAR_T('Ballerup_A','RESIDENTIAL',SSS,TTT);"
                    ]))
    incfile.body_prepare(['S', 'T'],
                        ['A', 'DHUSER'])
    incfile.save()

#%% ------------------------------- ###
###             3. Main             ###
### ------------------------------- ###
if __name__ == '__main__':
        CLI()
