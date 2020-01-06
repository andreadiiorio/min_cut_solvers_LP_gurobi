#!/usr/bin/env python2.7
#utils classes and functions used by the min cut problem solver
#basic graph rappresentation by Adjacency Lists and python built-in data types
#some utils function to well support mincut solvers 

import copy
from random import choice,seed,uniform


#Edges rappresentation via tuple (naming reflect this: edge e: 1->2; 1 is the tail of the edge
EDGE_TAIL_INDEX=0	#edge tail index in edge tuple
EDGE_HEAD_INDEX=1	#edge head index in edge tuple
EDGE_WEIGHT_INDEX=2	#edge weight index
DEFAULT_EDGE_WEIGHT=1
#special ID for terminal nodes
SUPER_SOURCE_NODE_ID=-2
SUPER_DEST_NODE_ID=-1
CONTRACT_CHR_SEP="_"
#INF=float("inf")	#PYTHON INF -> NOT SUPPORTED BY GUROBI
INF=999999
#from gurobipy import GRB
#INF=GRB.INFINITY	#NEEDED GUROBYPY IMPORTED
class Graph:
	def __init__(self,**argsDict):
	#non default init of graph by calling the constructor with kwargs named in same way of graph class attributes
	#it's assumed here but in the whole module consistency in the passed parameters, like edge correspond to nodes
		self.directed=False
		self.nodes=dict()	#adjacency list rappresentation of graph nodeID->list of nodesID reachable 
		#non default initialization
		if argsDict.get("directed")!=None:
			self.nodes=argsDict["directed"]
		if argsDict.get("nodes")!=None:
			self.addNodes(argsDict["nodes"])	#flexible nodes adding with a partial robstuness type check
		if argsDict.get("edges")!=None:
			self.addEdges(argsDict["edges"])
	
	def addNodes(self,nodesNew):
		#add new nodes as dict of nodesID -> nodesID reachable from this node
		#supported with type check also list of nodesID initialized with empty adjacent list 
		if type(nodesNew)==type(dict()):
			self.nodes.update(nodesNew)
		elif type(nodesNew)==type(list()): #otherwise add empty nodes (un connected) from passed list nodesNew
			for n in nodesNew:
				self.nodes[n]=list() #add nodes as unconnected (empty list of neighbors)
		else:
			raise Exception("invild type for newly added nodes")

	def addEdges(self,edgesNew):
		#edge to add to graph are rappresented by a list of tuples of newly (ordinatlly) connected nodes, e.g. [(1,2),(4,1)
		#edges added in adj lists of interested nodes 

		# print(self.nodes)
		# print("adding edges:",edgesNew)
		#update adj list in place
		for e in edgesNew:
			#eNodeTail=e[EDGE_TAIL_INDEX]
			#eNodeHead=e[EDGE_HEAD_INDEX]
			self.nodes[e[EDGE_TAIL_INDEX]].append(e[EDGE_HEAD_INDEX])
			if not self.directed:	#update adj list for un directed graphs
				self.nodes[e[EDGE_HEAD_INDEX]].append(e[EDGE_TAIL_INDEX])
		# print(self.nodes)
	
	def remEdges(self,edgesToRemove):
		#edgesToRemove is a list of tuple of edges to remove
		for edge in edgesToRemove:
			srcNodeID=edge[EDGE_TAIL_INDEX]
			dstNodeID=edge[EDGE_HEAD_INDEX]
			#update src node adj list
			#self.nodes[srcNodeID].remove(dstNodeID) #TODO SINGLE LINE UPDATE
			srcNodeAdjList=self.nodes[srcNodeID]
			srcNodeAdjList.remove(dstNodeID)
			self.nodes[srcNodeID]=srcNodeAdjList	#updated adj list of src Node
			#update adj list of dst node for un directed graph
			if self.directed==True:			
				dstNodeAdjList=self.nodes[dstNodeID]
				dstNodeAdjList.remove(srcNodeID)
				self.nodes[dstNodeID]=dstNodeAdjList	#updated adj list of dst Node

	def pickRandEdge(self):
		#return a uniformly picked random edge
		return choice(self.extractEdges())	#TODO FASTER!!!!!!!!

	def contractEdge(self,e):
		#for each edge in edgesToContract:  contract edge removing the edge and merge Heat and Tail nodes in a new node
		#old tail and head node with ID X,Y will be deletted and new node with ID like 'X_Y' will be added as a new node
		#return number of new contracted node's neighboors
		eTail=e[EDGE_TAIL_INDEX]
		eHead=e[EDGE_HEAD_INDEX]
		newNodeID=str(eTail)+CONTRACT_CHR_SEP+str(eHead)
		print("contracting\t",eTail," ",eHead," -> ",newNodeID)
		#remove old contracted nodes
		eTailNeigh=self.nodes.pop(eTail,list())
		eHeadNeigh=self.nodes.pop(eHead,list())
		
		#merge contracted nodes adj lists 		#TODO FASTER WITH DICT BUILD ??
		for neigh2 in eHeadNeigh:
			if neigh2 not in eTailNeigh:
				eTailNeigh.append(neigh2)
		#RESTRUCT OTHER NODE ADJ LIST WITH THE NEW NODE
		alreadyRenamed=False
		for node,neighboors in self.nodes.items():
			if eTail in neighboors:
				oldContractedNodeIndx=neighboors.index(eTail)
				self.nodes[node][oldContractedNodeIndx]=newNodeID #IN PLACE ADJ LIST MODIFY TOWRARDS NEW CONTRACTED NODE
				alreadyRenamed=True
			if eHead in neighboors:
				oldContractedNodeIndx=neighboors.index(eHead)
				if not alreadyRenamed: 
					self.nodes[node][oldContractedNodeIndx]=newNodeID #IN PLACE ADJ LIST MODIFY TOWRARDS NEW CONTRACTED NODE
				else:	#avoid incosistence in adj list -> if already renamed old tail Node -> new Node ==> head has to be removed from adj List
					self.nodes[node].pop(oldContractedNodeIndx)
		#finally insert the contracted node
		eTailNeigh.remove(eTail)
		eTailNeigh.remove(eHead)
		self.nodes[newNodeID]=eTailNeigh		
		#debug
		print(self.nodes)
		return len(eTailNeigh)
	
	def _delNodes(self,nodesIDs):
		#remove a list of nodesIDs from graph
		edgesToRemove=list()
		for n in nodesIDs:
			nodeAdjList=self.nodes[n]
			for reachableNode in nodeAdjList:
				edgesToRemove.append((n,reachableNode))
		if not self.directed:
			for node,adjNodes in self.nodes.items():
				for node2 in adjNodes:
					if node2 in nodesIDs:
						edgesToRemove.append((node2,node)) #backward edge to remove
		self.remEdges(edgesToRemove)

	def extractEdges(self):
		#extract edges from graph in form of list of tuples
		#like (TAIL,HEAD,WEIGHT)
		edges = list()
		for n, neigh in self.nodes.items():
			for n1 in neigh:
				if n==SUPER_SOURCE_NODE_ID or n1==SUPER_DEST_NODE_ID:
					edge=(n, n1, INF)
				else:
					edge=(n, n1, DEFAULT_EDGE_WEIGHT)
				edges.append(edge)
		return edges

	def build_incidentMatrix(self,printFlag=True):
		EDGE_EXIT_NODE=1
		EDGE_ENTER_NODE=-1
		ss_row_index=-2
		sd_row_index=-1
		#build edges list on the fly
		edges=self.extractEdges()
		#0 init matrix shallow copy fully avoiding
		incidentMatrix=list()
		for i in range(len(self.nodes)):
			incidentMatrix.append(list())
			for j in range(len(edges)):
				incidentMatrix[i].append(0)

		edges.sort()		#TODO EASIER TO READ
		for edgeID in range(len(edges)):
			edgeTuple=edges[edgeID]
			edgeSrc=edgeTuple[EDGE_TAIL_INDEX]
			edgeDst=edgeTuple[EDGE_HEAD_INDEX]
			#handle super source and super dest nodes in incident matrix
			if edgeSrc == SUPER_SOURCE_NODE_ID:
				edgeSrc=ss_row_index
			if edgeDst == SUPER_DEST_NODE_ID:
				edgeDst=sd_row_index

			incidentMatrix[edgeSrc][edgeID]=EDGE_EXIT_NODE
			incidentMatrix[edgeDst][edgeID]=EDGE_ENTER_NODE
			if self.directed==False:			#handle non orienthed graph
				incidentMatrix[edgeDst][edgeID]=EDGE_EXIT_NODE

		if(printFlag):		#print incident matrix infos
			print("---nodes---")
			print(self.nodes)
			print("---edges---")
			print(edges)
			print("edges IDs  ", list(range(len(edges))))
			for r in incidentMatrix:
				print(r)
			print("\n\n")
		return incidentMatrix
				

	def directizeGraph(self):
		#return a new copy of the current undirect graph as direct
		#because adj list are already doble naigable for each edge in un directed graph, this op will just return a deep copy of curr graph with directed flag setted

		if self.directed:
			raise Exception("already direct graph")
		directedGraph=copy.deepcopy(self)
		directedGraph.directed=True
		#edgesToAdd=list()
		#  #create reverse edges with same cost to add to undirect graph
		# for edge in directedGraph.EDGEEE:
		# 	newEdge=(edge[EDGE_HEAD_INDEX],edge[EDGE_TAIL_INDEX],edge[EDGE_WEIGHT_INDEX])
		# 	if newEdge not in directedGraph.EDGEEE: #undirect graph already have double directed edges
		# 		edgesToAdd.append(newEdge)
		#
		# directedGraph.addEdges(edgesToAdd)
		return directedGraph
	
	def __str__(self):
		return str(self.nodes)

