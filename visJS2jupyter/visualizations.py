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

def draw_graph_union(G1, G2, node_cmap=mpl.cm.autumn, edge_cmap=mpl.cm.coolwarm,
                     node_name_1="graph 1", node_name_2="graph 2",
                     physics_enabled=None, **kwargs):
    '''
    Takes two networkX graphs and displays their union, where intersecting nodes
    are triangles. Additional kwargs are passed to visjs_module.

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

    physics_enabled = set_physics_enabled(physics_enabled, numnodes)

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


def draw_heat_prop(G, seed_nodes, node_cmap=mpl.cm.autumn_r, edge_cmap=mpl.cm.autumn_r,
                   physics_enabled=None, num_nodes=None, **kwargs):
    '''
    Implements and displays the network propagation for a given graph and seed nodes.
    Additional kwargs are passed to visJS_module.

    Inputs:
        - G: a networkX graph
        - seed_nodes: nodes on which to initialize the simulation
        - node_cmap: matplotlib colormap for nodes, optional, default: matplotlib.cm.autumn_r
        - edge_cmap: matplotlib colormap for edges, optional, default: matplotlib.cm.autumn_r
        - physics_enabled: boolean, optional, default: True for graphs of 100 nodes, False otherwise
        - num_nodes: the number of the hottest nodes to graph, default: None (all nodes will be graphed)
    Returns:
        - VisJS html network plot (iframe) of the heat propagation.
    '''

    # check for invalid nodes in seed_nodes
    invalid_nodes = [node for node in seed_nodes if node not in G.nodes()]
    for node in invalid_nodes:
        print "Node %s not in graph" % node
    if invalid_nodes:
        return

    Wprime = normalized_adj_matrix(G)
    prop_graph = network_propagation(G, Wprime, seed_nodes).to_dict()
    nx.set_node_attributes(G, 'node_heat', prop_graph)

    # if the user set num_nodes, get the top num_nodes hottest nodes to graph
    G = set_num_nodes(G,num_nodes)
    nodes = G.nodes()
    edges = G.edges()

    # check for empty nodes and edges after getting subgraph of G
    if not nodes:
        print "There are no nodes in the graph. Try increasing num_nodes."
        return
    if not edges:
        print "There are no edges in the graph. Try increasing num_nodes."
        return

    node_to_color = visJS_module.return_node_to_color(G,
                                                      field_to_map = 'node_heat',
                                                      cmap = node_cmap,
                                                      color_vals_transform = 'log')

    # set heat value of edge based off hottest connecting node's value
    node_attr = nx.get_node_attributes(G,'node_heat')
    edge_weights = {}
    for e in edges:
        if node_attr[e[0]] > node_attr[e[1]]:
            edge_weights[e] = node_attr[e[0]]
        else:
            edge_weights[e] = node_attr[e[1]]

    nx.set_edge_attributes(G, 'edge_weight', edge_weights)

    edge_to_color = visJS_module.return_edge_to_color(G,
                                                      field_to_map = 'edge_weight',
                                                      cmap=edge_cmap,
                                                      color_vals_transform = 'log')

    # add a field for node labels
    node_blank_labels = ['']*len(G.nodes())
    node_labels = dict(zip(G.nodes(),node_blank_labels))

    node_titles = [str(node[0]) + '<br/>heat = ' + str(round(node[1]['node_heat'],5))
                   for node in G.nodes(data=True)]
    node_titles = dict(zip(G.nodes(),node_titles))
    pos = nx.spring_layout(G)
    border_width = {n:(2 if n in seed_nodes else 0) for n in nodes}

    nodes_shape=[]
    for node in G.nodes():
        if node in seed_nodes:
            nodes_shape.append('triangle')
        else:
            nodes_shape.append('dot')
    node_to_nodeShape=dict(zip(G.nodes(),nodes_shape))

    nodes_dict = [{"id":n,
                   "degree":G.degree(n),
                   "color":node_to_color[n],
                   "node_size":30,
                   "node_shape":node_to_nodeShape[n],
                   "title":node_titles[n],
                   "x":pos[n][0]*1000,
                   "y":pos[n][1]*1000,
                   "border_width":border_width[n]} for n in nodes]

    node_map = dict(zip(nodes, range(len(nodes))))
    edges_dict = [{"source":node_map[edges[i][0]],
                   "target":node_map[edges[i][1]],
                   "color":edge_to_color[edges[i]]} for i in range(len(edges))]

    # set node_size_multiplier to increase node size as graph gets smaller
    if len(nodes) > 500:
        node_size_multiplier = 1
    elif len(nodes) > 200:
        node_size_multiplier = 3
    else:
        node_size_multiplier = 5

    physics_enabled = set_physics_enabled(physics_enabled, len(nodes))

    return visJS_module.visjs_network(nodes_dict, edges_dict,
                                      node_size_field='node_size',
                                      node_size_multiplier=node_size_multiplier,
                                      physics_enabled=physics_enabled,
                                      node_color_hover_background='black',
                                      **kwargs)


def draw_colocalization(G,seed_nodes_1, seed_nodes_2, node_cmap=mpl.cm.autumn_r,
                        edge_cmap=mpl.cm.autumn_r, physics_enabled=None,
                        num_nodes=None, **kwargs):
    '''
    Implements and displays the network propagation for a given graph and two
    sets of seed nodes.
    Additional kwargs are passed to visJS_module.

    Inputs:
        - G: a networkX graph
        - seed_nodes_1: first set of nodes on which to initialize the simulation
        - seed_nodes_2: second set of nodes on which to initialize the simulation
        - node_cmap: matplotlib colormap for nodes, optional, default: matplotlib.cm.autumn_r
        - edge_cmap: matplotlib colormap for edges, optional, default: matplotlib.cm.autumn_r
        - physics_enabled: boolean, optional, default: True for graphs of 100 nodes, False otherwise
        - num_nodes: the number of the hottest nodes to graph, default: None (all nodes will be graphed)
    Returns:
        - VisJS html network plot (iframe) of the colocalization.
    '''

    # check for invalid nodes in seed_nodes
    invalid_nodes = [(node,'seed_nodes_1') for node in seed_nodes_1 if node not in G.nodes()]
    invalid_nodes.extend([(node,'seed_nodes_2') for node in seed_nodes_2 if node not in G.nodes()])
    for node in invalid_nodes:
        print "Node %s in %s not in graph" % (node[0], node[1])
    if invalid_nodes:
        return

    Wprime = normalized_adj_matrix(G)
    prop_graph_1 = network_propagation(G, Wprime, seed_nodes_1).to_dict()
    prop_graph_2 = network_propagation(G, Wprime, seed_nodes_2).to_dict()
    prop_graph = {node:(prop_graph_1[node]*prop_graph_2[node]) for node in prop_graph_1}
    nx.set_node_attributes(G, 'node_heat', prop_graph)

    # if the user set num_nodes, get the top num_nodes hottest nodes to graph
    G = set_num_nodes(G,num_nodes)
    nodes = G.nodes()
    edges = G.edges()

    # check for empty nodes and edges after getting subgraph of G
    if not nodes:
        print "There are no nodes in the graph. Try increasing num_nodes."
        return
    if not edges:
        print "There are no edges in the graph. Try increasing num_nodes."
        return

    node_to_color = visJS_module.return_node_to_color(G,
                                                      field_to_map = 'node_heat',
                                                      cmap = node_cmap,
                                                      color_vals_transform = 'log')

    # set heat value of edge based off hottest connecting node's value
    node_attr = nx.get_node_attributes(G,'node_heat')
    edge_weights = {}
    for e in edges:
        if node_attr[e[0]] > node_attr[e[1]]:
            edge_weights[e] = node_attr[e[0]]
        else:
            edge_weights[e] = node_attr[e[1]]

    nx.set_edge_attributes(G, 'edge_weight', edge_weights)

    edge_to_color = visJS_module.return_edge_to_color(G,
                                                      field_to_map = 'edge_weight',
                                                      cmap=edge_cmap,
                                                      color_vals_transform = 'log')

    # add a field for node labels
    node_blank_labels = ['']*len(nodes)
    node_labels = dict(zip(nodes,node_blank_labels))

    node_titles = [str(node[0]) + '<br/>heat = ' + str(round(node[1]['node_heat'],10))
                   for node in G.nodes(data=True)]
    node_titles = dict(zip(nodes,node_titles))
    pos = nx.spring_layout(G)
    border_width = {n:(3 if n in seed_nodes_1 or n in seed_nodes_2 else 0) for n in nodes}

    nodes_shape=[]
    for node in G.nodes():
        if node in seed_nodes_1:
            nodes_shape.append('triangle')
        elif node in seed_nodes_2:
            nodes_shape.append('square')
        else:
            nodes_shape.append('dot')
    node_to_nodeShape=dict(zip(G.nodes(),nodes_shape))

    nodes_dict = [{"id":n,
                   "degree":G.degree(n),
                   "color":node_to_color[n],
                   "node_size":30,
                   "node_shape":node_to_nodeShape[n],
                   "title":node_titles[n],
                   "x":pos[n][0]*1000,
                   "y":pos[n][1]*1000,
                   "border_width":border_width[n]} for n in nodes]

    node_map = dict(zip(nodes, range(len(nodes))))
    edges_dict = [{"source":node_map[edges[i][0]],
                   "target":node_map[edges[i][1]],
                   "color":edge_to_color[edges[i]]} for i in range(len(edges))]

    # set node_size_multiplier to increase node size as graph gets smaller
    if len(nodes) > 500:
        node_size_multiplier = 1
    elif len(nodes) > 200:
        node_size_multiplier = 3
    else:
        node_size_multiplier = 5

    physics_enabled = set_physics_enabled(physics_enabled, len(nodes))

    return visJS_module.visjs_network(nodes_dict, edges_dict,
                                      node_size_field='node_size',
                                      node_size_multiplier=node_size_multiplier,
                                      physics_enabled=physics_enabled,
                                      node_color_hover_background='black',
                                      **kwargs)


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
        Y[g] = Y[g]+1/float(len(seed_nodes)) # normalize total amount of heat added, allow for replacement
    Fold = Y.copy(deep=True)

    for t in range(num_its):
        Fnew = alpha*np.dot(Wprime,Fold) + np.multiply(1-alpha,Y)
        Fold=Fnew

    return Fnew


def set_physics_enabled(physics_enabled, num_nodes):
    '''
    Sets whether the graph should be physics-enabled or not. It is set for
    graphs of fewer than 100 nodes.

    Inputs:
        - physics-enabled: boolean value user passed in for physics-enabled
        - num_nodes: integer value for number of nodes in the graph
    Returns:
        - True if graph has fewer than 100 nodes, False otherwise.
    '''

    if physics_enabled == None:
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
