#!/usr/bin/env python3
"""
tests on mincut solvers
main function driverRandGraphIterativellyResized: drive tickening of a given N nodes minimal graph into a larger one
supported statistics mode during rand algo runnning
in main func there is code to progressivelly generate new run of driverRandGraphIterativellyResized with increased num of nodes

ENV VAR MAIN OVVERRIDE TESTS
START_NUM_NODES
GRAPH_REBUILD_ITERATION			#num of fixed num nooes graph will be created and expanded 	DFLT 1
GRAPH_NODES_INC_STEP			
EDGES_INCREASE_STEP
ITERATION_TICKENER			#num of iteration of expanding the graph with fixed num node and minCut solvers re run, DFLT 10
RND_ALGO_STATISTIC_MODE_ITERATIONS	#num of iterations for rand algo -> mean & stdev will be computed
"""
from mincut_lp import *
from timeit import default_timer as timer	
from copy import deepcopy
from random import seed
from statistics import mean,stdev
def minCutLP_stoerWagner_check(graph,**args):
	"""
	test validity of solution founded by minCutLPiterative comparing with stoer_wagner output from networkx python lib
	"""
	minCutLpIterative=minCutLPIterative(graph)
	minCutStoerWagnerSize=stoer_wagner_minCut(getNetworkxGraph(graph))
	return minCutStoerWagnerSize==len(minCutLpIterative)



def driverRandGraphIterativellyResized(nodesN,iterationsN,**args):
	"""
	drive target function calls with as input an iterativelly increased graph
	iterationsN is the number of iteration for increase the graph 
	nodesN is starting number of nodes for the graph (that will be expanded on each iteration
	args override default configuration
	return history of graphs used on each iteration in the algoritm
		where the indexing concorde with information dumped on stdout from each algo
	"""
	
	#driver configuration and **arg override logic
	RAND_ALGO_ITERATIONS_NUM=lambda nodesN: int((0.5)*nodesN*nodesN)	#will give prob (1-1/e) of finding the optimal min cut 
	EDGES_INCREASE_STEP=5
	RND_ALGO_STATISTIC_MODE_ITERATIONS=1					#num of iteration targetted to evaluate statistics on a rand algo
	if args.get("RAND_ALGO_ITERATIONS_NUM")!=None:		 RAND_ALGO_ITERATIONS_NUM=args["RAND_ALGO_ITERATIONS_NUM"]
	if args.get("EDGES_INCREASE_STEP")!=None:		 EDGES_INCREASE_STEP=args["EDGES_INCREASE_STEP"]
	if args.get("RND_ALGO_STATISTIC_MODE_ITERATIONS")!=None: RND_ALGO_STATISTIC_MODE_ITERATIONS=args["RND_ALGO_STATISTIC_MODE_ITERATIONS"]

	graphsHistory=list()	#list of used graph in the algoritm
	graph=pruferCodeGenTree(nodesN)	#start with a tree of chosen start num of nodes
	for i in range(iterationsN):
		graphNodes=list(graph.nodes.keys())
		graphEdges=graph.extractEdges()
		print("iteration :",i,"\n\n")
		start=timer()
		minCutStoerWagnerSize=stoer_wagner_minCut(graph)
		end=timer()
		print("@stoer_wagner_minCut\tminCutval= ",minCutStoerWagnerSize," graph: Nodes=",len(graphNodes),"Edges=",len(graphEdges),"\telapsed=",end-start,"\t randGraphIndex: ",i)
		start=timer()
		minCutLp=minCutLPIterative(graph)
		end=timer()
		print("@minCutLPIterative\tminCutVal= ",len(minCutLp)," graph: Nodes=",len(graphNodes),"Edges=",len(graphEdges),"\telapsed=",end-start,"\t randGraphIndex: ",i)
		#TODO ASSERT CHECK
		assert len(minCutLp) == minCutStoerWagnerSize, str(len(minCutLp))+" vs "+str(minCutStoerWagnerSize)
		
		#run the rundom algoritm until founded the best solution
		elapsedStatisticSamples_untilOpt=list()
		for j in range(RND_ALGO_STATISTIC_MODE_ITERATIONS):
			randomRepetition=0
			randAlgoMinCut=graphEdges	#start with maxium costly sol, re iter algo until opt. one founded
			start=timer()
			while len(randAlgoMinCut)!=len(minCutLp):
				randAlgoMinCut=randMinCut(graph)
				randomRepetition+=1
			end=timer()
			elapsedStatisticSamples_untilOpt.append(end-start)
		graphsHistory.append((deepcopy(graph),minCutLp,randAlgoMinCut))	#graph's deep copy indexed as dumped infos on stdout ##TODO DEBUG 
		avg=mean(elapsedStatisticSamples_untilOpt)
		devstd=0
		if RND_ALGO_STATISTIC_MODE_ITERATIONS>1: devstd=stdev(elapsedStatisticSamples_untilOpt)
		print("@randMinCut-untilOpt\tgraph: Nodes=",len(graphNodes),"Edges=",len(graphEdges),"\telapsed AVG,DEV_STD=",(avg,devstd),"\t randGraphIndex: ",i,"\titeration to reach Optimal: ",randomRepetition)
		
		#run random algoritm with fixed num of iteration and evaluate how mutch the output is far from the optimal
		elapsedStatisticSamples_fixedIter=list()
		for j in range(RND_ALGO_STATISTIC_MODE_ITERATIONS):
			start=timer()
			randAlgoMinCut=randMinCut(graph,RAND_ALGO_ITERATIONS_NUM(len(graphNodes)))
			end=timer()
			randAlgoMinCutDeltaOpt=len(randAlgoMinCut)-len(minCutLp)
			elapsedStatisticSamples_fixedIter.append(end-start)
		avg=mean(elapsedStatisticSamples_fixedIter)
		devstd=0
		if RND_ALGO_STATISTIC_MODE_ITERATIONS>1: devstd=stdev(elapsedStatisticSamples_fixedIter)
		print("@randMinCut-fixedIter\tminCutVal= ",len(randAlgoMinCut)," graph: Nodes=",len(graphNodes),"Edges=",len(graphEdges),"\telapsed AVG,DEV_STD=",(avg,devstd),"\t randGraphIndex: ",i,"\titerations: ",RAND_ALGO_ITERATIONS_NUM(len(graphNodes)),"\tdelta between founded sol and Opt one: ",randAlgoMinCutDeltaOpt)
		#TODO dump paper probability evaluation
		
		if len(graphEdges)==len(graphNodes)*(len(graphNodes)-1)*(0.5):
			print("max num of edges reached for ",len(graphNodes)," graph")
			break
		graphTickennerRand(graph,EDGES_INCREASE_STEP)	#expand the graph
	return graphsHistory


