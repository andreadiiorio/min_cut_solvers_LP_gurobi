#!/usr/bin/env python3
"""
tests on mincut solvers
main function driverRandGraphIterativellyResized: drive tickening of a given N nodes minimal graph into a larger one
supported statistics mode during rand algo runnning
in main func there is code to progressivelly generate new run of driverRandGraphIterativellyResized with increased num of nodes

ENV VAR MAIN OVVERRIDE FOR TESTS
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
import numpy, scipy.stats 

def minCutLP_stoerWagner_check(graph,**args):
	"""
	test validity of solution founded by minCutLPiterative comparing with stoer_wagner output from networkx python lib
	"""
	minCutLpIterative=minCutLPIterative(graph)
	minCutStoerWagnerSize=stoer_wagner_minCut(getNetworkxGraph(graph))
	return minCutStoerWagnerSize==len(minCutLpIterative)


def _tupleListExtract1NestedField(arr,destList,fieldN0,fieldN1):
	for x in arr: destList.append(x[fieldN0][fieldN1])
_confidenceInterval= lambda a: scipy.stats.t.interval(0.95, len(a)-1, loc=mean(a), scale=scipy.stats.sem(a))
_confidenceInterval(list(range(110)))

def statisticsAndNormalTestsWrap(dataList,prefixPrintK=""):
	#wrap var stats and normal tests over dataList
	NodesStats=(mean(maxRepUntilOpt),stdev(maxRepUntilOpt),max(maxRepUntilOpt))
	ormalTestPassed=scipy.stats.normaltest(maxRepUntilOpt)[-1]>=.05
	print("@@ global until Opt MAX stats on random graphs with nodes: ",nodesN,"\t",scipy.stats.normaltest(maxRepUntilOpt),"normalTestPassed: ",normalTestPassed," (AVG,DEV,MAX)",nNodesStats)
	if normalTestPassed: print(_confidenceInterval(maxRepUntilOpt))
	
#from inspect import getsource	#lambda print
def driverRandGraphIterativellyResized(nodesN,iterationsN,**args):
	"""
	drive target function calls with as input an iterativelly increased graph
	iterationsN is the number of iteration for increase the graph 
	nodesN is starting number of nodes for the graph (that will be expanded on each iteration
	args override default configuration of this driver
	return history of graphs used on each iteration in the algoritm
		where the indexing concorde with information dumped on stdout from each algo
	"""
	global rndRunUntilOptStatsNodeGroupped
	if rndRunUntilOptStatsNodeGroupped.get(nodesN)==None: rndRunUntilOptStatsNodeGroupped[nodesN]=list()
	
	#seed()
	RAND_ALGO_ITERATIONS_NUM=lambda nodesN: int((0.5)*nodesN*(nodesN-1))	#will give prob (1-1/e) of finding the optimal min cut 
	print("1/e fail prob iterations: ",RAND_ALGO_ITERATIONS_NUM(nodesN))
	EDGES_INCREASE_STEP=5
	RND_ALGO_STATISTIC_MODE_ITERATIONS=1					#num of iteration targetted to evaluate statistics on a rand algo timing
	if args.get("RAND_ALGO_ITERATIONS_NUM")!=None:		 RAND_ALGO_ITERATIONS_NUM=args["RAND_ALGO_ITERATIONS_NUM"]
	if args.get("EDGES_INCREASE_STEP")!=None:		 EDGES_INCREASE_STEP=args["EDGES_INCREASE_STEP"]
	if args.get("RND_ALGO_STATISTIC_MODE_ITERATIONS")!=None: RND_ALGO_STATISTIC_MODE_ITERATIONS=args["RND_ALGO_STATISTIC_MODE_ITERATIONS"]
	RND_ALGO_STATISTIC_MODE_ITERATIONS_PROB=RND_ALGO_STATISTIC_MODE_ITERATIONS #num of iteration targetted to evaluate statistics on a rand algo probability failure/success
	if args.get("RND_ALGO_STATISTIC_MODE_ITERATIONS_PROB")!=None: RND_ALGO_STATISTIC_MODE_ITERATIONS_PROB=args["RND_ALGO_STATISTIC_MODE_ITERATIONS_PROB"]
	
	#log probability info
	print("graph with num nodes= ",nodesN," with this num of iteration of rand Algo: ",RAND_ALGO_ITERATIONS_NUM(nodesN))
	#print("graph with num nodes= ",nodesN," 75% success with this num of iteration of rand Algo: ",RAND_ALGO_ITERATIONS_NUM(nodesN,.25))

	graphsHistory=list()	#list of used graph in the algoritm
	graph=pruferCodeGenTree(nodesN)	#start with a tree of chosen start num of nodes
	graphNodes=list(graph.nodes.keys())
	maxNumEdge=len(graphNodes)*(len(graphNodes)-1)*(0.5)
	if EDGES_INCREASE_STEP==-1: EDGES_INCREASE_STEP=int(maxNumEdge/iterationsN)	#enable graph compleating mode in iterationsN steps
	print(maxNumEdge,EDGES_INCREASE_STEP)
	for i in range(iterationsN+1):
		graphTickennerRand(graph,EDGES_INCREASE_STEP)	#expand the graph
		t=timer()
		graphEdges=graph.extractEdges()
		print("iteration :",i,"\n\n")
		start=timer()
		minCutStoerWagnerSize=stoer_wagner_minCut(graph)
		end=timer()
		print("@stoer_wagner_minCut\tminCutval= ",minCutStoerWagnerSize," graph: Nodes=",len(graphNodes),"Edges=",len(graphEdges),"\telapsed=",end-start,"\t randGraphIndex: ",i)
		#minCutLp=list(range(minCutStoerWagnerSize))
		start=timer()
		minCutLp=minCutLPIterative2(graph)
		end=timer()
		print("@minCutLPIterative2\tminCutVal= ",len(minCutLp)," graph: Nodes=",len(graphNodes),"Edges=",len(graphEdges),"\telapsed=",end-start,"\t randGraphIndex: ",i)
		###TODO ASSERT CHECK
		assert len(minCutLp) == minCutStoerWagnerSize, str(len(minCutLp))+" vs "+str(minCutStoerWagnerSize)
		
		#run the rundom algoritm until founded the best solution
		elapsedStatisticSamples_untilOpt=list()
		randomRepetitionSamples=list()
		for j in range(RND_ALGO_STATISTIC_MODE_ITERATIONS):
			randomRepetition=0
			randAlgoMinCutVal=float("inf")
			start=timer()
			while randAlgoMinCutVal!=len(minCutLp):
				randAlgoMinCutVal=randMinCut(graph)[-1]
				randomRepetition+=1
			end=timer()
			randomRepetitionSamples.append(randomRepetition)
			elapsedStatisticSamples_untilOpt.append(end-start)
		
		if GUI_GRAPH!=None: graphsHistory.append((deepcopy(graph),minCutLp))	#graph's deep copy indexed as dumped infos on stdout ##TODO DEBUG
		avgT=mean(elapsedStatisticSamples_untilOpt)
		repAvg=mean(randomRepetitionSamples)
		repDev=devstdT=0
		if RND_ALGO_STATISTIC_MODE_ITERATIONS>1: #ovverride std deviation if multiple samples has been recorded
			devstdT=stdev(elapsedStatisticSamples_untilOpt)
			repDev=stdev(randomRepetitionSamples)
			#print("@",scipy.stats.normaltest(randomRepetitionSamples),scipy.stats.normaltest(randomRepetitionSamples)[-1]>=.05)
		untilOptStats=(repAvg,repDev,max(randomRepetitionSamples))
		print("@randMinCut-untilOpt\tgraph: Nodes=",len(graphNodes),"Edges=",len(graphEdges),"\telapsed AVG,DEV_STD=",(avgT,devstdT),"\t randGraphIndex: ",i,"\titeration to reach Optimal AVG,DEV,MAX: ",untilOptStats)
		##rndRunUntilOptStatsNodeGroupped[nodesN].append([len(graphEdges),untilOptStats])	#for stats ani
		
		
		#run random algoritm with fixed num of iteration and evaluate how mutch the output is far from the optimal
		#elapsedStatisticSamples_fixedIter=list()
		#failures=0
		#deltaMinCutRndAlgoSamples=list()
		#rndMinCutsVals=list()
		#for j in range(RND_ALGO_STATISTIC_MODE_ITERATIONS_PROB):
		#	start=timer()
		#	randAlgoMinCutVal=randMinCut(graph,RAND_ALGO_ITERATIONS_NUM(len(graphNodes)))[-1]
		#	end=timer()
		#	rndMinCutsVals.append(randAlgoMinCutVal)
		#	randAlgoMinCutDeltaOpt=randAlgoMinCutVal-len(minCutLp)
		#	if randAlgoMinCutDeltaOpt>0: failures+=1
		#	deltaMinCutRndAlgoSamples.append(randAlgoMinCutDeltaOpt)
		#	elapsedStatisticSamples_fixedIter.append(end-start)
		#avgTime,devstdTime=mean(elapsedStatisticSamples_fixedIter),0
		#avgDelta,devstdDelta=mean(deltaMinCutRndAlgoSamples),0
		#failureRate=failures/RND_ALGO_STATISTIC_MODE_ITERATIONS_PROB
		#rndMinCutValsStats=(min(rndMinCutsVals),mean(rndMinCutsVals),0,max(rndMinCutsVals))
		#if RND_ALGO_STATISTIC_MODE_ITERATIONS_PROB>1:			#ovverride std deviation if multiple samples has been recorded
		#	devstdTime=stdev(elapsedStatisticSamples_fixedIter)
		#	devstdDelta=stdev(deltaMinCutRndAlgoSamples)
		#	rndMinCutValsStats=(min(rndMinCutsVals),mean(rndMinCutsVals),stdev(rndMinCutsVals),max(rndMinCutsVals))
		#
		#print("@randMinCut-fixedIter\tminCutVal stats (min,AVG,STDEV,MAX)= ",rndMinCutValsStats," graph: Nodes=",len(graphNodes),"Edges=",len(graphEdges),"\telapsed AVG,DEV_STD=",(avgTime,devstdTime),"\t randGraphIndex: ",i,"\titerations: ",RAND_ALGO_ITERATIONS_NUM(len(graphNodes)),"\tdelta between founded sol and Opt one (AVG,DEV) ",(avgDelta,devstdDelta)," FAILURE_RATE: ",failureRate)
		if len(graphEdges)==maxNumEdge:
			print("max num of edges reached for ",len(graphNodes)," graph")
			break
	return graphsHistory


from os import environ
from math import log,e
if __name__=="__main__" or True:
		global rndRunUntilOptStatsNodeGroupped	#stats
		rndRunUntilOptStatsNodeGroupped=dict()	#dict N_NODES -> [[N_EDGES,(avgRepUntilOpt,devstdRepUntilOpt,maxRepUntilOpt)],...]


		seed()
		graphsHistoryAll=list()
		ITERATION_TICKENER=10			#num of times that fixed num nodes graph will be expanded with random edges
		GRAPH_REBUILD_ITERATION=1		#num of fixed num nodes graph will be rebuilded for new tests
		GRAPH_NODES_INC_STEP=4			
		START_NUM_NODES=4
		nodesN=START_NUM_NODES
		edgeIncStep=-1
		statisticsIterations=1
		trgProbFailure=.5
		#OVERRIDE DEFAULT CONFIG WITH ENVIRON VARIABLE
		if environ.get("START_NUM_NODES")!=None:			nodesN=int(environ["START_NUM_NODES"])
		if environ.get("GRAPH_REBUILD_ITERATION")!=None:		GRAPH_REBUILD_ITERATION=int(environ["GRAPH_REBUILD_ITERATION"])
		if environ.get("GRAPH_NODES_INC_STEP")!=None:			GRAPH_NODES_INC_STEP=int(environ["GRAPH_NODES_INC_STEP"])
		if environ.get("EDGES_INCREASE_STEP")!=None:			edgeIncStep=int(environ["EDGES_INCREASE_STEP"])
		if environ.get("ITERATION_TICKENER")!=None:			ITERATION_TICKENER=int(environ["ITERATION_TICKENER"])
		if environ.get("RND_ALGO_STATISTIC_MODE_ITERATIONS")!=None:	statisticsIterations=int(environ["RND_ALGO_STATISTIC_MODE_ITERATIONS"])
		if environ.get("TRG_PROB_FAILURE")!=None:			trgProbFailure=float(environ["TRG_PROB_FAILURE"])
		rndFixedIteration=lambda n,p=trgProbFailure: int(n*(n-1)*(0.5)*log(1/p)) #should yeld to failure probability p

		print("\nLOGGING TEST WITH:\nstartN_",nodesN,"_rebuildsN_",GRAPH_REBUILD_ITERATION,"_edgeTickenning_",ITERATION_TICKENER,"_nodesStep_",GRAPH_NODES_INC_STEP,"_edgeStep_",edgeIncStep,"_statisticsIter_",statisticsIterations,".log",sep="")
		for i in range(GRAPH_REBUILD_ITERATION):
			print("\n\n\nexploring min cut solver algoritm with a graph of ",nodesN," with variable num of edges\n\n",sep="")
			graphsHistoryAll.extend(driverRandGraphIterativellyResized\
			(nodesN,ITERATION_TICKENER,EDGES_INCREASE_STEP=edgeIncStep,RND_ALGO_STATISTIC_MODE_ITERATIONS=statisticsIterations,RAND_ALGO_ITERATIONS_NUM=None))
			
			#maxRepUntilOpt,avgRepUntilOpt=list(),list()
			#_tupleListExtract1NestedField(rndRunUntilOptStatsNodeGroupped[nodesN],maxRepUntilOpt,-1,-1)
			#_tupleListExtract1NestedField(rndRunUntilOptStatsNodeGroupped[nodesN],avgRepUntilOpt,-1,0)
			#statisticsAndNormalTestsWrap(maxRepUntilOpt)
			#statisticsAndNormalTestsWrap(avgRepUntilOpt)


			nodesN+=GRAPH_NODES_INC_STEP
		

		#DBG CMDS GRAPHS
		#a=graphsHistoryAll
		#a.sort(key=lambda x:len(x[1]))	#sort a for increasing size of min cut solution
		
