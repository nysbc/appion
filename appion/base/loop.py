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
def loop(pipeline, args: dict, retrieveDoneImages : Callable = lambda : set(), preLoop : Callable = lambda args : {}, postLoop : Callable = lambda jobmetadata : None, retrieveReprocessImages : Callable = lambda : set(), min_workers : int = 0, max_workers : int = 32) -> None:
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
    prev_tasklist=set()
    failure_cooldown=1
    failure_waits=0

    executor = submitit.AutoExecutor(folder=os.path.join(args["rundir"], "working"))
    executor.update_parameters(timeout_min=6, slurm_partition="appion-motioncorrection", slurm_gres="gpu:1", cpus_per_task=2, cpus_per_gpu=2, slurm_array_parallelism=max_workers)
    while True:
        t0=time()
        all_images=readImageSet(args["sessionname"], args["preset"])
        done_images=retrieveDoneImages()
        rejected_images=retrieveRejectedImages(all_images, args["sessionname"], None, None, args["tiltangle"])
        # Not used by motioncor2; used by ctffind4
        reprocess_images=retrieveReprocessImages()
        tasklist=filterImages(all_images, done_images, reprocess_images, rejected_images)
        if len(tasklist) > 200:
            reduced_tasklist=list(tasklist)
            reduced_tasklist.sort()
            reduced_tasklist.reverse()
            reduced_tasklist=reduced_tasklist[0:200]
            tasklist=set(reduced_tasklist)
        if prev_tasklist:
            failureset=tasklist & prev_tasklist
            tasklist=tasklist-failureset
            logger.info("%d previously failed images will not be processed this iteration." % len(failureset))
        t1=time()
        logger.info("Constructed task list in %d seconds." % (t1-t0))
        logger.info("Image counts: %d total images, %d done images, %d rejected images, and %d images marked for reprocessing." % (len(all_images), len(done_images), len(rejected_images), len(reprocess_images)))
        if tasklist:
            pipeline_t0=time()
            futures=[]
            with executor.batch():
                for imageid in tasklist:
                    future = executor.submit(pipeline, imageid, args, jobmetadata)
                    futures.append(future)
            future_complete_counter=0
            throughput_t0=time()
            future_complete_counter=0
            while future_complete_counter != len(futures):
                future_complete_counter = sum(f.done() for f in futures)
                if future_complete_counter % 100 == 0:
                    throughput_t1=time()
                    done_images=retrieveDoneImages()
                    images_processed_total=len(done_images) - (len(all_images) - len(tasklist))
                    throughput=(images_processed_total)/(((throughput_t1-throughput_t0))/60.)
                    remaining_image_count=len(tasklist)-images_processed_total
                    logger.info("Progress: %d / %d images processed." % (images_processed_total, len(tasklist)))
                    logger.info("Throughput: %.2f images/min." % throughput)
                    if throughput > 0.0:
                        logger.info("Estimated remaining time: %.2f min." % (remaining_image_count/throughput))
                    else:
                        logger.info("Estimated remaining time: N/A min.")
                sleep(10)
            pipeline_t1=time()
            logger.info("Finished processing %d images in %d seconds." % (len(tasklist), (pipeline_t1-pipeline_t0)))
            prev_tasklist=tasklist
        else:
            logger.info(f"No new images.  Waiting {waitTime} seconds.")
            sleep(waitTime)
            if prev_tasklist:
                failure_waits+=1
                if failure_waits >= failure_cooldown:
                    prev_tasklist=set()
                    failure_waits=0
