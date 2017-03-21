'''
--------------------------------------------------------

Authors:
    - Brin Rosenthal (sbrosenthal@ucsd.edu)
    - Julia Len (jlen@ucsd.edu)

--------------------------------------------------------
'''

import pandas as pd
from py2cytoscape import util
import json
import math
import matplotlib as mpl
import networkx as nx
import numpy as np
import visJS_module as visJS_module

def draw_graph_overlap(G1, G2,
                       edge_cmap=mpl.cm.coolwarm,
                       export_file='graph_overlap.json',
                       export_network=False,
                       highlight_nodes=None,
                       k=None,
                       node_cmap=mpl.cm.autumn,
                       node_name_1='graph 1',
                       node_name_2='graph 2',
                       node_size=10,
                       physics_enabled=None,
                       **kwargs):
    '''
    Takes two networkX graphs and displays their overlap, where intersecting
    nodes are triangles. Additional kwargs are passed to visjs_module.

    Inputs:
        - G1: a networkX graph
        - G2: a networkX graph
        - edge_cmap: matplotlib colormap for edges, default: matplotlib.cm.coolwarm
        - export_file: JSON file to export graph data, default: 'graph_overlap.json'
        - export_network: export network to Cytoscape, default: False
        - highlight_nodes: list of nodes to place borders around, default: None
        - k: float, optimal distance between nodes for nx.spring_layout(), default: None
        - node_cmap: matplotlib colormap for nodes, default: matplotlib.cm.autumn
        - node_name_1: string to name first graph's nodes, default: 'graph 1'
        - node_name_2: string to name second graph's nodes, default: 'graph 2'
        - node_size: size of nodes, default: 10
        - physics_enabled: enable physics simulation, default: True for graphs of less than 100 nodes

    Returns:
        - VisJS html network plot (iframe) of the graph overlap.
    '''

    G_overlap = create_graph_overlap(G1, G2, node_name_1, node_name_2)

    # create nodes dict and edges dict for input to visjs
    nodes = G_overlap.nodes()
    edges = G_overlap.edges()

    # set the position of each node
    if k is None:
        pos = nx.spring_layout(G_overlap)
    else:
        pos = nx.spring_layout(G_overlap,k=k)

    xpos,ypos=zip(*pos.values())
    nx.set_node_attributes(G_overlap,'xpos',dict(zip(pos.keys(),[x*1000 for x in xpos])))
    nx.set_node_attributes(G_overlap,'ypos',dict(zip(pos.keys(),[y*1000 for y in ypos])))

    # set the border width of nodes
    if 'node_border_width' not in kwargs.keys():
        kwargs['node_border_width'] = 2

    border_width = {}
    for n in nodes:
        if highlight_nodes is not None and n in highlight_nodes:
            border_width[n] = kwargs['node_border_width']
        else:
            border_width[n] = 0

    nx.set_node_attributes(G_overlap,'nodeOutline',border_width)

    # set the shape of each node
    nodes_shape=[]
    for node in G_overlap.nodes(data=True):
        if node[1]['node_overlap']==0:
            nodes_shape.append('dot')
        elif node[1]['node_overlap']==2:
            nodes_shape.append('square')
        elif node[1]['node_overlap']==1:
            nodes_shape.append('triangle')
    node_to_shape=dict(zip(G_overlap.nodes(),nodes_shape))
    nx.set_node_attributes(G_overlap,'nodeShape',node_to_shape)

    # set the node label of each node
    if highlight_nodes:
        node_labels = {}
        for node in nodes:
            if node in highlight_nodes:
                node_labels[node] = node
            else:
                node_labels[node] = ''
    else:
        node_labels = {n:n for n in nodes}

    nx.set_node_attributes(G_overlap,'nodeLabel',node_labels)

    # set the node title of each node
    node_titles = [ node[1]['node_name_membership'] + '<br/>' + str(node[0])
                    for node in G_overlap.nodes(data=True) ]
    node_titles = dict(zip(G_overlap.nodes(),node_titles))
    nx.set_node_attributes(G_overlap,'nodeTitle',node_titles)

    # set color of each node
    node_to_color = visJS_module.return_node_to_color(G_overlap,
                                                      field_to_map='node_overlap',
                                                      cmap=node_cmap,
                                                      color_max_frac=.9,
                                                      color_min_frac=.1)

    # set color of each edge
    edge_to_color = visJS_module.return_edge_to_color(G_overlap,
                                                      field_to_map='edge_weight',
                                                      cmap=edge_cmap,
                                                      alpha=.3)

    # create the nodes_dict with all relevant fields
    nodes_dict = [{'id':n,
                   'border_width':border_width[n],
                   'color':node_to_color[n],
                   'degree':G_overlap.degree(n),
                   'node_label':node_labels[n],
                   'node_shape':node_to_shape[n],
                   'node_size':node_size,
                   'title':node_titles[n],
                   'x':pos[n][0]*1000,
                   'y':pos[n][1]*1000}
                  for n in nodes]

    # map nodes to indices for source/target in edges
    node_map = dict(zip(nodes,range(len(nodes))))

    # create the edges_dict with all relevant fields
    edges_dict = [{'source':node_map[edges[i][0]],
                   'target':node_map[edges[i][1]],
                   'color':edge_to_color[edges[i]]}
                  for i in range(len(edges))]

    # set node_size_multiplier to increase node size as graph gets smaller
    if 'node_size_multiplier' not in kwargs.keys():
        if len(nodes) > 500:
            kwargs['node_size_multiplier'] = 3
        elif len(nodes) > 200:
            kwargs['node_size_multiplier'] = 5
        else:
            kwargs['node_size_multiplier'] = 7

    kwargs['physics_enabled'] = set_physics_enabled(physics_enabled, len(nodes))

    # if node hovering color not set, set default to black
    if 'node_color_hover_background' not in kwargs.keys():
        kwargs['node_color_hover_background'] = 'black'

    # node size determined by size in nodes_dict, not by id
    if 'node_size_field' not in kwargs.keys():
        kwargs['node_size_field'] = 'node_size'

    # node label determined by value in nodes_dict
    if 'node_label_field' not in kwargs.keys():
        kwargs['node_label_field'] = 'node_label'

    # export the network to JSON for Cytoscape
    if export_network:
        node_colors = map_node_to_color(G_overlap,'node_overlap')
        nx.set_node_attributes(G_overlap,'nodeColor',node_colors)
        edge_colors = map_edge_to_color(G_overlap,'edge_weight')
        nx.set_edge_attributes(G_overlap,'edgeColor',edge_colors)
        export_to_cytoscape(G_overlap,export_file)

    return visJS_module.visjs_network(nodes_dict,edges_dict,**kwargs)


