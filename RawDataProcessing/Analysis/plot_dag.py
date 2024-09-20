"""
This requires an installation of graphviz on top of the python package
https://graphviz.org/download/
"""

from graphviz import Source

# Copy paste the output of snakemake --dag to within the dot_source below
dot_source = '''
digraph snakemake_dag {
    graph[bgcolor=white, margin=0];
    node[shape=box, style=rounded, fontname=sans,                 fontsize=10, penwidth=2];
    edge[penwidth=2, color=grey];
        0[label = "all", color = "0.56 0.6 0.85", style="rounded"];
        1[label = "exo_electricity_demand", color = "0.44 0.6 0.85", style="rounded"];
        2[label = "create_conversion_dictionaries", color = "0.11 0.6 0.85", style="rounded,dashed"];
        3[label = "format_energinet_electricity_data_to_xarray", color = "0.33 0.6 0.85", style="rounded"];
        4[label = "get_grid_from_Balmorel", color = "0.00 0.6 0.85", style="rounded"];
        1 -> 0
        4 -> 0
        2 -> 1
        3 -> 1
}
'''

# Create a Source object from the DOT source
graph = Source(dot_source)

# Render the diagram as a PNG file
graph.render('Analysis/snakemake_dag', format='svg', cleanup=False)

# Optionally view the diagram (depends on your environment)
graph.view()
