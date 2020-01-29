#!/usr/bin/env python3

#implemementation of solver for min cut problem over a generic undirected,connected graph using gurobi
from gurobipy import *
from graph_utils import *
from re import findall
from copy import deepcopy,copy
from timeit import default_timer as timer	#TODO UPDATE NEW PYTHON3 TIME LIB

global mod		#TODO DEBUG

def _getEdgeFromGurobyVarName(gurobiVarName):
	#extract edge in form [HEAD,TAIL,COST] from gurobi model edge var
	#var name should be like 'edge[HEAD,TAIL,COST] -> parse with regex
	edgeFieldsStr=findall(".*\[([0-9]+,[0-9]+,[0-9]+)\].*",gurobiVarName)[0].split(",")
	edge=(int(edgeFieldsStr[0]),int(edgeFieldsStr[1]),int(edgeFieldsStr[2]))
	return edge

def solveMinCutLP(nodes,edges,s,t):
	##global mod		#TODO DEBUG
	
	#solve min cut problem over graph
	#returned sol: selected edges for the min cut ( subset of input ones)
	
	mod=Model("minCut")
	mod.setParam(GRB.Param.OutputFlag,0)	#SUPPRESS PART OF DEFAULT GUROBI OUTPU
	#Variables
	zv=mod.addVars(nodes,name="z_node")
	edges.sort()
	d_uv=mod.addVars(edges,name="edge")
	#Constraints
	for e in edges:
		#take edge metadata
		edgeSrcNodeID=e[EDGE_TAIL_INDEX]
		edgeDstNodeID=e[EDGE_HEAD_INDEX]
		if edgeSrcNodeID==t or edgeDstNodeID==s:	#Discard edges exiting the tail or entering the source
			continue
		mod.addConstr( zv[edgeSrcNodeID] - zv[edgeDstNodeID] + d_uv[e]   >= 0 )
	mod.addConstr(zv[t]-zv[s] == 1)
	#TODO FIXABLE zv[s]=0
	#zv[s].UB=0
	#zv[s].LB=0
	#Constraints signs
	mod.addConstrs((d_uv[e] >= 0  for e in edges),name="sign_edge")
	mod.addConstrs((zv[v] >= -GRB.INFINITY  for v in nodes),name="sign_node")

	#Objective function
	mod.setObjective(( sum(d_uv[e] * e[EDGE_WEIGHT_INDEX] for e in edges)),GRB.MINIMIZE)

	#gurobi solve
	#mod.write("minCutBeforeOptimize.lp")
	mod.optimize()
	#mod.write("minCutAfterOptimize.lp")
	#printSolution(mod)
	selectedEdges=list()	#output soulution egdges 
	edgeIndex=0
	for edgeVarKey,edgeVarV in d_uv.items():
		if edgeVarV.X >0.0:		#selected edge from solution values of model decision var
			#extract decision var index (that match with the input edge's one) with a regex according standard naming scheme gurobi (as said in gurobi ref manual)
			edgeRegexName=_getEdgeFromGurobyVarName(edgeVarV.varName)
			edgeIndexRetrieved=edges[edgeIndex]	#FAST INDEX GET NOT SUPPORTED BY GUROBY TODO SEEM TO WORK
			if edgeIndexRetrieved != edgeRegexName: raise Exception("GUROBI INDEXING EDGE VARs DIFFERENT FROM SRC ONE!",mod.getVars(),"\n",edgeIndex,"\t:\t",edgeIndexRetrieved,edgeRegexName) #TODO DEBUG
			selectedEdges.append(edgeIndexRetrieved)

		edgeIndex+=1
	
	#_dumpAllVarsSolution(mod,True)														#TODO DEBUG
	return selectedEdges

