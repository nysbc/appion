#!/usr/bin/env python
import os
import shutil
from appionlib import apDDMotionCorrMaker
from appionlib import apDDFrameAligner
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apDisplay
from multiprocessing import Pool, Manager
import os
from time import sleep
import pickle
from fcntl import flock, LOCK_EX, LOCK_UN

def imageLoop():
	makeStack = apDDMotionCorrMaker.MotionCor2UCSFAlignStackLoop()
	emptyCount = 0
	pendingListPath = os.path.join(makeStack.params['rundir'], "todo.pkl")
	# End loop after 60 consecutive empty pending job lists.
	while emptyCount < 60:
		makeStack._reloadDoneDict()
		imgtree=makeStack._getAllImages()
		if len(imgtree) == 0:
			emptyCount+=1
		else:
			emptyCount=0
		if not os.path.isfile(pendingListPath):
			try:
				apDisplay.printWarning('creating %s'% pendingListPath)
				f=open(pendingListPath, 'a', 0666)
				f.close()
			except:
				apDisplay.printWarning("File creation failed.  Restarting loop.")
				continue
		else:
			apDisplay.printWarning('%s already exists'% pendingListPath)
		f=open(pendingListPath, 'rb+')
		apDisplay.printWarning('locking %s'% pendingListPath)
		flock(f, LOCK_EX)
		apDisplay.printWarning('lock acquired for %s'% pendingListPath)
		f.seek(0)
		f.truncate()
		apDisplay.printWarning('saving todo list')
		try:
			pickle.dump(imgtree, f)
			f.flush()
		except Exception as e:
			apDisplay.printError(e)
			return
		apDisplay.printWarning('unlocking %s'% pendingListPath)
		flock(f, LOCK_UN)
		f.close()
		sleep(60)

def main():
	makeStack = apDDMotionCorrMaker.MotionCor2UCSFAlignStackLoop()
	while True:
		try:
			r=makeStack.run(todolist=True)
			return r
		except Exception as e:
			apDisplay.printWarning("exception has occurred: %s" % str(e))
			continue

if __name__ == '__main__':
	procs=int(os.getenv("APPION_MOTIONCOR2_PROCS",16))
	p=Pool(procs)
	apDisplay.printMsg("Starting task queue creation loop")
	p.apply_async(imageLoop)
	apDisplay.printMsg("Starting Appion with %d parallel processes" % procs)
	for _ in range(procs):
		p.apply_async(main)
	p.close()
	p.join()

		

