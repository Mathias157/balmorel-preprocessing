-----------------------------
CREATING BALMOREL INPUT FILES
-----------------------------


Author: Mathias Berg Rosendal, PhD DTU Management 
Last updates: 
	- create_GKFX_DK in 2022
	- create_REdata in 2022
	- create_SetFiles in 2022
	- create_Grids in 2022


This folder contain 'create_XXX.py' scripts for creating Balmorel data inputs.
It utilise functions in the functions.py, which may need to be modified if new shapefiles are wanted, or if another type of pre-processing is required.

A further description of how each script works is found within each python file


REQUIREMENTS:
The python scripts are only tested to work with the environment attached in this upper folder: 'environment.yaml'
Please use the scripts within this environment.

How to install using conda:
	conda env create --name environment_name -f environment.yml