def create_graph_overlap(G1,G2,node_name_1,node_name_2):
    '''
    Create and return the overlap of two graphs.

    Inputs:
        - G1: a networkX graph
        - G2: a networkX graph
        - node_name_1: string to name first graph's nodes
        - node_name_2: string to name second graph's nodes

    Returns:
        - A networkX graph that is the overlap of G1 and G2.
    '''

    overlap_graph = nx.Graph()
    node_union = list(np.union1d(G1.nodes(),G2.nodes()))
    node_intersect = list(np.intersect1d(G1.nodes(),G2.nodes()))
    nodes_1only = np.setdiff1d(G1.nodes(),node_intersect)
    nodes_2only = np.setdiff1d(G2.nodes(),node_intersect)

    edges_total = G1.edges()
    edges_total.extend(G2.edges())

    overlap_graph.add_nodes_from(node_union)

    # set node attributes to distinguish which graph the node belongs to
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
            node_overlap.append(1)
            node_name_membership.append(node_name_1+' + '+node_name_2)

    nx.set_node_attributes(overlap_graph,
                           'node_overlap',
                           dict(zip(node_union,node_overlap)))
    nx.set_node_attributes(overlap_graph,
                           'node_name_membership',
                           dict(zip(node_union,node_name_membership)))

    nodes_total = overlap_graph.nodes()
    intersecting_edge_val = int(math.floor(math.log10(len(nodes_total)))) * 10

    # set the edge weights
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

    overlap_graph.add_weighted_edges_from(edges)
    nx.set_edge_attributes(overlap_graph,'edge_weight',edge_weights)
    return overlap_graph