def uniformRandomEdgeAdjList(nodesAdjList,nodesDegree):
	#pick uniformiformly random edge from graph adjacent list
	# nodesAdjList nodes field of graph: nodeID -> neighboorsNodeIDList
	# nodesDegree  dict nodeID -> degree, with special item "TOT"-> sum of all nodes degreea
	#first pick node in adj list basing of nodes degree
	#node with high degree will be more likelly chosen

	#random weighted edge tail selection
	#for each node in adj list will be allocated a range [a,b) and a uniform number picked n will discriminate the node s.t. n in node range
	#will be returned edge in classic defined form ignoring if node is SSRC or SDST
	rndEdgeTail=rndEdgeHead=None
	RANGE_START=0
	RANGE_END=100
	range_len=RANGE_END-RANGE_START
	nodeStartRange=RANGE_START	#will hold actual node range start
	randomUniformPick=uniform(RANGE_START,RANGE_END)

	nodesPickRanges=list()	#list of [(rangeStart,rangeEnd,nodeID),...] where rangeEnd is NotIncluded in nodeID pick range
	totDegree=float(nodesDegree["TOT"])
	# alloc for each node range for random weighted pick in a list
	for nodeID,degree in nodesDegree.items():
		nodeRangeLen=(degree/totDegree)*range_len
		#alloc for node range (nodeStartRange,nodeStartRange+nodeRangeLen)
		nodesPickRanges.append((nodeStartRange,nodeStartRange+nodeRangeLen,nodeID))
		nodeStartRange+=nodeRangeLen
	
	# detect witch node is discriminated by randomUniformPick checking nodes pick ranges
	for n in nodesPickRanges:
		if n[0] <= randomUniformPick and randomUniformPick < n[1]:	#founded edge tail node
			rndEdgeTail=n[2]
			break
	#now pick edge head simply with uniform choice among rndEdgeTail adj list
	rndEdgeHead=choice(nodesAdjList[rndEdgeTail])
	return (rndEdgeTail,rndEdgeHead,1)


