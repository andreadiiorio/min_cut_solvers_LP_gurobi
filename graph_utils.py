#!/usr/bin/env python2.7
#utils classes and functions used by the min cut problem solver

import copy,random

#basic graph rappresentation by Adjacency Lists and python built-in data types
#Edges rappresentation via tuple (naming reflect this: edge e: 1->2; 1 is the tail of the edge
EDGE_TAIL_INDEX=0	#edge tail index in edge tuple
EDGE_HEAD_INDEX=1	#edge head index in edge tuple
EDGE_WEIGHT_INDEX=2	#edge weight index
class Graph:
	def __init__(self,**argsDict):
	#non default init of graph by calling the constructor with kwargs named in same way of graph class attributes
	#it's assumed here but in the whole module consistency in the passed parameters, like edge correspond to nodes
		self.directed=False
		self.nodes=dict()	#adjacency list rappresentation of graph nodeID->list of nodesID reachable 
		self.edges=list()	#list of tuples [edgeTail,edgeHead]
		#non default initialization
		if argsDict.get("directed")!=None:
			self.nodes=argsDict["directed"]
		if argsDict.get("nodes")!=None:
			self.addNodes(argsDict["nodes"])	#flexible nodes adding with a partial robstuness type check
		if argsDict.get("edges")!=None:
			self.addEdges(argsDict["edges"])
	
	def addNodes(self,nodesNew):
		#add new nodes as dict of nodesID -> nodesID reachable from this node
		if type(nodesNew)==type(dict()):
			self.nodes.update(nodesNew)
		elif type(nodesNew)==type(list()): #otherwise add empty nodes (un connected) from passed list nodesNew
			for n in nodesNew:
				self.nodes[n]=list() #add nodes as unconnected
		else:
			raise Exception("invild type for newly added nodes")

	def addEdges(self,edgesNew):
		#edge to add to graph are rappresented by a list of tuples of newly (ordinatlly) connected nodes, e.g. [(1,2),(4,1)
		print("\n",edgesNew,"\n",self.nodes,"\n",self.edges)
		#update edges fields
		self.edges.extend(edgesNew)
		#update adj list in place
		for e in edgesNew:
			self.nodes[e[EDGE_TAIL_INDEX]].append(e[EDGE_HEAD_INDEX])
			if not self.directed:	#update adj list for un directed graphs
				self.nodes[e[EDGE_HEAD_INDEX]].append(e[EDGE_TAIL_INDEX])
		print(self.nodes)
	
	def remEdges(self,edgesToRemove):
		#edgesToRemove is a list of tuple of edges to remove
		for edge in edgesToRemove:
			self.edges.remove(edge)
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

	def build_incidentMatrix(self):
		print(self.nodes)
		print(self.edges)
		EDGE_EXIT_NODE=1
		EDGE_ENTER_NODE=-1
		#0 init matrix shallow copy fully avoiding
		incidentMatrix=list()
		for i in range(len(self.nodes)):
			incidentMatrix.append(list())
			for j in range(len(self.edges)):
				incidentMatrix[i].append(0)

		for edgeID in range(len(self.edges)):
			edgeTuple=self.edges[edgeID]
			edgeSrc=edgeTuple[EDGE_TAIL_INDEX]
			edgeDst=edgeTuple[EDGE_HEAD_INDEX]
			incidentMatrix[edgeSrc][edgeID]=EDGE_EXIT_NODE
			incidentMatrix[edgeDst][edgeID]=EDGE_ENTER_NODE
			if self.directed==False:			#handle non orienthed graph
				incidentMatrix[edgeDst][edgeID]=EDGE_EXIT_NODE
		return incidentMatrix
				

	def directizeGraph(self):
		#return a new copy of the current undirect graph as direct
		#the newly created direct graph will have twice the current edges with reverse src and dst
		if self.directed:
			raise Exception("already direct graph")
		directedGraph=copy.deepcopy(self)
		directedGraph.directed=True
		edgesToAdd=list()
		#create reverse edges with same cost to add to undirect graph 
		for edge in directedGraph.edges:
			newEdge=(edge[EDGE_HEAD_INDEX],edge[EDGE_TAIL_INDEX],edge[EDGE_WEIGHT_INDEX])
			edgesToAdd.append(newEdge)
		
		directedGraph.addEdges(edgesToAdd)
		return directedGraph
		


def genTreePath(nodesN):
	#generate a random tree with nodesN nodes as a random path among nodes
	#return tuple (nodeIDs,edges list)
	treeNodesIDs=list(range(nodesN))
	treeEdges=list()
	nodesDeepCopy=copy.deepcopy(treeNodesIDs)
	node=random.choice(nodesDeepCopy)	#select random root among nodes IDs
	nodesDeepCopy.remove(node)

	for x in range(TREE_SIZE-1):
		nextNode=random.choice(nodesDeepCopy)
		nodesDeepCopy.remove(nextNode)

		edge=(node,nextNode,1)
		treeEdges.append(edge)
		node=nextNode
	return (treeNodesIDs,treeEdges)

def _printMatrix(matrix,title):
	print(title)
	for row in matrix:
		print(row)
if __name__=="__main__":
	random.seed()
	#Basic graphs build
	#tree
	TREE_SIZE=10
	treeNodes,treeEdges=genTreePath(TREE_SIZE)
	treePath=Graph(nodes=treeNodes,edges=treeEdges)
	_printMatrix(treePath.build_incidentMatrix(),"incidentMatrix basic treePath")
	treePathOrientized=treePath.directizeGraph()
	_printMatrix(treePathOrientized.build_incidentMatrix(),"incidentMatrix orientized treePath")

	#TODO TESTS def & run
	#TODO FROM MINIMAL TREE PROGRSSIVELLY ADD EDGES -> ticken function
	#TODO SIMPLE ITERATION -> test over 2-nested iterations	for variadic num nodes -> increase edge num from start point (ticken func over minimal tree)
	#	-> sara base per test e confronti da mettere nella relazione