def draw_heat_prop(G, seed_nodes,
                   edge_cmap=mpl.cm.autumn_r,
                   export_file='heat_prop.json',
                   export_network=False,
                   highlight_nodes=None,
                   k=None,
                   largest_connected_component=False,
                   node_cmap=mpl.cm.autumn_r,
                   node_size=10,
                   num_nodes=None,
                   physics_enabled=None,
                   Wprime=None,
                   **kwargs):
    '''
    Implements and displays the network propagation for a given graph and seed
    nodes. Additional kwargs are passed to visJS_module.

    Inputs:
        - G: a networkX graph
        - seed_nodes: nodes on which to initialize the simulation
        - edge_cmap: matplotlib colormap for edges, default: matplotlib.cm.autumn_r
        - export_file: JSON file to export graph data, default: 'graph_overlap.json'
        - export_network: export network to Cytoscape, default: False
        - highlight_nodes: list of nodes to place borders around, default: None
        - k: float, optimal distance between nodes for nx.spring_layout(), default: None
        - largest_connected_component: boolean, whether or not to display largest_connected_component,
                                       default: False
        - node_cmap: matplotlib colormap for nodes, default: matplotlib.cm.autumn_r
        - node_size: size of nodes, default: 10
        - num_nodes: the number of the hottest nodes to graph, default: None (all nodes will be graphed)
        - physics_enabled: enable physics simulation, default: True for graphs of less than 100 nodes
        - Wprime: normalized adjacency matrix (from function normalized_adj_matrix())

    Returns:
        - VisJS html network plot (iframe) of the heat propagation.
    '''

    # check for invalid nodes in seed_nodes
    invalid_nodes = [node for node in seed_nodes if node not in G.nodes()]
    for node in invalid_nodes:
        print 'Node %s not in graph' % node
    if invalid_nodes:
        return

    # perform the network propagation
    if Wprime is None:
        Wprime = normalized_adj_matrix(G)
    prop_graph = network_propagation(G, Wprime, seed_nodes).to_dict()
    nx.set_node_attributes(G,'node_heat',prop_graph)

    # find top num_nodes hottest nodes and connected component if requested
    G = set_num_nodes(G,num_nodes)
    if largest_connected_component:
        G = max(nx.connected_component_subgraphs(G), key=len)
    nodes = G.nodes()
    edges = G.edges()

    # check for empty nodes and edges after getting subgraph of G
    if not nodes:
        print 'There are no nodes in the graph. Try increasing num_nodes.'
        return
    if not edges:
        print 'There are no edges in the graph. Try increasing num_nodes.'
        return

    # set the position of each node
    if k is None:
        pos = nx.spring_layout(G)
    else:
        pos = nx.spring_layout(G,k=k)

    xpos,ypos=zip(*pos.values())
    nx.set_node_attributes(G,'xpos',dict(zip(pos.keys(),[x*1000 for x in xpos])))
    nx.set_node_attributes(G,'ypos',dict(zip(pos.keys(),[y*1000 for y in ypos])))

    # set the border width of nodes
    if 'node_border_width' not in kwargs.keys():
        kwargs['node_border_width'] = 2

    border_width = {}
    for n in nodes:
        if n in seed_nodes:
            border_width[n] = kwargs['node_border_width']
        elif highlight_nodes is not None and n in highlight_nodes:
            border_width[n] = kwargs['node_border_width']
        else:
            border_width[n] = 0

    nx.set_node_attributes(G,'nodeOutline',border_width)

    # set the shape of each node
    nodes_shape=[]
    for node in G.nodes():
        if node in seed_nodes:
            nodes_shape.append('triangle')
        else:
            nodes_shape.append('dot')
    node_to_shape=dict(zip(G.nodes(),nodes_shape))
    nx.set_node_attributes(G,'nodeShape',node_to_shape)

    # add a field for node labels
    if highlight_nodes:
        node_labels = {}
        for node in nodes:
            if node in seed_nodes:
                node_labels[node] = node
            elif node in highlight_nodes:
                node_labels[node] = node
            else:
                node_labels[node] = ''
    else:
        node_labels = {n:n for n in nodes}

    nx.set_node_attributes(G,'nodeLabel',node_labels)

    # set title for each node
    node_titles = [str(node[0]) + '<br/>heat = ' + str(round(node[1]['node_heat'],5))
                   for node in G.nodes(data=True)]
    node_titles = dict(zip(G.nodes(),node_titles))
    nx.set_node_attributes(G,'nodeTitle',node_titles)

    # set color of each node
    node_to_color = visJS_module.return_node_to_color(G,
                                                      field_to_map='node_heat',
                                                      cmap=node_cmap,
                                                      color_vals_transform='log')

    # set heat value of edge based off hottest connecting node's value
    node_attr = nx.get_node_attributes(G,'node_heat')
    edge_weights = {}
    for e in edges:
        if node_attr[e[0]] > node_attr[e[1]]:
            edge_weights[e] = node_attr[e[0]]
        else:
            edge_weights[e] = node_attr[e[1]]

    nx.set_edge_attributes(G,'edge_weight',edge_weights)

    # set color of each edge
    edge_to_color = visJS_module.return_edge_to_color(G,
                                                      field_to_map='edge_weight',
                                                      cmap=edge_cmap,
                                                      color_vals_transform='log')

    # create the nodes_dict with all relevant fields
    nodes_dict = [{'id':n,
                   'border_width':border_width[n],
                   'degree':G.degree(n),
                   'color':node_to_color[n],
                   'node_label':node_labels[n],
                   'node_size':node_size,
                   'node_shape':node_to_shape[n],
                   'title':node_titles[n],
                   'x':pos[n][0]*1000,
                   'y':pos[n][1]*1000} for n in nodes]

    # map nodes to indices for source/target in edges
    node_map = dict(zip(nodes, range(len(nodes))))

    # create the edges_dict with all relevant fields
    edges_dict = [{'source':node_map[edges[i][0]],
                   'target':node_map[edges[i][1]],
                   'color':edge_to_color[edges[i]]} for i in range(len(edges))]

    # set node_size_multiplier to increase node size as graph gets smaller
    if 'node_size_multiplier' not in kwargs.keys():
        if len(nodes) > 500:
            kwargs['node_size_multiplier'] = 3
        elif len(nodes) > 200:
            kwargs['node_size_multiplier'] = 5
        else:
            kwargs['node_size_multiplier'] = 7

    kwargs['physics_enabled'] = set_physics_enabled(physics_enabled, len(nodes))

    # if node hovering color not set, set default to black
    if 'node_color_hover_background' not in kwargs.keys():
        kwargs['node_color_hover_background'] = 'black'

    # node size determined by size in nodes_dict, not by id
    if 'node_size_field' not in kwargs.keys():
        kwargs['node_size_field'] = 'node_size'

    # node label determined by value in nodes_dict
    if 'node_label_field' not in kwargs.keys():
        kwargs['node_label_field'] = 'node_label'

    # export the network to JSON for Cytoscape
    if export_network:
        node_colors = map_node_to_color(G,'node_heat')
        nx.set_node_attributes(G,'nodeColor',node_colors)
        edge_colors = map_edge_to_color(G,'edge_weight')
        nx.set_edge_attributes(G,'edgeColor',edge_colors)
        export_to_cytoscape(G,export_file)

    return visJS_module.visjs_network(nodes_dict,edges_dict,**kwargs)


