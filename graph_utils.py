#!/usr/bin/env python3
#utils classes and functions used by the min cut problem solver
#basic graph rappresentation by Adjacency Lists and python built-in data types
#some utils function to well support mincut solvers 

from copy import copy,deepcopy
from random import choice,seed,uniform,shuffle


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


	def pickUniformRandomEdge(self):
		#return a uniformly picked random edge with a trivial selection among all possible edges
		return choice(self.extractEdges())

	def pickUniformRandomEdgeQuick(self,nodesDegree=None,totDegrees=None):
		"""
		pick uniformiformly a random edge from graph 
		nodesDegree is a dict: nodeID -> degree of node
		totDegrees is the cumulative sum of all nodes degrees
		if nodesDegree,totDegrees are not gived will be computed
		uniform random edge selection based on a random weighted edge tail selection
		for each node in the graph's adj list will be allocated a range [a,b) accordindly with its degree
		a number n uniformly randomly picked in range [RANGE_START,RANGE_END] will discriminate the node N1 ( n is in ode's allocated range)
		finally will be randomly uniformly selected another node N2 in N1's neighbors list
		will be returned the selected edge (N1,N2)
		"""
		if nodesDegree==None and totDegrees==None:
			nodesDegree,totDegrees=_computeNodesDegree(self)
		rndEdgeTail=rndEdgeHead=None
		RANGE_START=0
		RANGE_END=1000
		range_len=RANGE_END-RANGE_START
		nodeStartRange=RANGE_START	#will hold actual node's range start
		
		randomUniformPick=uniform(RANGE_START,RANGE_END)	#UNIFORM RAND EXTRACTION IN RANGE
		nodesPickRanges=list()	#list of [(rangeStart,rangeEnd,nodeID),...] where rangeEnd is NotIncluded in nodeID pick range
		# alloc for each node a selection  range for random weighted pick
		for nodeID,degree in nodesDegree.items():
			nodeRangeLen=(degree/float(totDegrees))*range_len
			
			#alloc for node range (nodeStartRange,nodeStartRange+nodeRangeLen)
			nodesPickRanges.append((nodeStartRange,nodeStartRange+nodeRangeLen,nodeID))
			nodeStartRange+=nodeRangeLen
		
		# detect witch is the edge Tail discriminated by randomUniformPick checking nodes pick ranges
		for n in nodesPickRanges:
			if n[0] <= randomUniformPick and randomUniformPick < n[1]:	#founded edge tail node
				rndEdgeTail=n[2]
				break
		#now pick edge head simply with uniform choice among rndEdgeTail adj list
		rndEdgeHead=choice(self.nodes[rndEdgeTail])
		return (rndEdgeTail,rndEdgeHead,1)


	def contractEdgeQuick(self,e):	
		"""
		contract edge from current graph.
		nodes of edge e (n1,n2) will be deletted and new node rappresentted by python tuple (n1,n2) will be created
		multiple edge keeped so every node incident to the new node was incident to either n1 or n2
		self edges avoided in the new node
		if n1 or n2 was already a previously contracted node  during the merge the new node will be renamed as the whole list of contracted nodes
		so the random algoritm will easily found the partition identified by the founded cut at the end

		"""
		eTail=e[EDGE_TAIL_INDEX]
		eHead=e[EDGE_HEAD_INDEX]
		#build new node ID as concatenation of composing IDs in tuple
		newNode=contractEdgeMergeIDs(eTail,eHead)
		#merge contracted nodes adj lists 		#TODO FASTER WITH DICT BUILD ??
		#print("CONTRACT",e[:-1],"-->",newNode," graph before  ",self)
		eTailNeigh=self.nodes.pop(eTail,list())
		eTailNeigh.extend(self.nodes.pop(eHead,list()))
		#remove self loop
		newNodeNeigh=list()
		for x in eTailNeigh:
			if x!=eTail and x!=eHead: newNodeNeigh.append(x)
		del(eTailNeigh)
		#RESTRUCT OTHER NODEs ADJ LIST WITH THE NEW NODE CREATED
		for node, neighboors in self.nodes.items():
			for i in range(len(neighboors)):
				n=neighboors[i]
				if eTail==n or eHead==n:
					#self.nodes[node][i]=newNode	#update
					neighboors[i]=newNode
		#finally insert the contracted node with merged neighboors list
		self.nodes[newNode]=newNodeNeigh
		#print("contracted\t",eTail," ",eHead," -> ",newNodeID\t graphResoult: ",self)	#TODO DEBUG
		return len(newNodeNeigh)
	
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
				edge=(n, n1, DEFAULT_EDGE_WEIGHT)
				#AVOID DUPLICATED EDGE INSERTION FOR UNDIRECTED GRAPH
				edgeRev=(n1,n,DEFAULT_EDGE_WEIGHT)
				if self.directed==False and edgeRev in edges:
					continue	
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

		if self.directed:	raise Exception("already direct graph")
		directedGraph=deepcopy(self)
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
		outStr="Graph\t"
		if self.directed:
			outStr+="Directed\t"
		else:
			outStr+="Undirected\t"
		return outStr+str(self.nodes)