def addLocalTerminalNodes(graph,src,dst):
	#add terminal nodes to a specific nodes in the directed graph
	#attach a source to node src and a dest to dst

	terminalNodesToAdd=[SUPER_SOURCE_NODE_ID,SUPER_DEST_NODE_ID]
	edgesToAdd=list()
	edgesToAdd.append((SUPER_SOURCE_NODE_ID,src,INF)) #fake edge between fake super source and other nodes
	edgesToAdd.append((dst,SUPER_DEST_NODE_ID,INF)) #fake edge between fake super source and other nodes
	
	graph.addNodes(terminalNodesToAdd)
	graph.addEdges(edgesToAdd)
	

def addGlobalTerminalNodes(graph):
	#add terminal nodes to a directed graph, a super source and a source sink (S*,T*)
	#these special nodes will be connected with every other nodes in the graph with an edge s,v or u,t of inifinity cost (python float('inf'))
	#also defined special 
	terminalNodesToAdd=[SUPER_SOURCE_NODE_ID,SUPER_DEST_NODE_ID]
	edgesToAdd=list()
	for nodeID in graph.nodes:
		newEdge_sv=(SUPER_SOURCE_NODE_ID,nodeID,INF) #fake edge between fake super source and other nodes
		newEdge_ut=(nodeID,SUPER_DEST_NODE_ID,INF) #fake edge between fake super source and other nodes
		edgesToAdd.append(newEdge_sv)
		edgesToAdd.append(newEdge_ut)
	graph.addNodes(terminalNodesToAdd)
	graph.addEdges(edgesToAdd)
	



