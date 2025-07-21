import pandas as pd
from Bio import Phylo
from io import StringIO
import plotly.graph_objects as go
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.spatial.distance import pdist

def create_phylogenetic_tree_from_newick(newick_string):
    """
    Creates an interactive Plotly phylogenetic tree from a Newick format string.
    """
    if not newick_string:
        return None
    try:
        handle = StringIO(newick_string)
        tree = Phylo.read(handle, "newick")
        
        # This is a complex function to convert a Bio.Phylo tree to a Plotly figure
        def get_x_coordinates(tree):
            xcoords = tree.depths()
            if not max(xcoords.values()):
                xcoords = tree.counts()
            return xcoords

        def get_y_coordinates(tree, dist=1.3):
            maxheight = tree.count_terminals()
            ycoords = dict((x, i * dist) for i, x in enumerate(tree.get_terminals()))
            def calc_row(elem):
                if not elem.is_terminal():
                    ycoords[elem] = (ycoords[elem.clades[0]] + ycoords[elem.clades[1]]) / 2
            tree.root.visit(calc_row)
            return ycoords, maxheight

        xcoords = get_x_coordinates(tree)
        ycoords, maxheight = get_y_coordinates(tree)

        fig = go.Figure()
        
        for clade in tree.find_clades(order='preorder'):
            for child in clade:
                fig.add_trace(go.Scatter(
                    x=[xcoords[clade], xcoords[child]],
                    y=[ycoords[clade], ycoords[child]],
                    mode='lines',
                    line=dict(color='rgb(200,200,200)', width=1),
                    hoverinfo='none'
                ))
            if clade.is_terminal():
                fig.add_trace(go.Scatter(
                    x=[xcoords[clade]],
                    y=[ycoords[clade]],
                    mode='markers+text',
                    marker=dict(size=6, color='darkblue'),
                    text=clade.name,
                    textposition="middle right",
                    hovertext=f"Sample: {clade.name}",
                    name=clade.name
                ))

        fig.update_layout(
            title="Phylogenetic Tree",
            showlegend=False,
            xaxis=dict(title="Genetic Distance", showgrid=False, zeroline=False),
            yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
            height=200 + maxheight * 20,
            margin=dict(l=40, r=40, b=40, t=40)
        )
        return fig

    except Exception as e:
        print(f"Error creating phylogenetic tree: {e}")
        return None