def contractEdgeMergeIDs(eTail,eHead):
	newNodeIDs=list()
	if type(eTail)==int:
		newNodeIDs.append(eTail)
	else:
		newNodeIDs.extend(eTail)
	if type(eHead)==int:
		newNodeIDs.append(eHead)
	else:
		newNodeIDs.extend(eHead)
	newNodeID=tuple(newNodeIDs)
	return newNodeID

def _computeNodesDegree(graph):
	#return nodes degree dict, tot degree of all nodes in graph
	nodesDegree=dict()
	totDegrees=0
	for nodeID,neighboors in graph.nodes.items():
		nodesDegree[nodeID]=len(neighboors)
		totDegrees+=len(neighboors)
	return nodesDegree,totDegrees


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
	nodesDeepCopy=deepcopy(treeNodesIDs)
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

PRUFER_CODE_ARRAY_UNIQ=False
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
		if PRUFER_CODE_ARRAY_UNIQ: 	newNodesArrIDs.remove(nid)
	
	shuffle(pruferCodeArr)
	newEdges=pruferCodeGenTreeEdges(pruferCodeArr)
	pruferTreeGraph=Graph(nodes=newNodes,edges=newEdges)
	if logPrint:
		print("prufer code from random array: ",pruferCodeArr,"resulting edges")
		print(newEdges)
		pruferTreeGraph.build_incidentMatrix()
	return pruferTreeGraph

def graphTickennerRand(graph,edgesN,residualTry=30):
	#make the input graph "tickenner" by adding  edgesN randomly
	
	edgesNumActual=len(graph.extractEdges())
	#adding edges
	nodesIDs=list(graph.nodes.keys())
	maxEdgesNum=int(len(nodesIDs)*(len(nodesIDs)-1)*(0.5))
	e=0
	while residualTry>= 0 and edgesN>=e and (edgesNumActual+e)<=maxEdgesNum :
		edgeTailNode=choice(nodesIDs)
		nodesIDsCopy=copy(nodesIDs)	#quick shallow copy
		nodesIDsCopy.remove(edgeTailNode) #avoid useless self edge
		edgeHeadNode=choice(nodesIDsCopy)
		newPossibleEdge=(edgeTailNode,edgeHeadNode,DEFAULT_EDGE_WEIGHT)
		#eventually new possible edge may not be added to the graph if already in
		if edgeHeadNode in graph.nodes[edgeTailNode]:
			residualTry-=1	#avoid unlucky endless loop
			continue
		residualTry=30
		graph.addEdges([(edgeTailNode,edgeHeadNode,DEFAULT_EDGE_WEIGHT)])	#single insert
		e+=1

	
	
	return e
		

#####	GRAPH WRITE VIEW LOGIC ON GUI OF NETWORKX
from os import environ
#GUI_GRAPH=True
GUI_GRAPH=environ.get("GUI_GRAPH")!=None and len(environ["GUI_GRAPH"])>0
from networkx import stoer_wagner
from networkx import Graph as Graph_nx
from networkx import DiGraph as DiGraph_nx

