#!/usr/bin/env python
import os
import shutil
from appionlib import apDDMotionCorrMaker
from appionlib import apDDFrameAligner
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apDisplay
from multiprocessing import Pool

def main():
	makeStack = apDDMotionCorrMaker.MotionCor2UCSFAlignStackLoop()
	makeStack.run()

if __name__ == '__main__':
	appionProcCount=os.getenv("APPION_PROCESSES", 8)
	appionProcCount=int(appionProcCount)
	p=Pool(appionProcCount)
	for _ in range(appionProcCount):
		p.apply_async(main)
	p.close()
	p.join()