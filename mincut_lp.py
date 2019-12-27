#!/usr/bin/env python2.7

#implemementation of solver for min cut problem over a generic undirected,connected graph using gurobi
from gurobipy import *
from graph_utils import *
import re

GRB_INFINITY=9 #TODO GUROBYPY SUPPERT ?
def solveMinCut(nodes,edges): 	
	
	#solve min cut problem over graph
	#graph has to be directed and with super source and super sink connected with all nodes with inifity cost edges TODO SET IDENTIFIERS FOR SPECIAL EDGES-SSOURCE-SSINK
	#returned sol: selected edges for the min cut ( subset of input ones)
	global mod		#TODO DEBUG
	mod=Model("minCut")
	#Variables
	zv=mod.addVars(nodes)	#TODO? EXCLUDED TERMINAL NODES 
	d_uv=mod.addVars(len(edges))
	edgesCostVector=list()			#costant vector for obj func
	#Constraints
	for e in range(len(edges)):
		edge=edges[e]
		#take edge metadata
		edgeSrcNodeID=edge[EDGE_TAIL_INDEX]
		edgeDstNodeID=edge[EDGE_HEAD_INDEX]
		edgeW=edge[EDGE_WEIGHT_INDEX]
		if edgeW == float("inf"): edgeW=GRB_INFINITY
		edgesCostVector.append(edgeW)
		if edgeSrcNodeID==SUPER_SOURCE_NODE_ID: 	#s,v edge
			mod.addConstr( d_uv[e] + zv[edgeSrcNodeID] >= 1 )
		elif edgeDstNodeID==SUPER_DEST_NODE_ID:	#u,t edge  
			mod.addConstr( d_uv[e] - zv[edgeDstNodeID] >= 0 )
		else:					#real edge
			mod.addConstr( d_uv[e] - zv[edgeSrcNodeID] + zv[edgeDstNodeID] >= 0 )

	#Constraints signs
	mod.addConstrs((d_uv[e] >= 0 for e in range(len(d_uv))),name="signEdges")
	#mod.AddConstraints(node[n]  #TODO SOTTOINTESO APPARTENENETE A R ?

	#Objective function
	mod.setObjective(( sum(d_uv[e]*edgesCostVector[e] for e in range(len(edges)))),GRB.MINIMIZE)
	#gurobi solve
	mod.write("minCutBeforeOptimize.lp")
	mod.optimize()
	mod.write("minCutAfterOptimize.lp")
	#printSolution(mod)
	selectedEdges=list()	#output soulution egdges 
	for edgeVarKey,edgeVarV in d_uv.items():
		if edgeVarV.X >0.0:		#selected edge from solution values of model decision var
			#extract decision var index (that match with the input edge's one) with a regex according standard naming scheme gurobi (as said in gurobi ref manual)
			edgeVarIndex=int(re.findall(".+\[(.*)\]",edgeVarV.VarName)[0]) 
			#TODO ALSO DIRECTLY WITH _colno ? gurobi ref manul not talk about indexing 
			selectedEdges.append(edges[edgeVarIndex])	#append selected edge by same indexing input edges <-> decision var

	return selectedEdges

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
	addTerminalNodes(randGraphDir)
	print("tickened prufer code tree with terminal nodes ")
	randGraphDir.build_incidentMatrix()
	gTreePruferExtended=drawGraphColored(randGraphDir)

	#PL min cut version
	minCutEdges=solveMinCut(list(randGraphDir.nodes.keys()),randGraphDir.extractEdges())
	print(minCutEdges)
	#directize G
	#add fake super source,super sink
	#pass G nodes,edges to solve function to compute min cut

