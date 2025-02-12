#!/usr/bin/env python
import os
from appionlib import apDDMotionCorrMaker
from multiprocessing import Pool
import logging
import sys

def main():
	logger=logging.getLogger()
	logHandler=logging.StreamHandler(sys.stdout)
	logFormatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(process)d - %(message)s")
	logHandler.setFormatter(logFormatter)
	logger.setLevel("INFO")
	logHandler.setlevel("INFO")
	logger.addHandler(logHandler)
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