def genTreePath(nodesN):
	#generate a random tree with nodesN nodes as a random path among nodes
	#return tuple (nodeIDs,edges list)
	treeNodesIDs=list(range(nodesN))
	treeEdges=list()
	nodesDeepCopy=copy.deepcopy(treeNodesIDs)
	node=choice(nodesDeepCopy)	#select random root among nodes IDs
	nodesDeepCopy.remove(node)

	for x in range(TREE_SIZE-1):
		nextNode=choice(nodesDeepCopy)
		nodesDeepCopy.remove(nextNode)

		edge=(node,nextNode,DEFAULT_EDGE_WEIGHT)
		treeEdges.append(edge)
		node=nextNode
	return (treeNodesIDs,treeEdges)

def pruferCodeGenTreeEdges(pruferCodeArr):
	#from a prufer code in pruferCodeArr generate a list of edges rappresenting a tree returned
	#basic implementation taken from wikipedia
	#robstuness check on validity of prufer code passed
	if type(pruferCodeArr)!=type(list()) or  any([i > len(pruferCodeArr) for i in pruferCodeArr]):
		raise Exception("invalid prufer code")
	treeEdges=list()
	nodes=list(range(len(pruferCodeArr)+2))
	degrees=[1]*len(nodes)
	for f in pruferCodeArr:
		degrees[f]+=1
	for nodeF in pruferCodeArr:
		for node in nodes:
			if degrees[node] == 1:
				treeEdges.append((nodeF,node,DEFAULT_EDGE_WEIGHT))
				degrees[nodeF]-=1
				degrees[node]-=1
				break
			#else:	#debug
			#	print(degrees,node)
	#last edge to add u->v
	u,v=0,0
	for node in nodes:
		if degrees[node]==1:
			if u==0:
				u=node
			else:
				v=node
				break
	treeEdges.append((u,v,DEFAULT_EDGE_WEIGHT))
	degrees[u]-=1
	degrees[v]-=1
	return treeEdges