def draw_colocalization(G, seed_nodes_1, seed_nodes_2,
                        edge_cmap=mpl.cm.autumn_r,
                        export_file='colocalization.json',
                        export_network=False,
                        highlight_nodes=None,
                        k=None,
                        largest_connected_component=False,
                        node_cmap=mpl.cm.autumn_r,
                        node_size=10,
                        num_nodes=None,
                        physics_enabled=None,
                        Wprime=None,
                        **kwargs):
    '''
    Implements and displays the network propagation for a given graph and two
    sets of seed nodes. Additional kwargs are passed to visJS_module.

    Inputs:
        - G: a networkX graph
        - seed_nodes_1: first set of nodes on which to initialize the simulation
        - seed_nodes_2: second set of nodes on which to initialize the simulation
        - edge_cmap: matplotlib colormap for edges, optional, default: matplotlib.cm.autumn_r
        - export_file: JSON file to export graph data, default: 'colocalization.json'
        - export_network: export network to Cytoscape, default: False
        - highlight_nodes: list of nodes to place borders around, default: None
        - k: float, optional, optimal distance between nodes for nx.spring_layout(), default: None
        - largest_connected_component: boolean, optional, whether or not to display largest_connected_component,
                                       default: False
        - node_cmap: matplotlib colormap for nodes, optional, default: matplotlib.cm.autumn_r
        - node_size: size of nodes, default: 10
        - num_nodes: the number of the hottest nodes to graph, default: None (all nodes will be graphed)
        - physics_enabled: enable physics simulation, default: True for graphs of less than 100 nodes
        - Wprime:  Normalized adjacency matrix (from normalized_adj_matrix)

    Returns:
        - VisJS html network plot (iframe) of the colocalization.
    '''

    # check for invalid nodes in seed_nodes
    invalid_nodes = [(node,'seed_nodes_1') for node in seed_nodes_1 if node not in G.nodes()]
    invalid_nodes.extend([(node,'seed_nodes_2') for node in seed_nodes_2 if node not in G.nodes()])
    for node in invalid_nodes:
        print 'Node %s in %s not in graph' % (node[0], node[1])
    if invalid_nodes:
        return

    # perform the colocalization
    if Wprime is None:
        Wprime = normalized_adj_matrix(G)
    prop_graph_1 = network_propagation(G, Wprime, seed_nodes_1).to_dict()
    prop_graph_2 = network_propagation(G, Wprime, seed_nodes_2).to_dict()
    prop_graph = {node:(prop_graph_1[node]*prop_graph_2[node]) for node in prop_graph_1}
    nx.set_node_attributes(G,'node_heat',prop_graph)

    # find top num_nodes hottest nodes and connected component if requested
    G = set_num_nodes(G,num_nodes)
    if largest_connected_component:
        G = max(nx.connected_component_subgraphs(G), key=len)
    nodes = G.nodes()
    edges = G.edges()

    # check for empty nodes and edges after getting subgraph of G
    if not nodes:
        print 'There are no nodes in the graph. Try increasing num_nodes.'
        return
    if not edges:
        print 'There are no edges in the graph. Try increasing num_nodes.'
        return

    # set position of each node
    if k is None:
        pos = nx.spring_layout(G)
    else:
        pos = nx.spring_layout(G,k=k)

    xpos,ypos=zip(*pos.values())
    nx.set_node_attributes(G,'xpos',dict(zip(pos.keys(),[x*1000 for x in xpos])))
    nx.set_node_attributes(G,'ypos',dict(zip(pos.keys(),[y*1000 for y in ypos])))

    # set the border width of nodes
    if 'node_border_width' not in kwargs.keys():
        kwargs['node_border_width'] = 2

    border_width = {}
    for n in nodes:
        if n in seed_nodes_1 or n in seed_nodes_2:
            border_width[n] = kwargs['node_border_width']
        elif highlight_nodes is not None and n in highlight_nodes:
            border_width[n] = kwargs['node_border_width']
        else:
            border_width[n] = 0

    nx.set_node_attributes(G,'nodeOutline',border_width)

    # set the shape of each node
    nodes_shape=[]
    for node in G.nodes():
        if node in seed_nodes_1:
            nodes_shape.append('triangle')
        elif node in seed_nodes_2:
            nodes_shape.append('square')
        else:
            nodes_shape.append('dot')
    node_to_shape=dict(zip(G.nodes(),nodes_shape))
    nx.set_node_attributes(G,'nodeShape',node_to_shape)

    # add a field for node labels
    if highlight_nodes:
        node_labels = {}
        for node in nodes:
            if node in seed_nodes_1 or n in seed_nodes_2:
                node_labels[node] = node
            elif node in highlight_nodes:
                node_labels[node] = node
            else:
                node_labels[node] = ''
    else:
        node_labels = {n:n for n in nodes}

    nx.set_node_attributes(G,'nodeLabel',node_labels)

    # set the title of each node
    node_titles = [str(node[0]) + '<br/>heat = ' + str(round(node[1]['node_heat'],10))
                   for node in G.nodes(data=True)]
    node_titles = dict(zip(nodes,node_titles))
    nx.set_node_attributes(G,'nodeTitle',node_titles)

    # set the color of each node
    node_to_color = visJS_module.return_node_to_color(G,
                                                      field_to_map='node_heat',
                                                      cmap=node_cmap,
                                                      color_vals_transform='log')

    # set heat value of edge based off hottest connecting node's value
    node_attr = nx.get_node_attributes(G,'node_heat')
    edge_weights = {}
    for e in edges:
        if node_attr[e[0]] > node_attr[e[1]]:
            edge_weights[e] = node_attr[e[0]]
        else:
            edge_weights[e] = node_attr[e[1]]

    nx.set_edge_attributes(G, 'edge_weight', edge_weights)

    # set the color of each edge
    edge_to_color = visJS_module.return_edge_to_color(G,
                                                      field_to_map = 'edge_weight',
                                                      cmap=edge_cmap,
                                                      color_vals_transform = 'log')

    # create the nodes_dict with all relevant fields
    nodes_dict = [{'id':n,
                   'border_width':border_width[n],
                   'degree':G.degree(n),
                   'color':node_to_color[n],
                   'node_label':node_labels[n],
                   'node_size':node_size,
                   'node_shape':node_to_shape[n],
                   'title':node_titles[n],
                   'x':pos[n][0]*1000,
                   'y':pos[n][1]*1000} for n in nodes]

    # map nodes to indices for source/target in edges
    node_map = dict(zip(nodes, range(len(nodes))))

    # create the edges_dict with all relevant fields
    edges_dict = [{'source':node_map[edges[i][0]],
                   'target':node_map[edges[i][1]],
                   'color':edge_to_color[edges[i]]} for i in range(len(edges))]

    # set node_size_multiplier to increase node size as graph gets smaller
    if 'node_size_multiplier' not in kwargs.keys():
        if len(nodes) > 500:
            kwargs['node_size_multiplier'] = 1
        elif len(nodes) > 200:
            kwargs['node_size_multiplier'] = 3
        else:
            kwargs['node_size_multiplier'] = 5

    kwargs['physics_enabled'] = set_physics_enabled(physics_enabled, len(nodes))

    # if node hovering color not set, set default to black
    if 'node_color_hover_background' not in kwargs.keys():
        kwargs['node_color_hover_background'] = 'black'

    # node size determined by size in nodes_dict, not by id
    if 'node_size_field' not in kwargs.keys():
        kwargs['node_size_field'] = 'node_size'

    # node label determined by value in nodes_dict
    if 'node_label_field' not in kwargs.keys():
        kwargs['node_label_field'] = 'node_label'

    # export the network to JSON for Cytoscape
    if export_network:
        node_colors = map_node_to_color(G,'node_heat')
        nx.set_node_attributes(G,'nodeColor',node_colors)
        edge_colors = map_edge_to_color(G,'edge_weight')
        nx.set_edge_attributes(G,'edgeColor',edge_colors)
        export_to_cytoscape(G,export_file)

    return visJS_module.visjs_network(nodes_dict,edges_dict,**kwargs)


