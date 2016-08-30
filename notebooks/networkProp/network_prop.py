"""
 -----------------------------------------------------------------------

Author: Brin Rosenthal (sbrosenthal@ucsd.edu)

 -----------------------------------------------------------------------
"""


import matplotlib.pyplot as plt
import seaborn
import networkx as nx
import pandas as pd
import random
import numpy as np
import itertools
import json
import scipy
#import community
from sklearn.cluster import AffinityPropagation
from sklearn.cluster import AgglomerativeClustering


def normalized_adj_matrix(G,conserve_heat=True,weighted=False):
    
    '''
    This function returns normalized adjacency matrix.
    
    Inputs:
        - G: NetworkX graph from which to calculate normalized adjacency matrix
        - conserve_heat:
            - True: Heat will be conserved (sum of heat vector = 1).  Graph asymmetric
            - False:  Heat will not be conserved.  Graph symmetric.
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

def network_propagation(G,Wprime,seed_genes,alpha=.5, num_its=20):
    
    '''
    This function implements network propagation, as detailed in:
    Vanunu, Oron, et al. 'Associating genes and protein complexes with disease via network propagation.'
    Inputs:
        - G: NetworkX graph on which to run simulation
        - Wprime:  Normalized adjacency matrix (from normalized_adj_matrix)
        - seed_genes:  Genes on which to initialize the simulation.
        - alpha:  Heat dissipation coefficient.  Default = 0.5
        - num_its:  Number of iterations (Default = 20.  Convergence usually happens within 10)
        
    Outputs:
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
    for g in seed_genes:
        Y[g] = Y[g]+1/float(len(seed_genes)) # normalize total amount of heat added, allow for replacement
    Fold = Y.copy(deep=True)
    for t in range(num_its):
        Fnew = alpha*np.dot(Wprime,Fold) + np.multiply(1-alpha,Y)
        Fold=Fnew
    return Fnew
    
    
def get_corr_rand_set(G,disease_seeds,num_reps=5,alpha=.5,num_its=20,conserve_heat=True):
    '''
    
    Calculate the dot-product of heat propagated on N disease gene sets (disease_seeds: dict with keys disease names and values lists of disease genes), on an edge-shuffled, degree-preserving random matrix, with number of repetitions = num_reps, alpha=alpha, num_its = num_its.
    
    Return the mean of the dot-product averaged over num_reps, and the standard deviation over num_reps, over all pairs of gene sets in disease_seeds.  This way we only have to create one random matrix for each pair, which will speed up processing time a bit.
    
    '''
    
    num_Ds = len(disease_seeds)
    
    dnames = disease_seeds.keys()
    
    dname_pairs = list(itertools.combinations(dnames, 2))
        
    
    dot_rand=dict()
    dot_rand_mean = dict()
    dot_rand_std = dict()
    for d in dname_pairs:
        # initialize dictionaries
        dot_rand[d] = []
        dot_rand_mean[d] = []
        dot_rand_std[d] = []
    
    for r in range(num_reps):
        G_temp = nx.configuration_model(G.degree().values())
        G_rand = nx.Graph()  # switch from multigraph to digraph
        G_rand.add_edges_from(G_temp.edges())
        # remove self-loops
        #G_rand.remove_edges_from(G_rand.selfloop_edges())
        G_rand = nx.relabel_nodes(G_rand,dict(zip(range(len(G_rand.nodes())),G.degree().keys())))
        Wprime_rand = normalized_adj_matrix(G_rand,conserve_heat=conserve_heat)
        
        
        for i in range(len(dname_pairs)):
            seeds_D1 = disease_seeds[dname_pairs[i][0]]
            seeds_D2 = disease_seeds[dname_pairs[i][1]]
        
            Fnew_D1 = network_propagation(G_rand,Wprime_rand,seeds_D1,alpha=alpha,num_its=num_its)
            Fnew_D1_norm = Fnew_D1/np.linalg.norm(Fnew_D1)
        
            rand_seeds = seeds_D2 #set(random.sample(G.nodes(),size_rand_set))
            Fnew_D2 = network_propagation(G_rand,Wprime_rand,seeds_D2,alpha=alpha,num_its=num_its)
            Fnew_D2_norm = Fnew_D2/np.linalg.norm(Fnew_D2)

            idx_g0 = list(Fnew_D1[(Fnew_D1>0)&(Fnew_D2>0)].index)
            idx_ND1ND2 = list(np.setdiff1d(list(Fnew_D1.index),np.union1d(seeds_D1,seeds_D2)))
            
            dot_D1_D1 = np.dot(Fnew_D1_norm,Fnew_D2_norm)
                
            dot_rand[dname_pairs[i]].append(dot_D1_D1)
        
    
    for d in dname_pairs:
        dot_rand_mean[d] = np.mean(dot_rand[d])
        dot_rand_std[d] = np.std(dot_rand[d])

    
    return dot_rand_mean,dot_rand_std

