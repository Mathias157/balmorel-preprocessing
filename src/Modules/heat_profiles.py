"""
Generate Heat Demand Timeseries

Will use temperature coordinates to 1) find average temperatures within polygons, 
2) use heating degree days assumption from Eurostat to generate heat demand profiles based on these timeseries
3) aggregate this profile with a flat profile for hot water consumption, being 25% of the total profile

Created on 14.10.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
"""
#%% ------------------------------- ###
###             0. CLI              ###
### ------------------------------- ###

import matplotlib.pyplot as plt
import pandas as pd
from pybalmorel import IncFile
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
@click.option('--weather-year', type=int, required=False, default=2012, help="The weather year")
@click.option('--plot', is_flag=True, required=False, help="Plot the average temperatures on a map?")
def generate(ctx, cutout: str, weather_year: int, plot: bool):
        "A command in the CLI"
        
        # Get files
        temperature = xr.load_dataset(cutout).temperature
        the_index, geofile, c = prepared_geofiles('DKmunicipalities_names')

        # Aggregate temperature for coordinates inside municipality polygons
        agg_temperatures = aggregate_temperatures(temperature, geofile)
        
        plot_data(agg_temperatures, 'temperature')
        
        # Make heat demand profile
        ## Convert temperatures to C
        agg_temperatures['heat_demand'] = agg_temperatures.temperature.copy() - 273.15        
        ## Apply heat degree hour function
        agg_temperatures['heat_demand'] = xr.where(agg_temperatures.heat_demand <= 15, 18 - agg_temperatures.heat_demand, 0)
        ## Add constant profile for hot water consumption
        agg_temperatures['heat_demand'] = 0.75*agg_temperatures.heat_demand/agg_temperatures.heat_demand.sum('time') + 0.25 / len(agg_temperatures.time.data)
        
        plot_data(agg_temperatures, 'heat_demand')
        
        
        # Make Balmorel input
        df = format_data(agg_temperatures, weather_year)
        
        ## Create IncFiles
        f = IncFile(name='DH_VAR_T', path='Output',
                    prefix="\n".join([
                        "PARAMETER DH_VAR_T(AAA,DHUSER,SSS,TTT) 'Variation in heat demand';",
                        "TABLE DH_VAR_T1(SSS,TTT,AAA,DHUSER)",
                        "",
                    ]),
                    suffix="\n".join([
                        "",
                        ";",
                        "DH_VAR_T(AAA,'RESH',SSS,TTT) = DH_VAR_T1(SSS,TTT,AAA,'RESH');",
                        "DH_VAR_T1(SSS,TTT,AAA,DHUSER) = 0;",
                    ]))
        ### Make _A suffix
        dfA = df.copy()
        dfA.columns = pd.Series(dfA.columns) + '_A' + ' . RESH'
        f.body = dfA
        f.save()
        
        dfA.columns = pd.Series(dfA.columns).str.replace('_A', '_IDVU-SPACEHEAT').str.replace('RESH', 'RESIDENTIAL')
        f = IncFile(
                name = 'INDIVUSERS_DH_VAR_T',
                path = 'Output',
                prefix='\n'.join([
                    "TABLE DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER)",
                    ""
                ]),
                body= dfA,
                suffix='\n'.join([
                                "",
                                ";",
                                "DH_VAR_T(AAA,DHUSER,SSS,TTT)$(SUM((S,T), DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER))) = DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER);",
                                "DH_VAR_T_INDIVHEATING(SSS,TTT,AAA,DHUSER) = 0;"
                ])
        )
        f.save()        
                

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
                        temperature.loc[:, y0-0.25:y1+0.25, x0-0.25:x1+0.25] # Order of coordinates: time, latitude, longitude. Add buffer equal to grid resolution to ensure the snapshot is not empty
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
                
        # Add polygons for plotting
        geo = geofile['geometry']
        geo.index.name = 'municipality'
        
        agg_temperatures = xr.Dataset({'temperature' : agg_temperatures, 'geometry' : geo})
        agg_temperatures.geometry.attrs['crs'] = 'EPSG:4326'
                
        return agg_temperatures


def format_data(agg_temperatures: xr.Dataset, weather_year: int) -> pd.DataFrame:
        """Format timeseries to format expected by Balmorel 

        Args:
            agg_temperatures (xr.Dataset): The dataset with heat demands per municipality

        Returns:
            pd.DataFrame: The formatted dataframe, ready for the IncFile class
        """
        df = (
                agg_temperatures.heat_demand
                .to_dataframe()
                .reset_index()
                .pivot_table(index='time', columns=['municipality'], values='heat_demand', aggfunc='sum')
        )

        iso = pd.Series(df.index).dt.isocalendar()

        ## Sort away week 52 from last year 
        idx1 = iso.query('index < 672 and week == 52 and year == @weather_year-1').index
        ## Sort away week 1 from next year 
        idx2 = iso.query('index > 8088 and week == 1 and year == @weather_year+1').index 

        ## Check if there are exactly 8736 timeslices
        iso = (
                iso
                .drop(index=idx1)
                .drop(index=idx2)
        )
        
        assert len(iso) == 8736, 'Timeseries does not contain 52*168 slices!'

        df = df.iloc[iso.index]
        
        ## Make S and T index
        S = ['S0%d'%i for i in range(1, 10)] + ['S%d'%i for i in range(10, 53)]
        T = ['T00%d'%i for i in range(1, 10)] + ['T0%d'%i for i in range(10, 100)] + ['T%d'%i for i in range(100, 169)]
        index = pd.MultiIndex.from_product((S, T))  
        index = index.get_level_values(0) + ' . ' + index.get_level_values(1)      
        
        df.index = index
        df.index.name = ''
        df.columns.name = ''
        
        return df

@click.pass_context
def plot_data(ctx, 
                aggregated_temperatures: xr.Dataset,
                data: str):
        fig, ax = plt.subplots()
        
        geo = gpd.GeoDataFrame(aggregated_temperatures.geometry.to_dataframe(),
                               geometry='geometry', 
                               crs=aggregated_temperatures.geometry.crs)
        geo[data] = aggregated_temperatures[data].mean('time').to_dataframe()
        
        geo.plot(column=data, ax=ax)
        fig, ax = plot_style(fig, ax, 'Output/Figures/%s'%data, False)

@click.pass_context
def plot_style(ctx, fig: plt.figure, ax: plt.axes, name: str, legend: bool):
        
        ax.set_facecolor(ctx.obj['fc'])
        
        if legend:
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
