#!/usr/bin/env python2.7

#implemementation of solver for min cut problem over a generic undirected,connected graph using gurobi
from gurobipy import *
from graph_utils import *
from re import findall
from copy import deepcopy
import random
global mod		#TODO DEBUG

def _getEdgeFromGurobyVarName(gurobiVarName):
	#extract edge in form [HEAD,TAIL,COST] from gurobi model edge var
	#var name should be like 'edge[HEAD,TAIL,COST] -> parse with regex
	edgeFieldsStr=findall(".*([0-9]+,[0-9]+,[0-9]+).*",gurobiVarName)[0].split(",")
	edge=(int(edgeFieldsStr[0]),int(edgeFieldsStr[1]),int(edgeFieldsStr[2]))
	return edge

def solveMinCut(nodesTrue,edges): 	
	global mod		#TODO DEBUG
	
	#solve min cut problem over graph
	#graph has to be directed and with super source and super sink connected with all nodes with inifity cost edges TODO SET IDENTIFIERS FOR SPECIAL EDGES-SSOURCE-SSINK
	#returned sol: selected edges for the min cut ( subset of input ones)
	mod=Model("minCut")
	#Variables
	zv=mod.addVars(nodesTrue,name="z_node")	
	d_uv=mod.addVars(edges,name="edge")

	#edgesCostVector=list()			#costant vector for obj func	TODO USELESS
	#Constraints
	for e in edges:
		#take edge metadata
		edgeSrcNodeID=e[EDGE_TAIL_INDEX]
		edgeDstNodeID=e[EDGE_HEAD_INDEX]
		
		#actual constraints for each edges
		if edgeSrcNodeID==SUPER_SOURCE_NODE_ID: 			#s,v edge
			mod.addConstr( d_uv[e] + zv[edgeDstNodeID] >= 1 )
		elif edgeDstNodeID==SUPER_DEST_NODE_ID:				#u,t edge  
			mod.addConstr( d_uv[e] - zv[edgeSrcNodeID] >= 0 )
		else:								#real edge
			mod.addConstr( d_uv[e] - zv[edgeSrcNodeID] + zv[edgeDstNodeID] >= 0 )

	#Constraints signs
	mod.addConstrs((d_uv[e] >= 0  for e in edges),name="sign_edge")
	mod.addConstrs((zv[v] >= -GRB.INFINITY  for v in nodesTrue),name="sign_edge")
	#mod.AddConstraints(node[n]  #TODO SOTTOINTESO APPARTENENETE A R ?

	#Objective function
	mod.setObjective(( sum(d_uv[e] * e[EDGE_WEIGHT_INDEX] for e in edges)),GRB.MINIMIZE)

	#gurobi solve
	mod.write("minCutBeforeOptimize.lp")
	mod.optimize()
	mod.write("minCutAfterOptimize.lp")
	#printSolution(mod)
	selectedEdges=list()	#output soulution egdges 
	for edgeVarKey,edgeVarV in d_uv.items():
		if edgeVarV.X >0.0:		#selected edge from solution values of model decision var
			#extract decision var index (that match with the input edge's one) with a regex according standard naming scheme gurobi (as said in gurobi ref manual)
			#TODO ALSO DIRECTLY WITH _colno ? gurobi ref manul not talk about indexing 
			selectedEdges.append(_getEdgeFromGurobyVarName(edgeVarV.varName))
	
	_dumpAllVarsSolution(mod)

	return selectedEdges

def _dumpAllVarsSolution(model):
	vars=model.getVars()
	for v in vars:
		print(v.VarName+"\t->\t"+str(v.X))
	
#def printSolution(model):	#TODO PRINT SOL TEMPLATE FROM DIET MODEL

#    if model.status == GRB.Status.OPTIMAL:
#        print('\nCost: %g' % model.objVal)
#        buyx = model.getAttr('x', buy)
#        for f in foods:
#            if buy[f].x > 0.0001:
#                print('%s %g' % (f, buyx[f]))
#    else:
#        print('No solution')


