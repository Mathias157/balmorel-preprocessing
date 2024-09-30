@REM Run workflow
snakemake -s .workflow/clustering

@REM Make DAG plot
snakemake -s .workflow/clustering --dag > analysis/clustering_dot_source.txt
python analysis/plot_dag.py --workflow=clustering --view=false