from os import environ
if __name__=="__main__" or True:
		seed()
		graphsHistoryAll=list()
		ITERATION_TICKENER=10			#num of times that fixed num nodes graph will be expanded with random edges
		GRAPH_REBUILD_ITERATION=1		#num of fixed num nodes graph will be rebuilded for new tests
		GRAPH_NODES_INC_STEP=4			
		START_NUM_NODES=4
		nodesN=START_NUM_NODES
		edgeIncStep=3
		statisticsIterations=1
		#OVERRIDE DEFAULT CONFIG WITH ENVIRON VARIABLE
		if environ.get("START_NUM_NODES")!=None:			nodesN=int(environ["START_NUM_NODES"])
		if environ.get("GRAPH_REBUILD_ITERATION")!=None:		GRAPH_REBUILD_ITERATION=int(environ["GRAPH_REBUILD_ITERATION"])
		if environ.get("GRAPH_NODES_INC_STEP")!=None:			GRAPH_NODES_INC_STEP=int(environ["GRAPH_NODES_INC_STEP"])
		if environ.get("EDGES_INCREASE_STEP")!=None:			edgeIncStep=int(environ["EDGES_INCREASE_STEP"])
		if environ.get("ITERATION_TICKENER")!=None:			ITERATION_TICKENER=int(environ["ITERATION_TICKENER"])
		if environ.get("RND_ALGO_STATISTIC_MODE_ITERATIONS")!=None:	statisticsIterations=int(environ["RND_ALGO_STATISTIC_MODE_ITERATIONS"])

		print("\nLOGGING TEST WITH:\nstartN_",nodesN,"_rebuildsN_",GRAPH_REBUILD_ITERATION,"_edgeTickenning_",ITERATION_TICKENER,"_nodesStep_",GRAPH_NODES_INC_STEP,"_edgeStep_",edgeIncStep,"_statisticsIter_",statisticsIterations,".log",sep="")
		for i in range(GRAPH_REBUILD_ITERATION):
			print("exploring min cut solver algoritm with a graph of ",nodesN," with variable num of edges\n\n",sep="")
			graphsHistoryAll.extend(driverRandGraphIterativellyResized(nodesN,ITERATION_TICKENER,EDGES_INCREASE_STEP=edgeIncStep,RND_ALGO_STATISTIC_MODE_ITERATIONS=statisticsIterations))
			nodesN+=GRAPH_NODES_INC_STEP
		#DBG CMDS
		a=graphsHistoryAll
		a.sort(key=lambda x:len(x[1]))	#sort a for increasing size of min cut solution

