import submitit
import os
from time import sleep, time
import logging
import sys
from signal import signal, SIGINT, SIGTERM, SIGCONT, Signals
from .retrieve import readImageSet, retrieveRejectedImages
from .calc import filterImages
from typing import Callable

# Parameters passed in using lambdas.
def loop(pipeline, args: dict, retrieveDoneImages : Callable = lambda : set(), preLoop : Callable = lambda args : {}, postLoop : Callable = lambda jobmetadata : None, retrieveReprocessImages : Callable = lambda : set(), batch_size : int = 1, max_window : int = 200, parallelism : int = 32) -> None:
    jobmetadata={}
    # Signal handler used to ensure that cleanup happens if SIGINT, SIGCONT or SIGTERM is received.
    def handler(signum, frame):
        signame = Signals(signum).name
        logger.info(f"Received {signame} signal.  Cleaning up and exiting now.")
        try:
            postLoop(jobmetadata)
            logger.info("Server has exited cleanly.  Bye!")
        except SystemExit:
            postLoop(jobmetadata)
            logger.debug("Function lower on the stack has received exited midway.")
        except:
            logger.exception("Exception occurred while server was trying to exit cleanly.", stack_info=True)
            sys.exit(1)
        sys.exit(0)

    # Set up logging
    logger=logging.getLogger(__name__)
    logHandler=logging.StreamHandler(sys.stdout)
    logFormatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(process)d - %(message)s")
    logHandler.setFormatter(logFormatter)
    logger.setLevel("INFO")
    logHandler.setLevel("INFO")
    logger.addHandler(logHandler)

    # Set up the control loop and signal handlers.
    signal(SIGTERM, handler)
    signal(SIGINT, handler)
    signal(SIGCONT, handler)

    jobmetadata=preLoop()
    waitTime=30
    prev_taskset=set()
    failure_cooldown=1
    failure_waits=0

    executor = submitit.AutoExecutor(folder=os.path.join(args["rundir"], "working"))
    executor.update_parameters(timeout_min=6, slurm_partition="appion-motioncorrection", slurm_gres="gpu:1", slurm_cpus_per_task=2, slurm_array_parallelism=parallelism)
    while True:
        t0=time()
        all_images=readImageSet(args["sessionname"], args["preset"])
        done_images=retrieveDoneImages()
        rejected_images=retrieveRejectedImages(all_images, args["sessionname"], None, None, args["tiltangle"])
        # Not used by motioncor2; used by ctffind4
        reprocess_images=retrieveReprocessImages()
        taskset=filterImages(all_images, done_images, reprocess_images, rejected_images)
        unprocessed_image_count=len(taskset)       
        if prev_taskset:
            failureset=taskset & prev_taskset
            taskset=taskset-failureset
            logger.info("%d previously failed images will not be processed this iteration." % len(failureset))
        tasklist=list(taskset)
        tasklist.sort()
        tasklist.reverse() 
        t1=time()
        logger.info("Constructed task list in %d seconds." % (t1-t0))
        logger.info("Image counts: %d total images, %d done images, %d rejected images, and %d images marked for reprocessing." % (len(all_images), len(done_images), len(rejected_images), len(reprocess_images)))
        if tasklist:
            pipeline_t0=time()
            futures=[]
            batches=[]
            taskStartIdx=0
            taskEndIdx=batch_size
            maxIdx=min(unprocessed_image_count, max_window)
            for imageid in tasklist:
                if taskEndIdx > maxIdx:
                    taskEndIdx=maxIdx
                batches.append(tasklist[taskStartIdx:taskEndIdx])
                prev_taskset.add(tasklist[taskStartIdx:taskEndIdx])
                taskStartIdx+=batch_size
                taskEndIdx+=batch_size
            with executor.batch():
                for batchid, imageids in enumerate(batches):
                    future = executor.submit(pipeline, batchid, imageids, args, jobmetadata)
                    futures.append(future)
            future_complete_counter=0
            throughput_t0=time()
            future_complete_counter=0
            step=20
            while future_complete_counter != len(futures) and len(futures) != 0:
                future_complete_counter = sum(f.done() for f in futures)
                if future_complete_counter > step and future_complete_counter != 0:
                    throughput_t1=time()
                    throughput=(future_complete_counter)/(((throughput_t1-throughput_t0))/60.)
                    remaining_image_count=unprocessed_image_count-future_complete_counter
                    logger.info("Progress: %d / %d images processed." % (future_complete_counter, unprocessed_image_count))
                    logger.info("Throughput: %.2f images/min." % throughput)
                    if throughput > 0.0:
                        logger.info("Estimated remaining time: %.2f min." % (remaining_image_count/throughput))
                    else:
                        logger.info("Estimated remaining time: N/A min.")
                    step+=20
                sleep(10)
            pipeline_t1=time()
            logger.info("Finished processing %d images in %d seconds." % (len(prev_taskset), (pipeline_t1-pipeline_t0)))
        else:
            logger.info(f"No new images.  Waiting {waitTime} seconds.")
            sleep(waitTime)
            if prev_taskset:
                failure_waits+=1
                if failure_waits >= failure_cooldown:
                    prev_taskset=set()
                    failure_waits=0