def calc_3way_colocalization(Gint,genes_sfari, genes_EPI, genes_AEM, write_file_name = 'colocalization_results.csv',
                             num_reps=5, num_genes = 20, subsample=True, conserve_heat=True, print_flag=True,
                             exclude_overlap=True,replace=True,savefile=True,alpha=.5):
    
    '''
    
    Calculate co-localization between three gene sets, using network propagation
    
    Inputs:
        - Gint: Background interactome 
        - genes_sfari, genes_EPI, genes_AEM:  Three input gene sets (can be sets or lists)
        - write_file_name:  Name for file to write results to, if savefile = True.  Default = 'colocalization_results.csv'
        - num_reps:  Number of samples.  Default = 5
        - num_genes:  Number of genes to sample from each input gene set, if subsample=True.  Default = 20
        - subsample:  Select if you want to subsample input gene lists.  If False, entire length of gene lists are sampled (can be different lengths).  Default = True. 
        - conserve_heat:  Select if you want heat propagation to conserve heat (if True, sum(heat vector F) at each step = 1).  Default = True
        - print_flag:  Select if you want to print out some diagnostics.  Default = True
        - exclude_overlap:  Select if you want to include overlapping genes in input gene lists (e.g. what to do if the same gene appears in multiple sets).  If True, all overlapping genes will be discarded from input gene lists.  Default = True
        - replace:  Select if you want to allow replacement in sampling.  Default = True
        - savefile:  Select if you want to save the results to a file.  Default = True
        - alpha:  Set the heat dissipation coefficient.  Default = 0.5
        
    Returns:
        - results_dict:  A dictionary containing the following key-value pairs:
            - 'aem_epi', 'sfari_aem', 'sfari_epi':  Dot products of heat vectors between three input gene lists
            - 'aem_epi_rand', 'aem_sfari_rand', 'sfari_epi_rand':  Dot products of heat vectors between three input gene lists on edge-shuffled networks.
            - 'num_reps':  Number of samples
            - 'num_genes_S','num_genes_E','num_genes_A':  Number of genes sampled from each of the three input lists
            - 'conserve_heat':  Boolean- input parameter
            - 'exclude_overlap':  Boolean- input parameter
            - 'replace':  Boolean- input parameter
            - 'subsample':  Boolean- input parameter

    '''

    seed_SFARI = list(np.intersect1d(list(genes_sfari),Gint.nodes()))
    seed_EPI = list(np.intersect1d(list(genes_EPI),Gint.nodes()))
    seed_AEM = list(np.intersect1d(list(genes_AEM),Gint.nodes()))
    
    
    Wprime = normalized_adj_matrix(Gint,conserve_heat=conserve_heat)

    # exclude genes which appear in multiple diseases
    if exclude_overlap:
        seed_SFARI = list(np.setdiff1d(seed_SFARI,seed_AEM))
        seed_EPI = list(np.setdiff1d(seed_EPI,seed_AEM))
        seed_EPI = list(np.setdiff1d(seed_EPI,seed_SFARI))
        
    if subsample:
        num_genes_S=num_genes
        num_genes_E=num_genes
        num_genes_A=num_genes
    else:
        num_genes_S=len(seed_SFARI)
        num_genes_E=len(seed_EPI)
        num_genes_A=len(seed_AEM)

    dot_sfari_epi=[]
    dot_sfari_aem=[]
    dot_aem_epi=[]

    dot_aem_epi_rand, dot_aem_sfari_rand, dot_sfari_epi_rand= [],[],[]
    dot_aem_epi_std, dot_aem_sfari_std, dot_sfari_epi_std = [],[],[]
    for r in range(num_reps):
        if print_flag:
            print(r)
        # sample N genes from each list
        subset_SFARI = np.random.choice(seed_SFARI,size=num_genes_S,replace=replace)
        subset_EPI = np.random.choice(seed_EPI,size=num_genes_E,replace=replace)
        subset_AEM = np.random.choice(seed_AEM,size=num_genes_A,replace=replace)

        Fnew_SFARI = network_propagation(Gint,Wprime,subset_SFARI,alpha=alpha,num_its=20)
        Fnew_EPI = network_propagation(Gint,Wprime,subset_EPI,alpha=alpha,num_its=20)
        Fnew_AEM = network_propagation(Gint,Wprime,subset_AEM,alpha=alpha,num_its=20)

        Fnew_SFARI_norm = Fnew_SFARI/np.linalg.norm(Fnew_SFARI)
        Fnew_EPI_norm = Fnew_EPI/np.linalg.norm(Fnew_EPI)
        Fnew_AEM_norm = Fnew_AEM/np.linalg.norm(Fnew_AEM)

        dot_sfari_epi.append(np.dot(Fnew_SFARI_norm,Fnew_EPI_norm))
        dot_sfari_aem.append(np.dot(Fnew_SFARI_norm,Fnew_AEM_norm))
        dot_aem_epi.append(np.dot(Fnew_AEM_norm,Fnew_EPI_norm))

        disease_seeds = dict()
        disease_seeds['EPI']=subset_EPI
        disease_seeds['SFARI']=subset_SFARI
        disease_seeds['AEM']=subset_AEM
        dot_rand_mean, dot_rand_std = get_corr_rand_set(Gint,disease_seeds,num_reps=1,alpha=alpha,conserve_heat=conserve_heat)

        dot_aem_epi_rand.append(dot_rand_mean[('AEM','EPI')])
        dot_aem_epi_std.append(dot_rand_std[('AEM','EPI')])

        dot_aem_sfari_rand.append(dot_rand_mean[('AEM','SFARI')])
        dot_aem_sfari_std.append(dot_rand_std[('AEM','SFARI')])

        dot_sfari_epi_rand.append(dot_rand_mean[('SFARI','EPI')])
        dot_sfari_epi_std.append(dot_rand_std[('SFARI','EPI')])

        if print_flag:
            print(dot_sfari_epi[-1])
            print(dot_sfari_epi_rand[-1])
            print(dot_sfari_aem[-1])
            print(dot_aem_sfari_rand[-1])
            print(dot_aem_epi[-1])
            print(dot_aem_epi_rand[-1])

        

    results_dict = {'B_C':dot_aem_epi, 'A_C':dot_sfari_aem, 'A_B':dot_sfari_epi,
                    'B_C_rand':dot_aem_epi_rand,
                    'A_C_rand':dot_aem_sfari_rand,
                    'A_B_rand':dot_sfari_epi_rand,
                    'num_reps':num_reps,
                    'num_genes_A':num_genes_S, 'num_genes_B':num_genes_E, 'num_genes_C':num_genes_A,
                    'conserve_heat':conserve_heat,
                    'exclude_overlap':exclude_overlap,'replace':replace,
                    'subsample':subsample}
    
    # write results to json
    if savefile:
        json.dump(results_dict, open(write_file_name,'w'))
    
    return results_dict
    
    

