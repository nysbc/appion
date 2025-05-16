#!/usr/bin/env python
import os
import shutil
from appionlib import apDDMotionCorrMaker
from appionlib import apDDFrameAligner
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apDisplay
from multiprocessing import Pool, Manager

def main():
	makeStack = apDDMotionCorrMaker.MotionCor2UCSFAlignStackLoop()
	return makeStack.run()

if __name__ == '__main__':
	procs=16
	p=Pool(procs)
	apDisplay.printMsg("Starting Appion with %d parallel processes" % procs)
	for _ in range(procs):
		p.apply_async(main)
	p.close()
	p.join()

		

