

# Supplemental Information

<a id='toc'></a>
## Table of contents

1. [Analysis of TCGA mutation data](#TCGA_analysis)  
2. [Visualizations](#visualizations)  
  2.1 [Graph Overlap](#graph_overlap)   
  2.2 [Heat propagation](#heat_prop)  
  2.3 [Co-localization](#colocalization)  


<a id='TCGA_analysis'></a>
## 1. Analysis of TCGA mutation data 
As an example of the type of systems biology network analysis enabled by our tool, we display a mutation-disease network built from cancer data. In this analysis, we load the top 25 most mutated genes from 35 TCGA cancer types.  We then create a bipartite network from these data, where one node set is composed of TCGA diseases (triangles), and the other is made up of commonly mutated genes (circles).  Links are drawn between genes and diseases when a gene is commonly mutated in that disease.  This network allows for inspection of mutations which are found almost universally across tumor types, located near the center, including TP53, MUC16, and TTN.  Additionally, we see from this network that there are some mutations which are specific to one disease, or a set of diseases.  These disease-specific mutations are found near the periphery of the graph, and have only a small number of connections.  Genes that have relevant drug targets are outlined in black, and the user may hover over each gene for a list of DrugBank IDs, as well as the number of diseases in which the gene is commonly mutated. The user may click on nodes to see connections, and zoom pan and drag nodes for further inspection of the network.  


<a id='visualizations'></a>
## 2.  Visualizations

<a id='graph_overlap'></a>
### 2.1 Graph overlap


<a id='heat_prop'></a>
### 2.2 Heat propagation


<a id='colocalization'></a>
### 2.3 Co-localization

[Table of contents](#toc)
