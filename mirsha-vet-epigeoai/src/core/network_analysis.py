import pandas as pd
import networkx as nx
from pyvis.network import Network

def build_network_graph(movement_df):
    """
    Builds a NetworkX graph from a dataframe of movements.
    Calculates centrality and sizes nodes by importance.
    """
    if movement_df.empty:
        return None

    G = nx.from_pandas_edgelist(
        movement_df,
        source='origin_name',
        target='destination_name',
        edge_attr='total_animals',
        create_using=nx.DiGraph() # Use a directed graph
    )
    
    # Calculate centrality to find important nodes (markets)
    # Degree centrality: number of connections
    try:
        centrality = nx.degree_centrality(G)
        nx.set_node_attributes(G, centrality, 'centrality')

        # Set node sizes based on centrality for visualization
        # Scale the sizes for better visual appearance
        min_size = 5
        max_size = 50
        max_centrality = max(centrality.values()) if centrality else 1
        
        node_sizes = {
            node: min_size + (data['centrality'] / max_centrality) * (max_size - min_size)
            for node, data in G.nodes(data=True)
        }
        nx.set_node_attributes(G, node_sizes, 'size')
        
    except Exception as e:
        print(f"Could not calculate centrality: {e}")

    return G

def create_interactive_network_viz(G, movement_df):
    """
    Creates an interactive Pyvis network visualization from a NetworkX graph.
    """
    if G is None:
        return None

    net = Network(height='750px', width='100%', notebook=True, cdn_resources='in_line', directed=True)
    net.from_nx(G)

    # Customize the physics for a better layout
    net.set_options("""
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      }
    }
    """)
    
    # Save the network to an HTML file
    html_path = 'network.html'
    net.write_html(html_path)
    return html_path