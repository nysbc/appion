import os
from appionlib import apDisplay
from appionlib import apDatabase
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
            applyresults=[]
            for idx in imgnums:
                pixsize=apDatabase.getPixelSize(loop.imgtree[idx])
                applyresults.append(p.apply_async(processOneImage, (loop, idx, pixsize)))
            p.close()
            p.join()
            applyresults=[r.get() for r in applyresults]
            for applyresult in applyresults:
                imgdata=applyresults[0]
                results=applyresults[1]
                ### WRITE db data
                if loop.params['commit'] is True:
                    if not loop.params['background']:
                        apDisplay.printColor(" ==== Committing data to database ==== ", "blue")
                    loop.loopCommitToDatabase(imgdata)
                    loop.commitResultsToDatabase(imgdata, results)
                else:
                    apDisplay.printWarning("not committing results to database, all data will be lost")
                    apDisplay.printMsg("to preserve data start script over and add 'commit' flag")
                    loop.writeResultsToFiles(imgdata, results)
                loop.loopCleanUp(imgdata)
            imgnum+=procs
            loop.finishLoopImages(procs)

        if loop.notdone is True:
            loop.notdone = loop._waitForMoreImages()
        #END NOTDONE LOOP

    loop.postLoopFunctions()
    loop.close()

def processOneImage(loop, imgnum, pixsize):
    imgdata = loop.imgtree[imgnum]

    ### CHECK IF IT IS OKAY TO START PROCESSING IMAGE
    if not loop._startLoop(imgdata):
        return

    ### set the pixel size
    loop.params['apix'] = pixsize
    if not loop.params['background']:
        apDisplay.printMsg("Pixel size for image number %d: %s" % (imgnum, str(loop.params['apix'])))

    ### START any custom functions HERE:
    results = loop.loopProcessImage(imgdata)

    return (imgdata, results)

