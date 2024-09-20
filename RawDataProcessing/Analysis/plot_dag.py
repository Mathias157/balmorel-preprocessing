"""
This requires an installation of graphviz on top of the python package
https://graphviz.org/download/
"""

from graphviz import Source

# Do snakemake --dag > analysis/dot_source.txt to within the dot_source below
with open('Analysis/dot_source.txt', 'r') as f:
    dot_source = f.read()

# Create a Source object from the DOT source
graph = Source(dot_source)

# Render the diagram as a PNG file
graph.render('Analysis/snakemake_dag', format='svg', cleanup=False)

# Optionally view the diagram (depends on your environment)
graph.view()
