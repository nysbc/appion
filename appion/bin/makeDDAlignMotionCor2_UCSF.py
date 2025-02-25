#!/usr/bin/env python
import os
import shutil
from appionlib import apDDMotionCorrMaker
from appionlib import apDDFrameAligner
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apDisplay
from multiprocessing import Pool

def main(numProcs,minProcs,maxProcs):
	makeStack = apDDMotionCorrMaker.MotionCor2UCSFAlignStackLoop()
	return makeStack.run(True,numProcs,minProcs,maxProcs)

if __name__ == '__main__':
	startPower=2
	endPower=4
	minProcs=2**startPower
	maxProcs=2**endPower
	notdone=True
	imgCount=0
	while notdone:
		procs=2**startPower
		for tmpPower in range(startPower+1,endPower+1):
			if imgCount > 2**tmpPower:
				procs=2**tmpPower
		p=Pool(procs)
		results=[]
		apDisplay.printMsg("Starting Appion with %d parallel processes" % procs)
		for _ in range(procs):
			results.append(p.apply_async(main, (procs,minProcs,maxProcs)))
		p.close()
		p.join()
		returnData=[r.get(1) for r in results]
		try:
			imgCounts=[int(r[0]) for r in returnData if r[0]]
		except:
			imgCounts=[]
		notDones=[r[1] for r in returnData if r[1]]
		if imgCounts:
			imgCount=max(imgCounts)
		else:
			imgCount=0
		if sum(notDones) == 0:
			notdone=False

		

