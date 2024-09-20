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
        0[label = "all", color = "0.07 0.6 0.85", style="rounded"];
        1[label = "exo_electricity_demand", color = "0.20 0.6 0.85", style="rounded"];
        2[label = "create_conversion_dictionaries", color = "0.27 0.6 0.85", style="rounded,dashed"];
        3[label = "format_energinet_electricity_data", color = "0.00 0.6 0.85", style="rounded,dashed"];
        4[label = "get_grid_from_Balmorel", color = "0.33 0.6 0.85", style="rounded"];
        5[label = "format_dkstat_transport_data", color = "0.13 0.6 0.85", style="rounded,dashed"];
        6[label = "exo_heat_demand", color = "0.47 0.6 0.85", style="rounded"];
        7[label = "format_vpdk21_data", color = "0.60 0.6 0.85", style="rounded"];
        8[label = "format_dkstat_industry_data", color = "0.40 0.6 0.85", style="rounded,dashed"];
        1 -> 0
        4 -> 0
        5 -> 0
        6 -> 0
        2 -> 1
        3 -> 1
        7 -> 6
        8 -> 6
}
'''

# Create a Source object from the DOT source
graph = Source(dot_source)

# Render the diagram as a PNG file
graph.render('Analysis/snakemake_dag', format='svg', cleanup=False)

# Optionally view the diagram (depends on your environment)
graph.view()