def normalized_adj_matrix(G,conserve_heat=True,weighted=False):
    '''
    This function returns normalized adjacency matrix.

    Inputs:
        - G: NetworkX graph from which to calculate normalized adjacency matrix
        - conserve_heat:
            - True: Heat will be conserved (sum of heat vector = 1).  Graph asymmetric
            - False:  Heat will not be conserved.  Graph symmetric.

    Returns:
        - numpy array of the normalized adjacency matrix.
    '''

    wvec=[]
    for e in G.edges(data=True):
        v1 = e[0]
        v2 = e[1]
        deg1 = G.degree(v1)
        deg2 = G.degree(v2)

        if weighted:
            weight = e[2]['weight']
        else:
            weight=1

        if conserve_heat:
            wvec.append((v1,v2,weight/float(deg2))) #np.sqrt(deg1*deg2)))
            wvec.append((v2,v1,weight/float(deg1)))
        else:
            wvec.append((v1,v2,weight/np.sqrt(deg1*deg2)))

    if conserve_heat:
        # if conserving heat, make G_weighted a di-graph (not symmetric)
        G_weighted= nx.DiGraph()
    else:
        # if not conserving heat, make G_weighted a simple graph (symmetric)
        G_weighted = nx.Graph()

    G_weighted.add_weighted_edges_from(wvec)

    Wprime = nx.to_numpy_matrix(G_weighted,nodelist=G.nodes())
    Wprime = np.array(Wprime)

    return Wprime


