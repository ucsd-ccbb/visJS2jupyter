'''
--------------------------------------------------------

Authors:
    - Brin Rosenthal (sbrosenthal@ucsd.edu)
    - Julia Len (jlen@ucsd.edu)

--------------------------------------------------------
'''

# import some packages
import numpy as np
import networkx as nx
import pandas as pd
import matplotlib as mpl
import math
import visJS_module as visJS_module

def graph_union(G1, G2, node_cmap=mpl.cm.autumn, edge_cmap=mpl.cm.coolwarm,
                node_name_1="graph 1", node_name_2="graph 2",
                physics_enabled=None, **kwargs):
    '''
    Takes two networkX graphs and displays their union, where intersecting nodes
    are triangles. Additional kwargs are passed to visjs_network.

    Inputs:
        - G1: a networkX graph
        - G2: a networkX graph
        - node_cmap: matplotlib colormap for nodes, optional, default: matplotlib.cm.autumn
        - edge_cmap: matplotlib colormap for edges, optional, default: matplotlib.cm.coolwarm
        - node_name_1: string to name first graph's nodes, optional, default: "graph 1"
        - node_name_2: string to name second graph's nodes, optional, default: "graph 2"
        - physics_enabled: boolean, optional, default: True for graphs of 100 nodes, False otherwise
    Returns:
        - VisJS html network plot (iframe) of the graph union.
    '''

    G_union = create_graph_union(G1, G2, node_name_1, node_name_2)

    # create nodes dict and edges dict for input to visjs
    nodes = G_union.nodes()
    numnodes = len(nodes)
    edges = G_union.edges()
    numedges = len(edges)

    pos = nx.spring_layout(G_union, weight="edge_weight")

    # set node_size to degree
    degree = G_union.degree()
    node_size = [int(float(n)/np.max(degree.values())*25+1) for n in degree.values()]
    node_to_nodeSize = dict(zip(degree.keys(),node_size))

    # add nodes to highlight (none for now)
    nodes_HL = pd.Series(0,index=G_union.nodes())
    nodes_HL = dict(nodes_HL)

    nodes_shape=[]
    for node in G_union.nodes(data=True):
        if node[1]['node_overlap']==0:
            nodes_shape.append('dot')
        elif node[1]['node_overlap']==2:
            nodes_shape.append('square')
        elif node[1]['node_overlap']==1:
            nodes_shape.append('triangle')
    node_to_nodeShape=dict(zip(G_union.nodes(),nodes_shape))

    # add a field for node labels
    node_blank_labels = ['']*len(G_union.nodes())

    node_labels = dict(zip(G_union.nodes(),node_blank_labels))

    node_titles = [ node[1]['node_name_membership']+'<br/>'+str(node[0]) for node in G_union.nodes(data=True)]
    node_titles = dict(zip(G_union.nodes(),node_titles))

    # set plotting parameters
    field_to_map='node_overlap'
    label_field = 'id'

    node_to_color = visJS_module.return_node_to_color(G_union,field_to_map=field_to_map,cmap=node_cmap,alpha = 1,
                                                      color_max_frac = .9,color_min_frac = .1)

    edge_to_color = visJS_module.return_edge_to_color(G_union,field_to_map = 'weight',cmap=edge_cmap,alpha=.3)

    nodes_dict = [{"id":n,"degree":G_union.degree(n),"color":node_to_color[n],
                   "node_size":30,'border_width':nodes_HL[n],
                   "node_label":node_labels[n],
                   "edge_label":'',
                   "title":node_titles[n],
                   "node_shape":node_to_nodeShape[n],
                   "x":pos[n][0]*1000,
                   "y":pos[n][1]*1000} for n in nodes
                 ]

    node_map = dict(zip(nodes,range(numnodes)))  # map to indices for source/target in edges

    edges_dict = [{"source":node_map[edges[i][0]], "target":node_map[edges[i][1]],
                   "color":edge_to_color[edges[i]],"title":'test'} for i in range(numedges)]

    # set node_size_multiplier to increase node size as graph gets smaller
    if numnodes > 500:
        node_size_multiplier = 1
    elif numnodes > 200:
        node_size_multiplier = 3
    else:
        node_size_multiplier = 5

    # if the user has not set a value for physics_enabled, then set it to default
    # value of true if the graph is smaller than 100 nodes, and false otherwise
    if physics_enabled == None:
        if numnodes < 100:
            physics_enabled = True
        else:
            physics_enabled = False

    return visJS_module.visjs_network(nodes_dict,edges_dict,
                                      node_size_field='node_size',
                                      node_size_multiplier=node_size_multiplier,
                                      physics_enabled=physics_enabled,
                                      **kwargs)


def create_graph_union(G1,G2,node_name_1,node_name_2):
    '''
    Create and return a union of two graphs, with node attributes indicating overlap,
    and weight indicating edge overlap.

    Inputs:
        - G1: a networkX graph
        - G2: a networkX graph
        - node_name_1: string to name first graph's nodes
        - node_name_2: string to name second graph's nodes
    Returns:
        - A networkX graph that is the union of G1 and G2.
    '''

    union_graph = nx.Graph()
    node_union = list(np.union1d(G1.nodes(),G2.nodes()))
    node_intersect = list(np.intersect1d(G1.nodes(),G2.nodes()))
    nodes_1only = np.setdiff1d(G1.nodes(),node_intersect)
    nodes_2only = np.setdiff1d(G2.nodes(),node_intersect)

    edges_total = G1.edges()
    edges_total.extend(G2.edges())

    union_graph.add_nodes_from(node_union)

    # set a node attribute to True if the node belongs to both graphs, otherwise False
    node_overlap=[]
    node_name_membership=[]
    for node in node_union:
        if node in nodes_1only:
            node_overlap.append(0)
            node_name_membership.append(node_name_1)
        elif node in nodes_2only:
            node_overlap.append(2)
            node_name_membership.append(node_name_2)
        else:
            # both is in the middle for colormapping
            node_overlap.append(1)
            node_name_membership.append(node_name_1+' + '+node_name_2)

    nx.set_node_attributes(union_graph,'node_overlap',dict(zip(node_union,node_overlap)))
    nx.set_node_attributes(union_graph,'node_name_membership',dict(zip(node_union,node_name_membership)))

    nodes_12 = union_graph.nodes()
    intersecting_edge_val = int(math.floor(math.log10(len(nodes_12)))) * 10

    # set the edge weights: intersecting_edge_val if edge is found in both graphs, 1 otherwise
    edge_weights = {}
    for e in edges_total:
        eflip = (e[1],e[0])
        if (e in edge_weights.keys()):
            edge_weights[e]+=intersecting_edge_val
        elif (eflip in edge_weights.keys()):
            edge_weights[eflip]+=intersecting_edge_val
        else:
            edge_weights[e]=1

    v1,v2 = zip(*edge_weights.keys())
    weights = edge_weights.values()
    edges = zip(v1,v2,weights)

    union_graph.add_weighted_edges_from(edges)
    nx.set_edge_attributes(union_graph, 'edge_weight', edge_weights)

    return union_graph
