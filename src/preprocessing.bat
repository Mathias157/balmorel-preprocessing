@REM Run workflow
snakemake -s .workflow/preprocessing

@REM Make DAG plot
snakemake -s .workflow/preprocessing --dag > analysis/preprocessing_dot_source.txt
python analysis/plot_dag.py --workflow=preprocessing --view=false