def network_propagation(G,Wprime,seed_nodes,alpha=.5, num_its=20):
    '''
    This function implements network propagation, as detailed in:
    Vanunu, Oron, et al. 'Associating genes and protein complexes with disease
    via network propagation.'

    Inputs:
        - G: NetworkX graph on which to run simulation
        - Wprime:  Normalized adjacency matrix (from normalized_adj_matrix)
        - seed_nodes:  Genes on which to initialize the simulation.
        - alpha:  Heat dissipation coefficient.  Default = 0.5
        - num_its:  Number of iterations (Default = 20.  Convergence usually happens within 10)

    Returns:
        - Fnew: heat vector after propagation
    '''

    nodes = G.nodes()
    numnodes = len(nodes)
    edges=G.edges()
    numedges = len(edges)

    Fold = np.zeros(numnodes)
    Fold = pd.Series(Fold,index=G.nodes())
    Y = np.zeros(numnodes)
    Y = pd.Series(Y,index=G.nodes())
    for g in seed_nodes:
        # normalize total amount of heat added, allow for replacement
        Y[g] = Y[g]+1/float(len(seed_nodes))
    Fold = Y.copy(deep=True)

    for t in range(num_its):
        Fnew = alpha*np.dot(Wprime,Fold) + np.multiply(1-alpha,Y)
        Fold=Fnew

    return Fnew


