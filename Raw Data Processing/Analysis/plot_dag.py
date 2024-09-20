"""
This requires an installation of graphviz
https://graphviz.org/download/
"""

from graphviz import Source

# Define the DOT source code as a string, get it with snakemake --dag
dot_source = '''
digraph snakemake_dag {
    graph[bgcolor=white, margin=0];
    node[shape=box, style=rounded, fontname=sans, fontsize=10, penwidth=2];
    edge[penwidth=2, color=grey];
        0[label = "all", color = "0.00 0.6 0.85", style="rounded"];
        1[label = "electricity_demands", color = "0.11 0.6 0.85", style="rounded"];
        2[label = "create_conversion_dictionaries", color = "0.44 0.6 0.85", style="rounded,dashed"];
        3[label = "format_energinet_electricity_data_to_xarray", color = "0.33 0.6 0.85", style="rounded,dashed"];
        4[label = "get_grid_from_Balmorel", color = "0.22 0.6 0.85", style="rounded,dashed"];
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