from time import sleep
def getNetworkxGraph(graph):

	g=Graph_nx()	
	if graph.directed:	#overwrite  g for direct graphs
		g=DiGraph_nx()
	g.add_nodes_from(list(graph.nodes.keys()))
	edgesHeadTailList=list()
	#edgesWeightList=list()		#same indexing edgesHeadTailList abve
	edges=graph.extractEdges()
	for e in edges:
		edgesHeadTailList.append(e[:-1]) #exclude nested weight field
		#edgesWeightList.append(e[-1])
	g.add_edges_from(edgesHeadTailList)
	return g
	
if GUI_GRAPH:	#this flag (settable by env) can trigger the import of (heavy) graphical lib for the graphical rappresentation
	import matplotlib.pyplot as plt
	import networkx as nx
	drawn=0
	COLOR_N="g"
	COLOR_E="r"
	def drawGraph(graph,blockingShow=False):
		drawGraphMinCut(graph,blockingShow=blockingShow)
	def drawGraphMinCut(graph,minCutEdges=[],s_node_id=-1,t_node_id=-1,blockingShow=False):
		global drawn
		#try draw graph by nxgraph python lib
		#return nx.Graph obj 
		g=getNetworkxGraph(graph)
		nodesPositions = nx.spring_layout(g)  # positions for all nodes
		plt.subplot()
		nodesToDraw=list(g.nodes.keys())
		if s_node_id!=-1 and t_node_id!=-1:
			#draw s,t nodes with different color, if given
			nx.draw_networkx_nodes(g,nodesPositions,nodelist=[s_node_id,t_node_id],node_color=COLOR_N,with_labels=True)
			nodesToDraw.remove(s_node_id)
			nodesToDraw.remove(t_node_id)
		
		nx.draw_networkx(g,nodesPositions,nodelist=nodesToDraw,with_labels=True)	#draw residual nodes
		nx.draw_networkx_edges(g,nodesPositions,minCutEdges,edge_color=COLOR_E)		#draw min cut edges,if given
		
		#nx.draw(g,with_labels=True)
		plt.show(block=blockingShow)
		return g

		# EXAMPLE COLORED EDGE #g.add_edge(e[EDGE_TAIL_INDEX],e[EDGE_HEAD_INDEX],color=colo,weight=e[EDGE_WEIGHT_INDEX])
		
	def drawGraphColored(graph):	#TODO DEPRECATED
	
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

if __name__=="__main__":  
	global TREE_SIZE,gTreePruferExtended,gPathExtended
	seed()
	TREE_SIZE=20
	
	###	Build Rand Graph from a random Path tickened randomly 

	#treeNodes,treeEdges=genTreePath(TREE_SIZE)
	#treePath=Graph(nodes=treeNodes,edges=treeEdges)
	#print("treePath simple")
	#treePath.build_incidentMatrix()
	#newNodes,newEdges=graphTickennerRand(treePath,1)
	##print("newNodes",newNodes,"newEdges",newEdges)
	#print("treePath tickened ")
	#treePath.build_incidentMatrix()

	#treePathOrientized=treePath.directizeGraph()
	#print("treePath tickened directized")
	#treePathOrientized.build_incidentMatrix()
	#gPathExtended=drawGraph(treePathOrientized)
	
	
	### Build Rand Graph from prufer code tree generation tickened randomly 
	pruferTreeGraph=pruferCodeGenTree(TREE_SIZE,True)
	drawGraph(pruferTreeGraph,True)
	print("prufer code tree")
	pruferTreeGraph.build_incidentMatrix()
	newNodes,newEdges=graphTickennerRand(pruferTreeGraph,2)
	print("prufer code tree tickened")
	pruferTreeGraph.build_incidentMatrix()
	gTreePruferExtended=drawGraph(pruferTreeGraph)
	
	# stoer_wagner min cut with networknx lib
	#cutVal,nodesParti=stoer_wagner(gTreePruferExtended)
	#print(cutVal,nodesParti)
	#pruferTreeGraphDirectized= pruferTreeGraph.directizeGraph()
	#print("prufer code tree tickened directized")
	#pruferTreeGraphDirectized.build_incidentMatrix()

	#addGlobalTerminalNodes(pruferTreeGraphDirectized)
	#print("prufer code tree tickened directized with terminal nodes")
	#pruferTreeGraphDirectized.build_incidentMatrix()
	#drawGraphColored(pruferTreeGraphDirectized)
