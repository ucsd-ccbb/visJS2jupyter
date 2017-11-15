# # More complex network styling for visJS2jupyter
# ------------
# 
# Authors: Brin Rosenthal (sbrosenthal@ucsd.edu), Mikayla Webster (m1webste@ucsd.edu), Julia Len (jlen@ucsd.edu)
# Authors: Amro Tork (amtc2018@gmail.com)
# 
# -----------

import matplotlib as mpl
import networkx as nx
import visJS2jupyter.visJS_module


# create a simple graph
G = nx.connected_watts_strogatz_graph(30,5,.2)
nodes = list(G.nodes()) # type cast to list in order to make compatible with networkx 1.11 and 2.0
edges = list(G.edges()) # for nx 2.0, returns an "EdgeView" object rather than an iterable

# add a node attributes to color-code by
cc = nx.clustering(G)
degree = dict(G.degree()) # nx 2.0 returns a "DegreeView" object. Cast to dict to maintain compatibility with nx 1.11
bc = nx.betweenness_centrality(G)
nx.set_node_attributes(G, name = 'clustering_coefficient', values = cc) # parameter order for name and values is switched 
nx.set_node_attributes(G, name = 'degree', values = degree)             # between networkx 1.11 and 2.0, therefore we must
nx.set_node_attributes(G, name = 'betweenness_centrality', values = bc) # explicitly pass our arguments 
                                                                        # (not implicitly through position)
# map the betweenness centrality to the node color, using matplotlib spring_r colormap
node_to_color = visJS2jupyter.visJS_module.return_node_to_color(G,field_to_map='betweenness_centrality',cmap=mpl.cm.spring_r,alpha = 1,
                                                 color_max_frac = .9,color_min_frac = .1)

# set node initial positions using networkx's spring_layout function
pos = nx.spring_layout(G)

nodes_dict = [{"id":n,"color":node_to_color[n],
               "degree":nx.degree(G,n),
              "x":pos[n][0]*1000,
              "y":pos[n][1]*1000} for n in nodes
              ]
node_map = dict(zip(nodes,range(len(nodes))))  # map to indices for source/target in edges
edges_dict = [{"source":node_map[edges[i][0]], "target":node_map[edges[i][1]], 
              "color":"gray","title":'test'} for i in range(len(edges))]

# set some network-wide styles
graph = visJS2jupyter.visJS_module.visjs_network(nodes_dict,edges_dict,
                          node_size_multiplier=7,
                          node_size_transform = '',
                          node_color_highlight_border='red',
                          node_color_highlight_background='#D3918B',
                          node_color_hover_border='blue',
                          node_color_hover_background='#8BADD3',
                          node_font_size=25,
                          edge_arrow_to=True,
                          physics_enabled=True,
                          edge_color_highlight='#8A324E',
                          edge_color_hover='#8BADD3',
                          edge_width=3,
                          max_velocity=15,
                          min_velocity=1)

visJS2jupyter.visJS_module.save_to_html(graph,"complex_example.html")
