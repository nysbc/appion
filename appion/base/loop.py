from time import sleep, time
import logging
import sys
from signal import signal, SIGINT, SIGTERM, SIGCONT, Signals
from .retrieve import readImageSet, retrieveRejectedImages
from .calc import filterImages
from typing import Callable

# Parameters passed in using lambdas.
def loop(args: dict, pipeline:  Callable = lambda tasklist, args : {}, retrieveDoneImages : Callable = lambda : set(), preLoop : Callable = lambda args : {}, 
        postLoop : Callable = lambda jobmetadata : None, retrieveReprocessImages : Callable = lambda : set(), tasklimit: int = 200) -> None:
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
            logger.debug("Function lower on the stack has exited midway.")
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

    while True:
        t0=time()
        all_images=readImageSet(args["sessionname"], args["preset"])
        done_images=retrieveDoneImages()
        rejected_images=retrieveRejectedImages(all_images, args["sessionname"], None, None, args["tiltangle"])
        # Not used by motioncor2; used by ctffind4
        reprocess_images=retrieveReprocessImages()
        taskset=filterImages(all_images, done_images, reprocess_images, rejected_images)      
        if prev_taskset:
            failureset=taskset & prev_taskset
            taskset=taskset-failureset
            logger.info("%d previously failed images will not be processed this iteration." % len(failureset))
        tasklist=list(taskset)
        tasklist.sort()
        tasklist.reverse() 
        tasklist=tasklist[0:tasklimit]
        t1=time()
        logger.info("Constructed task list in %d seconds." % (t1-t0))
        logger.info("Image counts: %d total images, %d done images, %d rejected images, and %d images marked for reprocessing." % (len(all_images), len(done_images), len(rejected_images), len(reprocess_images)))
        if tasklist:
            pipeline_t0=time()
            pipeline(tasklist, jobmetadata)
            pipeline_t1=time()
            logger.info("Finished processing %d images in %d seconds." % (len(tasklist), (pipeline_t1-pipeline_t0)))
            prev_taskset=taskset
        else:
            logger.info(f"No new images.  Waiting {waitTime} seconds.")
            sleep(waitTime)
            if prev_taskset:
                failure_waits+=1
                if failure_waits >= failure_cooldown:
                    prev_taskset=set()
                    failure_waits=0

def futures_wait(futures : list, log_prefix : str = "Generic", step : int = 20):
    throughput_t0=time()
    logger=logging.getLogger(__name__)
    future_complete_counter=0
    total_future_count=len(futures)
    future_progress_counter=0
    while future_complete_counter != len(futures) and len(futures) != 0:
        future_complete_counter = sum(f.done() for f in futures)
        if future_complete_counter > future_progress_counter and future_complete_counter != 0:
            throughput_t1=time()
            throughput=(future_complete_counter)/(((throughput_t1-throughput_t0))/60.)
            remaining_future_count=total_future_count-future_complete_counter
            logger.info("[%s] Progress: %d / %d futures processed." % (log_prefix, future_complete_counter, total_future_count))
            logger.info("[%s] Throughput: %.2f futures/min." % (log_prefix, throughput))
            if throughput > 0.0:
                logger.info("[%s] Estimated remaining time: %.2f min." % (log_prefix, (remaining_future_count/throughput)))
            else:
                logger.info("[%s] Estimated remaining time: N/A min." % log_prefix)
            future_progress_counter+=step
        sleep(10)
