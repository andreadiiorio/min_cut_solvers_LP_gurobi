#!/usr/bin/env python3

#implemementation of solvers for min cut problem over a generic undirected,connected graph using gurobi,kargerD algo (and stoer_wagner wrapped from networkx)
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
	#solve min cut problem over a directed graph
	#returned sol: selected edges for the min cut ( subset of input ones)
	#model used: https://www3.diism.unisi.it/~agnetis/mincut.pdf
	
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
	

def minCutLPIterative(graph):
	"""search minimal cut with a LP script runned over a graph in witch has been selected a source and a dest 
	and undirected edges has been substituited with couple of directed edges
	iterativelly evaluate min cut relative to all possible unordered nodes pair n1,n2 
	return min cut as list of edges """

	if graph.directed==False:	#make sure the graph has been directized
		graph=graph.directizeGraph()

	nodes=list(graph.nodes.keys())
	minCut=graph.extractEdges()	#init min cut with worst solution, enhanced during the iterations
	
	n=0,len(nodes)
	for x in range(len(nodes)):			#all n(n-1)/2 non ordered couples
		for y in range(x+1,len(nodes)):
			n1=nodes[x]
			n2=nodes[y]

			##remove teminal nodes for pl script input -for trevisan lp model- 
			#nodesNoTerminal=copy(graph.nodes) #shallow copy enough, just ref.s modified
			#nodesNoTerminal.pop(n1)
			#nodesNoTerminal.pop(n2)
			minCutEdges=solveMinCutLP(graph.nodes,graph.extractEdges(),n1,n2)
			##print("New cut with src/dst node pair: ",(n1,n2),"\t:",minCutEdges)
			if len(minCut)>len(minCutEdges):	#either new min cut founded or first one
				minCut=minCutEdges
				##print("FOUNDED NEW MINCUT from src/dst: ",(n1,n2)," of size: ",len(minCut))
	return minCut

def minCutLPIterative2(graph):
	"""
	relaxed model of the above
	search minimal cut with a LP script runned over a graph in witch has been selected a source and a dest 
	and undirected edges has been substituited with couple of directed edges
	iterativelly evaluate min cut relative to all possible nodes pair s,t, where s is fixed and t!=s
	return min cut as list of edges
	"""

	if graph.directed==False:	#make sure the graph has been directized
		graph=graph.directizeGraph()

	nodes=list(graph.nodes.keys())
	minCut=graph.extractEdges()	#init min cut with worst solution, enhanced during the iterations
	
	n=0,len(nodes)
	for x in range(1,len(nodes)):			
			s=nodes[0]
			t=nodes[x]

			##remove teminal nodes for pl script input -for trevisan lp model- 
			#nodesNoTerminal=copy(graph.nodes) #shallow copy enough, just ref.s modified
			#nodesNoTerminal.pop(n1)
			#nodesNoTerminal.pop(n2)
			minCutEdges=solveMinCutLP(graph.nodes,graph.extractEdges(),s,t)
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

dbgC=0
def randMinCut(graph,iterations=1,OUTPUT_MODE_PARTITION=True):
	"""
	get min cut of a undirected graph by rand algo of KergerD.
	randomly contract edges in the graph getting a cut
	dynamically updated hashmap nodeK->degree to support quick uniform edge selection
	run this algo for  the given num of iteration, returning the best,minimal cost solution
	based on OUTPUT_MODE_PARTITION flag the output change 
	if OUTPUT_MODE_PARTITION is set : returned (nodePartitionCutDiscrimineted,cutValue)
	if OUTPUT_MODE_PARTITION isn't set : returned cut edgeList
	"""
	#global dbgC

	bestCutVal=float("inf")
	contractedEdges=list()
	#build nodesDegree for quick uniform rand edge pick
	nodesDegree,totDegrees=_computeNodesDegree(graph)
	for i in range(iterations):	#iterativelly run the random  algoritm keeping the best solution
		#print(str(bestCutVal)+" "+str(dbgC),end="\t")
		#dbgC+=1

		cutEdges=list()
		nodesDegreeCopy=deepcopy(nodesDegree)	#TODO ACTUALLY ENOUGH SHALLOW COPY
		totDegreesCopy=totDegrees
		graphContracted=deepcopy(graph)	#copy of src graph for contractions 
		for i in range (len(graph.nodes) -2 ): #n-2 edges contraction result in the graph with 2 residual nodes
			#PICK UNIFORMLY A RANDOM EDGE 
			###e=graphContracted.pickUniformRandomEdge()
			e=graphContracted.pickUniformRandomEdgeQuick(nodesDegreeCopy,totDegreesCopy)
			d=graphContracted.contractEdgeQuick(e)		#EDGE CONTRACT
			nodesDegreeCopy[contractEdgeMergeIDs(e[EDGE_TAIL_INDEX],e[EDGE_HEAD_INDEX])]=d
			d-=nodesDegreeCopy.pop(e[EDGE_TAIL_INDEX])
			d-=nodesDegreeCopy.pop(e[EDGE_HEAD_INDEX])

			totDegreesCopy+=d
		
		#here only 2 node remained
		#nodesParti1,2 will hold a lists of nodes that constitute the graph partition
		residualNodes=list(graphContracted.nodes.keys())
		nodeParti0=residualNodes[0]
		nodeParti1=residualNodes[1]
		#if one side of partition is a single node substitute with a list of itself
		if type(residualNodes[0])==int: nodeParti0=[residualNodes[0]]
		if type(residualNodes[1])==int: nodeParti1=[residualNodes[1]]
		
		#exit here if requested just partition identified by the founded cut
		
		cutVal=len(graphContracted.nodes[residualNodes[0]])
		newCut=(nodeParti0,cutVal)
		if OUTPUT_MODE_PARTITION == False:	#compute cut edges and ovveride outCut thanks to python polymorifsm
			for nodeID1 in nodeParti0:
				for nodeID2 in graph.nodes[nodeID1]:
					#select only edges cross partition from the source graph
					if nodeID2 in nodeParti1: cutEdges.append((nodeID1,nodeID2,1))
			cutVal=len(cutEdges)
			newCut=cutEdges		
		#update current optimal solution
		if cutVal <= bestCutVal:
			bestCutVal=cutVal
			outCut=newCut
			#print(cutVal,end="\t")
			##print("@randMinCut founded newMinCut: ",bestMinCut," at iteration: ",i)
	return outCut	



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
	#main()
	nNodes=66
	randomIterForPerr0_37=nNodes*nNodes*.5
	pruferTreeGraph = pruferCodeGenTree(nNodes, False)
	graphTickennerRand(pruferTreeGraph, 162)
	
	g= getNetworkxGraph(pruferTreeGraph)
	minCutStoerWagnerSize,nodesParti=stoer_wagner(g)
	for x in range(33):
		i=0
		cutVal=float("inf")
		while(cutVal != minCutStoerWagnerSize):
			cut=randMinCut(pruferTreeGraph,1,False)
			cutVal=len(cut)
			i+=1
		print("@",i,"\tvs\titer needed s.t. Perr =  .37 ",randomIterForPerr0_37)
		if i >= randomIterForPerr0_37:
			print("@@!!!!")
	print("minCut = ",minCutStoerWagnerSize," a node parti: ",nodesParti)
	print(pruferTreeGraph)
	
	try:drawGraphMinCut(pruferTreeGraph,cut,blockingShow=True)		#SET ENVIRON VARIABLE 
	except: print("set env variable: export GUI_GRAPH=True")
