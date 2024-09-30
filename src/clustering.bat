@REM Run workflow
snakemake -s clustering

@REM Make DAG plot
snakemake -s clustering --dag > analysis/clustering_dot_source.txt
python analysis/plot_dag.py --workflow=clustering --view=false