def pruferCodeGenTree(treeSize=1,logPrint=False):
	#generate a random prufer code array and corresponding tree 
	#return graph generated

	newNodesArrIDs=list(range(treeSize-2))	#support array
	newNodes=list(range(treeSize))		#new nodes for the random prufer code tree
	pruferCodeArr=list()			#actual prufer code array
	#build prufer code arr TODO CONSTRAINT FOR BETTER QUALITY ?
	for n in range(len(newNodesArrIDs)):
		nid=choice(newNodesArrIDs)
		pruferCodeArr.append(nid)
		newNodesArrIDs.remove(nid)

	newEdges=pruferCodeGenTreeEdges(pruferCodeArr)
	pruferTreeGraph=Graph(nodes=newNodes,edges=newEdges)
	if logPrint:
		print("prufer code from random array: ",pruferCodeArr,"resulting edges")
		print(newEdges)
		pruferTreeGraph.build_incidentMatrix()
	return pruferTreeGraph

def graphTickennerRand(graph,nodesN,edgesN,MAX_TRIES_NUM=20):
	#make the input graph "tickenner" by adding nodesN and edgesN randomly
	#return tuple of ( newly added nodes num, newly added edges num )

	#Adding nodes
	firstNewNodeID=1+max(list(graph.nodes.keys()))
	newNodesIDs=list(range(firstNewNodeID,firstNewNodeID+nodesN))
	graph.addNodes(newNodesIDs)

	#adding edges
	#for a limited num of times, try select a pair of nodes and add edge if not already exist
	newEdgesToAdd=list()
	nodesIDs=list(graph.nodes.keys())
	triesLeft=MAX_TRIES_NUM
	while triesLeft >= 0 and edgesN>=0:
		edgeTailNode=choice(nodesIDs)
		edgeHeadNode=choice(nodesIDs)
		newPossibleEdge=(edgeTailNode,edgeHeadNode,DEFAULT_EDGE_WEIGHT)
		#eventually new possible edge may not be added to the graph
		edgeAlreadyIn=edgeHeadNode in graph.nodes[edgeTailNode] or edgeTailNode==edgeHeadNode or newPossibleEdge in newEdgesToAdd
		if edgeAlreadyIn:
			triesLeft-=1
			continue

		graph.addEdges([(edgeTailNode,edgeHeadNode,DEFAULT_EDGE_WEIGHT)])	#single insert

	#batch insert
	#newEdgesToAdd.append((edgeTailNode,edgeHeadNode,DEFAULT_EDGE_WEIGHT))
	#graph.addEdges(newEdgesToAdd)
	print("Added ",len(newNodesIDs)," nodes and ",len(newEdgesToAdd)," edges to the graph")
	print(graph.nodes)
	return (len(newNodesIDs),len(newEdgesToAdd))
		

#####	GRAPH WRITE VIEW LOGIC ON GUI OF NETWORKX
import matplotlib.pyplot as plt
import networkx as nx
from time import sleep
drawn=0
def getNetworkxGraph(graph):
	g=nx.Graph()	
	if graph.directed:	#overwrite  g for direct graphs
		g=nx.DiGraph()
	g.add_nodes_from(list(graph.nodes.keys()))
	edgesHeadTailList=list()
	edgesWeightList=list()		#same indexing edgesHeadTailList abve
	edges=graph.extractEdges()
	for e in edges:
		edgesHeadTailList.append(e[:-1]) #exclude nested weight field
		edgesWeightList.append(e[-1])
	g.add_edges_from(edgesHeadTailList)
	return g

def drawGraph(graph):
	global drawn
	#try draw graph by nxgraph python lib
	#return nx.Graph obj 
	g=getNetworkxGraph(graph)
	plt.subplot()
	nx.draw(g,with_labels=True)
	drawn += 1
	print("drawn", drawn)
	plt.show(block=False)

	return g

# g.add_edge(e[EDGE_TAIL_INDEX],e[EDGE_HEAD_INDEX],color=colo,weight=e[EDGE_WEIGHT_INDEX])