def set_physics_enabled(physics_enabled, num_nodes):
    '''
    Sets whether the graph should be physics-enabled or not. Physics simulation
    is turned on by default for graphs of fewer than 100 nodes.

    Inputs:
        - physics-enabled: boolean value user passed in for physics-enabled
        - num_nodes: integer value for number of nodes in the graph

    Returns:
        - True if graph has fewer than 100 nodes, False otherwise.
    '''

    if physics_enabled is None:
        if num_nodes < 100:
            return True
        else:
            return False
    return physics_enabled


def set_num_nodes(G, num_nodes):
    '''
    Sets whether the graph should be physics-enabled or not. It is set for
    graphs of fewer than 100 nodes.

    Inputs:
        - G: a networkX graph
        - num_nodes: the number of the hottest nodes to graph

    Returns:
        - networkX graph that is the subgraph of G with the num_nodes hottest
          nodes
    '''

    if num_nodes != None and num_nodes < len(G.nodes()):
        node_heat = [(node[0], node[1]['node_heat']) for node in G.nodes(data=True)]
        nodes_sorted = sorted(node_heat, key=lambda x: x[1], reverse=True)
        top_hottest_nodes = [nodes_sorted[i][0] for i in range(num_nodes)]
        return G.subgraph(top_hottest_nodes)
    return G


def export_to_cytoscape(G, export_file):
    '''
    Exports networkX graph to JSON file in a Cytoscape compatible format.

    Inputs:
        - G: networkX graph
        - export_file: JSON file name to export graph to

    Returns:
        - None

    Side Effect:
        - Creates a JSON file of the name export_file.
    '''

    G_json = util.from_networkx(G)
    with open(export_file,'w') as outfile:
        json.dump(G_json,outfile)


def map_node_to_color(G,field_to_map):
    '''
    Maps node to color value between 0 and 1 based on the given field.

    Inputs:
        - G: networkX graph
        - field_to_map: node attribute to map color to

    Returns:
        - Dictionary that maps node to color value.
    '''

    node_to_field = dict([(n[0], n[1][field_to_map])
                          for n in G.nodes(data=True)])
    min_val = np.min(node_to_field.values())
    max_val = np.max(node_to_field.values()) - min_val
    color_list = [float(node_to_field[n]-min_val)/max_val for n in G.nodes()]
    return dict(zip(G.nodes(),color_list))


def map_edge_to_color(G,field_to_map):
    '''
    Maps edge to color value between 0 and 1 based on the given field.

    Inputs:
        - G: networkX graph
        - field_to_map: edge attribute to map color to

    Returns:
        - Dictionary that maps edge to color value.
    '''

    edges_data = [(e[0],e[1],e[2][field_to_map])
                  for e in G.edges(data=True)]
    edges1,edges2,data = zip(*edges_data)
    edges_data = zip(zip(edges1,edges2),data)
    edge_to_field = dict(edges_data)
    min_val = np.min(edge_to_field.values())
    max_val = np.max(edge_to_field.values()) - min_val
    color_list = [float(edge_to_field[e]-min_val)/max_val for e in G.edges()]
    return dict(zip(G.edges(),color_list))