def minCutLpIterative(graph):
	#search minimal cut with a LP script runned over a graph in witch has been selected a source and a dest
	#iterativelly evaluate min cut relative to all possible nodes pair n1,n2 s.t. n1!=n2 in graph nodes
	#return min cut as list of edges 

	nodes=list(randGraphDir.nodes.keys())
	minCut=None					#output min cut, edges list
	
	#TODO COMBO 2 NESTED FORs
	#for x in range(len(nodes)):
	#	for y in range(x+1,len(nodes)):
	#		n1=nodes[x]
	#		n2=nodes[y]

	for n1 in nodes:
		for n2 in nodes:
			if n1 != n2:
				graphCopy=deepcopy(graph)
				addLocalTerminalNodes(graphCopy,n1,n2)	#add fake SSRC,SDEST to node pair n1,n2
				#graphCopy.build_incidentMatrix()
				#g=drawGraphColored(graphCopy)
				
				#remove teminal nodes for pl script input  
				trueNodes=deepcopy(graphCopy.nodes) #actually not needed deepcopy here
				trueNodes.pop(SUPER_DEST_NODE_ID)
				trueNodes.pop(SUPER_SOURCE_NODE_ID)
				minCutEdges=solveMinCut(trueNodes,graphCopy.extractEdges())
				print("New cut with src/dst node pair: ",(n1,n2),"\t:",minCutEdges)
				if minCut==None or len(minCut)>len(minCutEdges):	#either new min cut founded or first one
					minCut=minCutEdges
					print("founded new minCut from src/dst: ",(n1,n2)," of size: ",len(minCut))
	return minCut
					

import networkx as nx
def stoer_wagner_minCut(graph):
	#get mincut with stoer_wagner algo by netowrkx lib (used for graph draw)
	g= getNetworkxGraph(graph)
	cutVal,nodesParti=nx.stoer_wagner(g)
	print(cutVal)
	print(nodesParti)
	return cutVal

def randMinCut(graph):
	#get min cut of graph by rand algo
	#return edge list of the min cut
	#undirected graph 
	print("RAND MIN CUT OVER:\n")
	print(graph)
	outEdges=list()
	contractedEdges=list()
	#build nodesDegree for quick uniform edge pick
	nodesDegree=dict()
	totDegrees=0
	for nodeID,neighboors in graph.nodes.items():
		nodesDegree[nodeID]=len(neighboors)
		totDegrees+=len(neighboors)
	nodesDegree["TOT"]=totDegrees
	graphContracted=deepcopy(graph)	#copy of src graph for contractions 
	#TODO BATCH REMOVE VERSION -> because at each edge contraction graph will loose 1 node and is needed to stop a 2 remaining nodes
	#I simply select |V| - 2 random edges to contract and then remove all of them
	for i in range (len(graph.nodes) -2 ):
		#PICK UNIFORM RANDOM EDGE 
		#e=graphContracted.pickRandEdge()
		e=uniformRandomEdgeAdjList(graphContracted.nodes,nodesDegree)
		d=graphContracted.contractEdge(e)		#EDGE CONTRACT
		nodesDegree[str(e[EDGE_TAIL_INDEX])+CONTRACT_CHR_SEP+str(e[EDGE_HEAD_INDEX])]=d
		#update degreas dict
		d-=nodesDegree.pop(e[EDGE_TAIL_INDEX])
		d-=nodesDegree.pop(e[EDGE_HEAD_INDEX])
		nodesDegree["TOT"]+=d
	
	#here only 2 node remained
	#Extract graph cut node partition 
	node=list(graphContracted.nodes.keys())[0]	#get 1 of remaining node after contractions
	print(node)
	if type(node)==type(0):		#contraction leaved 1 node alone and all other together
		nodesDeContracted=[node]
	else: 
		nodesDeContracted=node.split(CONTRACT_CHR_SEP) #str list of nodes contracted 
	#extract cut edges
	for n in nodesDeContracted:
		nodeID=int(n)
		nOldNeighs=graph.nodes[nodeID]
		for nodeID2 in nOldNeighs:
			outEdges.append((nodeID,nodeID2,1))
	
	return outEdges


def main():				#TODO DEBUG SWITCH
	global randGraphDir,pruferTreeGraph

	#Generate Tree from a random prufer code arr, then ticken the tree randomly 
	TREE_SIZE=4
	pruferTreeGraph=pruferCodeGenTree(TREE_SIZE,True)
	newNodes,newEdges=graphTickennerRand(pruferTreeGraph,0,2)
	
	g=drawGraph(pruferTreeGraph)
	#adding terminal nodes on directized graph 
	randGraphDir=pruferTreeGraph.directizeGraph()	#make the graph direct
	randGraphDir.build_incidentMatrix()
	#g=drawGraph(randGraphDir)

	#LP ITERATIVE VERSION
	#minCut=minCutLpIterative(randGraphDir)
	#print("FOUNDED MIN CUT:\t",minCut)

	##stoer_wagner_minCut with networkx lib
	#print(stoer_wagner_minCut(pruferTreeGraph))

	#rand cut over graph
	print("RAND MINCUT ",randMinCut(pruferTreeGraph))

if __name__=="__main__":
	main()
