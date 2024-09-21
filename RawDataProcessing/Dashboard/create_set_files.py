"""
TITLE

Description

Created on 21.09.2024
@author: Mathias Berg Rosendal, PhD Student at DTU Management (Energy Economics & Modelling)
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
###        1. 
### ------------------------------- ###

f = (
    ### COPY PASTE THE STRING BELOW HERE ###
  {
  "countries": {
    "Country1": [
      "Region1",
      "Region2"
    ],
    "Country2": [
      "Region3"
    ]
  },
  "regions": {
    "Region1": [
      "Area1",
      "Area2"
    ],
    "Region2": [],
    "Region3": [
      "Area3"
    ]
  },
  "areas": {
    "Area1": [],
    "Area2": [],
    "Area3": []
  }
}
    
    ### COPY PASTE THE STRING ABOVE HERE ###
)

def make_dataframe_with_unequal_dimensions(input: dict):
    return pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in input.items() ]))

# Format
countries = make_dataframe_with_unequal_dimensions(f['countries'])
regions = make_dataframe_with_unequal_dimensions(f['regions'])
areas = make_dataframe_with_unequal_dimensions(f['areas'])