def drawGraphColored(graph):

	#try draw graph by nxgraph python lib
	#graph drawn with colors
	#return nx.Graph obj
	global drawn

	g=nx.Graph()
	if graph.directed:	#overwrite  g for direct graphs
		g=nx.DiGraph()
	nodesIDSorted=list(graph.nodes.keys())
	nodesIDSorted.sort()
	g.add_nodes_from(nodesIDSorted)
	edgesHeadTailList=list()
	fakeEdges=list()
	edgesWeightList=list()		#same indexing edgesHeadTailList abve
	edges = graph.extractEdges()
	for e in edges:
		edgesHeadTailList.append(e[:-1])  # exclude nested weight field
		edgesWeightList.append(e[-1])
		if e[EDGE_WEIGHT_INDEX]==INF:
			fakeEdges.append(e)

	g.add_edges_from(edgesHeadTailList)

	plt.subplot()			#like a base canva
	nodesPositions = nx.spring_layout(g)  # positions for all nodes
	# nodesPositions = nx.shell_layout(g)  # positions for all nodes
	firstTrueNodeIndex=nodesIDSorted.index(SUPER_SOURCE_NODE_ID)+2
	# nx.draw_networkx_nodes(g,nodesPositions,nodesIDSorted[firstTrueNodeIndex:],node_color="g")
	# nx.draw_networkx_nodes(g,nodesPositions,nodesIDSorted[:firstTrueNodeIndex],node_color="b")
	# nx.draw_networkx_edges(g,nodesPositions,edgesHeadTailList,edge_color="b")

	#MOST STRAIGHTFORWARD DRAWING APPROCH: start basic "dflt" draw, then re-draw different colors stuff (e.g. fake edges)
	nx.draw_networkx(g,nodesPositions)
	nx.draw_networkx_edges(g,nodesPositions,fakeEdges,edge_color="b")
	drawn += 1
	print("drawn", drawn)
	plt.show()
	return g

if __name__=="__main__":  	#TODO debug switch  see below
#def main():			#TODO NEEDED PYTHON SHELL TEST TMP
	global TREE_SIZE,gTreePruferExtended,gPathExtended
	seed()
	TREE_SIZE=4
	
	###	Build Rand Graph from a random Path tickened randomly 
	treeNodes,treeEdges=genTreePath(TREE_SIZE)
	treePath=Graph(nodes=treeNodes,edges=treeEdges)
	print("treePath simple")
	treePath.build_incidentMatrix()
	newNodes,newEdges=graphTickennerRand(treePath,0,1)
	#print("newNodes",newNodes,"newEdges",newEdges)
	print("treePath tickened ")
	treePath.build_incidentMatrix()

	treePathOrientized=treePath.directizeGraph()
	print("treePath tickened directized")
	treePathOrientized.build_incidentMatrix()
	gPathExtended=drawGraph(treePathOrientized)
	
	
	### Build Rand Graph from prufer code tree generation tickened randomly 
	pruferTreeGraph=pruferCodeGenTree(TREE_SIZE,True)
	print("prufer code tree")
	pruferTreeGraph.build_incidentMatrix()
	newNodes,newEdges=graphTickennerRand(pruferTreeGraph,0,2)
	print("prufer code tree tickened")
	pruferTreeGraph.build_incidentMatrix()
	gTreePruferExtended=drawGraph(pruferTreeGraph)
	
	# stoer_wagner min cut with networknx lib
	cutVal,nodesParti=nx.stoer_wagner(gTreePruferExtended)
	print(cutVal)
	print(nodesParti)
	sleep(2)
	#DIRECTIZE AND TERMINALS ASS
	#pruferTreeGraphDirectized= pruferTreeGraph.directizeGraph()
	#print("prufer code tree tickened directized")
	#pruferTreeGraphDirectized.build_incidentMatrix()

	#addGlobalTerminalNodes(pruferTreeGraphDirectized)
	#print("prufer code tree tickened directized with terminal nodes")
	#pruferTreeGraphDirectized.build_incidentMatrix()
	#drawGraphColored(pruferTreeGraphDirectized)
#main()		#TODO SWITHCK, see above 



	#TODO TESTS def & run
	#TODO SIMPLE ITERATION -> test over 2-nested iterations	for variadic num nodes -> increase edge num from start point (ticken func over minimal tree)
	#	-> sara base per test e confronti da mettere nella relazione