def calc_localization(Gint,genes_focal,write_file_name='localization_results',num_reps=5,num_genes=20,
                     conserve_heat=True, replace=True,subsample=True, savefile=True):
    
    seed_FOCAL = list(np.intersect1d(list(genes_focal),Gint.nodes()))
    
    if subsample:
        num_genes_S=num_genes
    else:
        num_genes_S=len(seed_FOCAL)

    Wprime = normalized_adj_matrix(Gint,conserve_heat=conserve_heat)
    
    kurt_FOCAL =[]
    kurt_Srand=[]
    var_FOCAL, var_Srand=[],[]
    sumTop_FOCAL= []
    sumTop_Srand= []
    for r in range(num_reps):
        print(r)
        
        subset_FOCAL = np.random.choice(seed_FOCAL,size=num_genes_S,replace=replace)

        Fnew_FOCAL = network_propagation(Gint,Wprime,subset_FOCAL,alpha=.5,num_its=20)
        Fnew_FOCAL.sort()
        kurt_FOCAL.append(scipy.stats.kurtosis(Fnew_FOCAL))
        var_FOCAL.append(np.var(Fnew_FOCAL))
        sumTop_FOCAL.append(np.sum(Fnew_FOCAL.head(1000)))

        G_temp = nx.configuration_model(Gint.degree().values())
        G_rand = nx.Graph()  # switch from multigraph to digraph
        G_rand.add_edges_from(G_temp.edges())
        # remove self-loops
        #G_rand.remove_edges_from(G_rand.selfloop_edges())
        G_rand = nx.relabel_nodes(G_rand,dict(zip(range(len(G_rand.nodes())),Gint.degree().keys())))
        Wprime_rand = normalized_adj_matrix(G_rand,conserve_heat=conserve_heat)

        Fnew_Srand = network_propagation(G_rand,Wprime_rand,subset_FOCAL,alpha=.5,num_its=20)
        Fnew_Srand.sort()
        kurt_Srand.append(scipy.stats.kurtosis(Fnew_Srand))
        var_Srand.append(np.var(Fnew_Srand))
        sumTop_Srand.append(np.sum(Fnew_Srand.head(1000)))

        print(var_FOCAL[-1])
        print(var_Srand[-1])
    
    results_dict = {'kurtosis':kurt_FOCAL,'kurt_rand':kurt_Srand,
                   'var':var_FOCAL,'var_rand':var_Srand,
                   'sumTop':sumTop_FOCAL, 'sumTop_rand':sumTop_Srand,
                   'num_reps':num_reps, 'conserve_heat':conserve_heat,
                   'replace':replace,'subsample':subsample,'num_genes':num_genes}
    
    if savefile:
        json.dump(results_dict,open(write_file_name,'w'))
        
    return results_dict



def calc_pos_labels(pos,dx=.03):
    
    '''
    Helper function to return label positions offset by dx
    
    - input node positions from nx.spring_layout()
    
    '''
    
    pos_labels = dict()
    for key in pos.keys():
        pos_labels[key] = np.array([pos[key][0]+dx,pos[key][1]+dx])
    
    return pos_labels






