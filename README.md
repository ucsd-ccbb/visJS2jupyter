# visJS_2_jupyter
visJS_2_jupyter is a tool to bring the interactivity of networks created with vis.js into jupyter notebook cells, authored by members of the UCSD Center for Computational Biology & Bioinformatics (http://compbio.ucsd.edu)
--------------

Authors: Brin Rosenthal (sbrosenthal@ucsd.edu), Mikayla Webster (m1webste@ucsd.edu), Aaron Gary (agary@ucsd.edu)


A simple use example is included in the notebooks folder (and the interactive version may be found HERE).  In the example provided, we show how to display a graph created with NetworkX using visJS_2_jupyter.  Here the networks displayed within Jupyter notebook cells may be dragged, clicked, and hovered on, and zooming is enabled within the window.  Nodes and edges may be styled with properties available from vis.js networks (see http://visjs.org/docs/network/ for a list and description of properties).  The main function is 'visjs_network', which requires two inputs which describe the nodes and edges in the network- 'nodes_dict', and edges_dict'.  The other arguments are optional, and apply general styles to the graph, such as sizes, highlight colors, and physics properties of the graph.  
