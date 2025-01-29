"""
This requires an installation of graphviz on top of the python package
https://graphviz.org/download/
"""

import click
from graphviz import Source

@click.command()
@click.option('--workflow', type=str, required=True, help="Which workflow to plot")
@click.option('--view', type=bool, required=False, help="View the plotted DAG?")
def main(workflow: str, view: bool = False):
    # Do snakemake --dag > analysis/dot_source.txt to within the dot_source below
    with open('Analysis/%s_dot_source.txt'%workflow, 'r') as f:
        dot_source = f.read()

    # Create a Source object from the DOT source
    graph = Source(dot_source)

    # Render the diagram as a PNG file
    graph.render('Analysis/%s_dag'%workflow, format='pdf', cleanup=False)

    if view:
        # Optionally view the diagram (depends on your environment)
        graph.view()


if __name__ == '__main__':
    main()