def solveMinCutLP_trevisan(nodesNoTerminal,edges,s,t):
	##global mod		#TODO DEBUG
	
	#solve min cut problem over graph
	#returned sol: selected edges for the min cut ( subset of input ones)
	
	mod=Model("minCut")
	#Variables
	zv=mod.addVars(nodesNoTerminal,name="z_node")	
	d_uv=mod.addVars(edges,name="edge")
	#Constraints
	for e in edges:
		#take edge metadata
		edgeSrcNodeID=e[EDGE_TAIL_INDEX]
		edgeDstNodeID=e[EDGE_HEAD_INDEX]
		terminalEdge=False
		print(e,s,t)
		#constraints for each edges

		#if edgeSrcNodeID==s and edgeDstNodeID==t: 			#s,t edge
		#	d_uv[e].UB=1
		#	d_uv[e].LB=1
		if edgeSrcNodeID==s: 			#s,v edge
			mod.addConstr( d_uv[e] + zv[edgeDstNodeID] >= 1 )
			terminalEdge=True
		if edgeDstNodeID==t:				#u,t edge  
			mod.addConstr( d_uv[e] - zv[edgeSrcNodeID] >= 0 )
			terminalEdge=True
		if edgeSrcNodeID==t or edgeDstNodeID==s:	#Discard edges exiting the tail or entering the source
			continue
		if terminalEdge==False:	#specific constraint for generic edge u,v
			mod.addConstr( d_uv[e] - zv[edgeSrcNodeID] + zv[edgeDstNodeID] >= 0 )

	#Constraints signs
	mod.addConstrs((d_uv[e] >= 0  for e in edges),name="sign_edge")
	mod.addConstrs((zv[v] >= -GRB.INFINITY  for v in nodesNoTerminal),name="sign_node")
	#mod.AddConstraints(node[n]  #TODO SOTTOINTESO APPARTENENETE A R ?

	#Objective function
	mod.setObjective(( sum(d_uv[e] * e[EDGE_WEIGHT_INDEX] for e in edges)),GRB.MINIMIZE)

	#gurobi solve
	#mod.write("minCutBeforeOptimize.lp")
	mod.optimize()
	#mod.write("minCutAfterOptimize.lp")
	#printSolution(mod)
	selectedEdges=list()	#output soulution edges 
	for edgeVarKey,edgeVarV in d_uv.items():
		if edgeVarV.X >0.0:		#selected edge from solution values of model decision var
			#extract decision var index (that match with the input edge's one) with a regex according standard naming scheme gurobi (as said in gurobi ref manual)
			#TODO ALSO DIRECTLY WITH _colno ? gurobi ref manul not talk about indexing 
			selectedEdges.append(_getEdgeFromGurobyVarName(edgeVarV.varName))
	
	_dumpAllVarsSolution(mod,True)

	return selectedEdges


def _dumpAllVarsSolution(model,dumpJustSelected=False):
	vars=model.getVars()
	for v in vars:
		if dumpJustSelected and v.X <=0.0:
			continue
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


def minCutLPIterative(graph):
	#search minimal cut with a LP script runned over a graph in witch has been selected a source and a dest 
	#and undirected edges has been substituited with couple of directed edges
	#iterativelly evaluate min cut relative to all possible nodes pair n1,n2 s.t. n1!=n2 in graph nodes
	#return min cut as list of edges 

	if graph.directed==False:	#make sure the graph has been directized
		graph=graph.directizeGraph()

	nodes=list(graph.nodes.keys())
	minCut=graph.extractEdges()	#init min cut with worst solution, enhanced during the iterations
	
	#TODO ALL ORDERED COUPLES
	#for n1 in nodes:
	#	for n2 in nodes:
	#		if n1 != n2:
	n=0,len(nodes)
	for x in range(len(nodes)):			#all n(n-1)/2 non ordered couples
		for y in range(x+1,len(nodes)):
			n1=nodes[x]
			n2=nodes[y]

			#remove teminal nodes for pl script input  
			#nodesNoTerminal=copy(graph.nodes) #shallow copy enough, just ref.s modified
			#nodesNoTerminal.pop(n1)
			#nodesNoTerminal.pop(n2)
			minCutEdges=solveMinCutLP(graph.nodes,graph.extractEdges(),n1,n2)
			##print("New cut with src/dst node pair: ",(n1,n2),"\t:",minCutEdges)
			if len(minCut)>len(minCutEdges):	#either new min cut founded or first one
				minCut=minCutEdges
				##print("FOUNDED NEW MINCUT from src/dst: ",(n1,n2)," of size: ",len(minCut))
	return minCut
					

#import networkx as nx
#from networknx import stoer_wagner,Graph,DiGraph

def stoer_wagner_minCut(graph):
	#get mincut with stoer_wagner algo by netowrkx lib (used for graph draw)
	#return founded min cut size
	g= getNetworkxGraph(graph)
	cutVal,nodesParti=stoer_wagner(g)
	##print("cutVal: ",cutVal,"nodesPartitioining ",nodesParti)
	return cutVal

def _computeNodesDegree(graph):
	#return nodes degree dict, tot degree of all nodes in graph
	nodesDegree=dict()
	totDegrees=0
	for nodeID,neighboors in graph.nodes.items():
		nodesDegree[nodeID]=len(neighboors)
		totDegrees+=len(neighboors)
	return nodesDegree,totDegrees

