#!/usr/bin/env python2.7

#implemementation of solver for min cut problem over a generic undirected,connected graph using gurobi
from gurobipy import *
from graph_utils import *
from re import findall
from copy import deepcopy

global mod		#TODO DEBUG
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
	#for edgeVarKey,edgeVarV in d_uv.items():
	#	if edgeVarV.X >0.0:		#selected edge from solution values of model decision var
	#		#extract decision var index (that match with the input edge's one) with a regex according standard naming scheme gurobi (as said in gurobi ref manual)
	#		edgeVarIndex=int(findall(".+\[(.*)\]",edgeVarV.VarName)[0]) 
	#		#TODO ALSO DIRECTLY WITH _colno ? gurobi ref manul not talk about indexing 
	#		selectedEdges.append(edges[edgeVarIndex])	#append selected edge by same indexing input edges <-> decision var
	#
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

#if __name__=="__main__":		#TODO DEBUG SWITCH
def main():				#TODO DEBUG SWITCH
	global randGraphDir,pruferTreeGraph

	#Generate Tree from a random prufer code arr, then ticken the tree randomly 
	TREE_SIZE=3
	pruferTreeGraph=pruferCodeGenTree(TREE_SIZE,True)
	newNodes,newEdges=graphTickennerRand(pruferTreeGraph,0,5)
	#adding terminal nodes on directized graph 
	randGraphDir=pruferTreeGraph.directizeGraph()
	#addGlobalTerminalNodes(randGraphDir)		#SUPER SOURCE SUPER SINK
	nodes=list(randGraphDir.nodes.keys())
	addLocalTerminalNodes(randGraphDir,nodes[0],nodes[-1])
	print("tickened prufer code tree with terminal nodes ")
	randGraphDir.build_incidentMatrix()
	gTreePruferExtended=drawGraphColored(randGraphDir)

	#PL min cut version
	#remove teminal nodes for pl script input
	trueNodes=deepcopy(randGraphDir.nodes)
	trueNodes.pop(SUPER_DEST_NODE_ID)
	trueNodes.pop(SUPER_SOURCE_NODE_ID)
	#minCutEdges=solveMinCut(list(randGraphDir.nodes.keys()),randGraphDir.extractEdges())
	
	minCutEdges=solveMinCut(trueNodes,randGraphDir.extractEdges())
	print(minCutEdges)
	#directize G
	#add fake super source,super sink
	#pass G nodes,edges to solve function to compute min cut
	return mod,minCutEdges

