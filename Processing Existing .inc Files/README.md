# How to Use
The main file is 'dataprocessing.py', 

If you choose 'use_provided = True', the two provided *_ReadData files will be copy+pasted into the project_dir folder that you specify (should be where your Balmorel.gms file is, typically Balmorel/scenario/model, where scenario could be 'base')

If not, you will have to specify your custom run_file. This should be a GAMS script that loads the .inc files you need to load.