def randMinCut(graph,iterations=1):
	#get min cut of a undirected graph by rand algo
	#randomly contract edges in the graph getting a cut
	#run this algo for  the given num of iteration, returning the best,minimal cost solution
	#return edge list of the best founded min cut
	
	##print("RAND MIN CUT OVER:\t", graph)

	bestMinCut=graph.extractEdges()	#start with max cut possible and enhance the solution during iterations
	contractedEdges=list()
	#build nodesDegree for quick uniform rand edge pick
	nodesDegree,totDegrees=_computeNodesDegree(graph)

	for i in range(iterations):	#iterativelly run the random  algoritm keeping the best solution
		cutEdges=list()
		nodesDegreeCopy=deepcopy(nodesDegree)	#TODO ACTUALLY ENOUGH SHALLOW COPY
		totDegreesCopy=totDegrees
		graphContracted=deepcopy(graph)	#copy of src graph for contractions 
		for i in range (len(graph.nodes) -2 ): #n-2 edges contraction result in the graph with 2 residual nodes
			#PICK UNIFORMLY A RANDOM EDGE 
			#e=graphContracted.pickRandEdge()
			e=graphContracted.pickUniformRandomEdgeQuick(nodesDegreeCopy,totDegreesCopy)
			d=graphContracted.contractEdge(e)		#EDGE CONTRACT
			nodesDegreeCopy[str(e[EDGE_TAIL_INDEX])+CONTRACT_CHR_SEP+str(e[EDGE_HEAD_INDEX])]=d
			#update degreas dict
			d-=nodesDegreeCopy.pop(e[EDGE_TAIL_INDEX])
			d-=nodesDegreeCopy.pop(e[EDGE_HEAD_INDEX])
			totDegreesCopy+=d #update tot degree with degree of new contracted node - degree of parent nodes
		
		#here only 2 node remained
		#Extract graph cut node partition 
		##print("resoulting contracted graph: ",graphContracted)
		node=list(graphContracted.nodes.keys())[0]	#get 1 of remaining node after contractions
		if type(node)==type(0):		#node hasn't been contrated in this iteration
			nodesDeContracted=[node]
		else: 				
			nodesDeContracted=node.split(CONTRACT_CHR_SEP) #str list of nodes contracted 
		#extract cut edges
		for n in nodesDeContracted:
			nodeID=int(n)
			nOldNeighs=graph.nodes[nodeID]
			for nodeID2 in nOldNeighs:
				cutEdges.append((nodeID,nodeID2,1))
		if len(cutEdges)< len(bestMinCut):
			bestMinCut=cutEdges
			##print("@randMinCut founded newMinCut: ",bestMinCut," at iteration: ",i)
	return bestMinCut



def main():				#TODO DEBUG SWITCH
	global randGraphDir,pruferTreeGraph

	#Generate Tree from a random prufer code arr, then ticken the tree randomly 
	TREE_SIZE=6
	pruferTreeGraph=pruferCodeGenTree(TREE_SIZE,True)
	newNodes,newEdges=graphTickennerRand(pruferTreeGraph,2)
	
	randGraphDir=pruferTreeGraph.directizeGraph()	#make the graph direct
	randGraphDir.build_incidentMatrix()
	g=drawGraph(randGraphDir)
	
	##stoer_wagner_minCut with networkx lib
	start=timer()
	minCutStoerWagnerSize=stoer_wagner_minCut(pruferTreeGraph)
	end=timer()
	minCutStoerWagnerTime=end-start
	print("@min cut stoerWagner value:  ",minCutStoerWagnerSize," duration: ",minCutStoerWagnerTime)

	#LP ITERATIVE VERSION
	start=timer()
	minCutIterative=minCutLPIterative(randGraphDir)
	end=timer()
	minCutIterativeTime=end-start
	print("@min cut PL iterative:  ",minCutIterative," duration: ",minCutIterativeTime)


	#rand cut over graph
	start=timer()
	randMinCutSol=randMinCut(pruferTreeGraph,5)
	end=timer()
	randMinCutTime=end-start
	print("@min cut randomized algo:  ",randMinCutSol," duration: ",randMinCutTime)
	
	#TODO MATCHING RESULT AND DEBUG
	print("@@MINCUT VALUES:  iterativePL=",len(minCutIterative),"  randomized algo=",len(randMinCutSol),"  stoerWagner=",minCutStoerWagnerSize)
	print("@@MINCUT TIMES:  iterativePL=",minCutIterativeTime,"  randomized algo=",randMinCutTime,"  stoerWagner=",minCutStoerWagnerTime)
	print("@@MINCUT TIME DELTAS:  iterativePL-rand=",abs(minCutIterativeTime-randMinCutTime)," stoerWagner-rand=",abs(randMinCutTime-minCutStoerWagnerTime),"  iterative-stoerWagner=",abs(minCutIterativeTime-minCutStoerWagnerTime))



if __name__=="__main__":
	main()
	#input()
