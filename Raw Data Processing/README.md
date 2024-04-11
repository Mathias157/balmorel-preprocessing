# Creating .inc Files for Balmorel

Last updates: 

- main in 2024
- create_GKFX_DK in 2022
- create_SetFiles in 2022
- create_Grids in 2022
- create_TechData in 2022
- create_Demands in 2022

Run all python scripts in this folder to process data for a Danish Balmorel case study at various spatial resolution (main.py, create_XXXX...)

main.py is a new and more systematic way of processing data, using classes and function instead of the long, hard-to-read create_XXXX python files. It is the plan to migrate everything into this structure in the future, but main.py currently only process data for industry, district heating and hydrogen.

A further description of how each script works is found within each python file

NB: No data is provided in this repo. Data link upcoming