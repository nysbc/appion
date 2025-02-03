import os
from appionlib import apDisplay
from multiprocessing import Pool
import time
    
def run(loop):
    """
    processes all images
    """
    ### get images from database
    loop._getAllImages()
    os.chdir(loop.params['rundir'])
    loop.stats['startimage'] = time.time()
    loop.preLoopFunctions()
    ### start the loop
    loop.notdone=True
    loop.stats['startloop'] = time.time()
    maxProcs=os.getenv("MAX_APPION_PROCS",8)
    maxProcs=int(maxProcs)
    while loop.notdone:
        apDisplay.printColor("\nBeginning Main Loop", "green")
        imgnum = 0
        # The number of processes spawned is proportional to the total
        # backlog of images.
        procs=int(round(len(loop.imgtree) ** (1/3)))
        if procs > maxProcs:
            procs=maxProcs
        while imgnum < len(loop.imgtree) and loop.notdone is True:
            loop.stats['startimage'] = time.time()
            if (imgnum + procs) > len(loop.imgtree):
                procs=len(loop.imgtree)-imgnum
            imgnums=[imgnum + i for i in range(procs)]
            p=Pool(procs)
            p.map(loop.processOneImage, imgnums)
            p.close()
            p.join()
            imgnum+=procs
            loop.finishLoopImages(procs)

        if loop.notdone is True:
            loop.notdone = loop._waitForMoreImages()
        #END NOTDONE LOOP

    loop.postLoopFunctions()
    loop.close()