@REM Run workflow with additional arguments
snakemake -s preprocessing %*

@REM Make DAG plot
snakemake -s preprocessing --dag > analysis/preprocessing_dot_source.txt
python analysis/plot_dag.py --workflow=preprocessing --view=false