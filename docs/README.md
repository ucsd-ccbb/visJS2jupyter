

# Supplemental Information

<a id='toc'></a>
## Table of contents

1. [Analysis of TCGA mutation data](#TCGA_analysis)  
2. [Visualizations](#visualizations)  
  2.1 [Graph Overlap](#graph_overlap)   
  2.2 [Heat propagation](#heat_prop)  
  2.3 [Co-localization](#colocalization) 
3. [Tips on usage](#usage_tips)  
  3.1 [Multiple networks in the same notebook](#graphid)  
  3.2 [Mapping colors to nodes and edges](#map_colors)  
  3.3 [High resolution images](#high_res)  
  3.4 [Exporting to Cytoscape compatible format](#cytoscape)  
4. [Validating network propagation with known Autism risk genes](#asd_validation)  
5. [Arguments](#arguments)  
  5.1 [Required arguments](#required)  
  5.2 [Node-specific arguments](#node_specific)  
  5.3 [Edge-specific arguments](#edge_specific)  
  5.4 [Interaction-specific arguments](#interaction_specific)  
  5.5 [Configuration-specific arguments](#configuration_specific)  
  5.6 [Miscellaneous arguments](#miscellaneous)  
  


<a id='TCGA_analysis'></a>
## 1. Analysis of TCGA mutation data 
As an example of the type of systems biology network analysis enabled by our tool, we display a mutation-disease network built from cancer data. In this analysis, we load the top 25 most mutated genes from 35 TCGA cancer types.  We then create a bipartite network from these data, where one node set is composed of TCGA diseases (triangles), and the other is made up of commonly mutated genes (circles).  Links are drawn between genes and diseases when a gene is commonly mutated in that disease.  This network allows for inspection of mutations which are found almost universally across tumor types, located near the center, including TP53, MUC16, and TTN.  Additionally, we see from this network that there are some mutations which are specific to one disease, or a set of diseases.  These disease-specific mutations are found near the periphery of the graph, and have only a small number of connections.  Genes that have relevant drug targets are outlined in black, and the user may hover over each gene for a list of DrugBank IDs, as well as the number of diseases in which the gene is commonly mutated. The user may click on nodes to see connections, and zoom pan and drag nodes for further inspection of the network.  


<a id='visualizations'></a>
## 2.  Visualizations

Visualizations is a supplementary module that calls visJS_module to perform operations on graphs, and to visualize their results.  These functions include the overlap of two graphs, heat propagation, and co-localization. Users simply provide a network in NetworkX format, and when called, the function performs the desired operation. The function then visualizes the output in the notebook cell. Many customizations are possible for the graph, such as the color maps used for nodes and edges. Furthermore, users can customize the physics simulation of their networks. The physics simulation provides another interactive element of the graph that enables users to view the connectivity of nodes when dragging them. By default, the physics simulation is turned on for networks of fewer than 100 nodes and turned off otherwise. All arguments available in visJS_module for network customization are also available in visualizations. 


<a id='graph_overlap'></a>
### 2.1 Graph overlap

When working with networks, it is often useful to consider how similar two networks are. The function draw_graph_overlap introduces a network overlap visualization function to allow comparisons between networks. This function takes in two NetworkX graphs and displays a single graph of their union. Intersecting nodes are triangles and non-intersecting nodes are either circles or squares, depending on which graph they belong to. A simple example can be found at https://bl.ocks.org/julialen/raw/d21c9d378cb09b5a7181497101996727/.

![Graph overlap](https://github.com/ucsd-ccbb/visJS2jupyter/blob/master/docs/graph_overlap.png?raw=true)



<a id='heat_prop'></a>
### 2.2 Heat propagation

We implement the network propagation method developed in (Vanunu et al. 2010), which simulates how heat would diffuse, with loss, through the network by traversing the edges, starting from an initially hot set of ‘seed’ nodes.  At each step, one unit of heat is added to the seed nodes, and is then spread to the neighbor nodes.  A constant fraction of heat is then removed from each node, so that heat is conserved in the system.  After a number of iterations, the heat on the nodes converges to a stable value.  This final heat vector is a proxy for how close each node is to the seed set.  For example, if a node was between two initially hot nodes, it would have an extremely high final heat value, and alternatively if a node was quite far from the initially hot seed nodes, it would have a very low final heat value. This process is described in (Vanunu et al. 2010):

Heat propagation is useful for visualizing network propagation from a set of seed nodes. The function draw_heat_prop draws this visualization when provided with a NetworkX graph and a list of seed nodes. Using the list of seed nodes, it calculates the heat value of each node based on how connected it is to the seed nodes. Seed nodes are depicted with a triangular shape to distinguish them from other nodes. By default, hot nodes are colored red with cooler nodes gradually fading to yellow. The edges are also colored from red to yellow, depending on the heat of the nodes they are connecting. The overall effect is a clear visualization of how the heat from the seed nodes spreads throughout the network. If including all nodes in the graph produces a cluttered network, draw_heat_prop provides the argument ‘num_nodes’ to specify how many nodes the network should include. This argument finds the num_nodes number of hottest nodes and only graphs those. An example of a network drawn by draw_heat_prop can be found at https://bl.ocks.org/julialen/raw/82c316048ade650effbff3fd9eaddccd/.



<a id='colocalization'></a>
### 2.3 Co-localization

Co-localization works similarly to heat propagation but requires two sets of seed nodes instead of one. The function draw_colocalization creates a network visualization of this propagation. Seed nodes belonging to one set are shaped as triangles while seed nodes belonging to the other set are shaped as squares. Heat values are calculated by running a heat propagation simulation with one set of seed nodes and then a different propagation using the other set of seed nodes. The product of the heat values in each simulation becomes each node’s heat value in the final graph. An example can be found at https://bl.ocks.org/julialen/raw/a82040bdc8b5ba3ca866489db795af74/.

[Table of contents](#toc)
<a id='usage_tips'></a>
## 3. Tips on usage



[Table of contents](#toc)
<a id='graphid'></a>
### 3.1 Multiple networks in the same notebook
visJS2jupyter takes parameters specified by the user and then creates an HTML file that contains the vis.js code to draw the network visualization. Each graph generates its own HTML file. The Jupyter notebook cell then renders this HTML file to produce the visualization. To create multiple graphs in one notebook, use the graph_id argument to specify an identification for the graph. Each different graph_id will generate a different HTML file.



<a id='map_colors'></a>
### 3.2 Mapping colors to nodes and edges
Color-coding nodes and edges is a common way of mapping complex layers of information to a graph. The functions return_node_to_color and return_edge_to_color included in the package provide the means with which to do this. The return_node_to_color function creates a dictionary mapping of nodes to color values based on the specified colormap and node attribute to map. Similarly, return_edge_to_color creates a dictionary mapping of edges to color values. Any node or edge level property can be mapped to node color or edge color, as long as it is represented numerically, and added as a node/edge attribute. Use the argument field_to_map to specify this property. The user can also utilize the argument cmap to specify which matplotlib colormap to use for the color mapping. 


<a id='high_res'></a>
### 3.3 High resolution images
In order to save high resolution images, we include the ‘scaling_factor’ argument, which scales up each graph element and increase its resolution. To save the image, right-click on the notebook cell and select ‘save as’.  For most graphs an adequately high-resolution image is obtained from setting the scaling_factor between three and five. 



<a id='cytoscape'></a>
### 3.4 Exporting to cytoscape compatible format

To export to a cytoscape compatible format, set the ‘export_network’ argument to True in the visualization functions.  The network, with attributes, will be saved in a Cytoscape compatible JSON format.  To change the default file name, set the ‘export_file’ argument to the desired name.  Once the network has been saved, open Cytoscape and load the file.  To reproduce the network as it looked in the Jupyter cell, load the corresponding Cytoscape style file (provided where in the GitHub repository https://github.com/ucsd-ccbb/visJS2jupyter/tree/master/cytoscape_styles), and apply it to the network.

[Table of contents](#toc)
<a id='asd_validation'></a>
## 4. Validating network propagation with known Autism risk genes

We validate the network propagation technique as a method for prioritizing disease risk genes, from a set of genes known to be involved in the disease.  We start with the large set of genes known to be involved in Autism, as our set of seed genes, and the STRING (REF) interactome as our background network for propagation.  

To test if the network propagation function will be useful for gene prioritization, we randomly select a subset of n genes from the total list of 859, run the network propagation function from these n genes on the STRING interactome, and then count the number of withheld Autism genes which appear in the top N hottest genes.  If the method works, we will find many withheld Autism genes in the top set, because we expect disease-related genes to be near other disease-related genes, in network space.  To establish a baseline, we run a control condition.  We randomly select 859 control genes, C from the genome, and repeat the prioritization test on this set.  That is, we randomly select n genes from the control set C to use as seeds for the network propagation, and measure the number of withheld control genes which are recovered in the top N hottest genes.  This experiment is repeated k=100 times for each value of N (Figure ??, where we plot the fraction of recovered withheld disease risk genes recovered for Autism (red) and Control (black)).  Consistently we recover many more Autism genes than Control genes, in the simulation, indicating that the network propagation method works as a prioritization technique, as expected.

Analysis for this result may be found in Jupyter notebook form (HERE). 

[Table of contents](#toc)
<a id='arguments'></a>
## 5. Arguments

<a id='required'></a>
### 5.1 Required arguments

[Table of contents](#toc)
<a id='node_specific'></a>
### 5.2 Node-specific arguments

[Table of contents](#toc)
<a id='edge_specific'></a>
### 5.3 Edge-specific arguments

[Table of contents](#toc)
<a id='interaction_specific'></a>
### 5.4 Interaction-specific arguments

[Table of contents](#toc)
<a id='configuration_specific'></a>
### 5.5 Configuration-specific arguments

[Table of contents](#toc)
<a id='miscellaneous'></a>
### 5.6 Miscellaneous arguments
[Table of contents](#toc)
