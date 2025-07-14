from dask.distributed import Client, as_completed
from distributed.deploy import Cluster
from time import sleep, time
import logging
import sys
from signal import signal, SIGINT, SIGTERM, SIGCONT, Signals
from .retrieve import readImageSet, retrieveRejectedImages
from .calc import filterImages
from typing import Callable

# Parameters passed in using lambdas.
def loop(pipeline, args: dict, cluster : Cluster, retrieveDoneImages : Callable = lambda : set(), preLoop : Callable = lambda args : {}, postLoop : Callable = lambda jobmetadata : None, retrieveReprocessImages : Callable = lambda : set(), max_workers : int = 32) -> None:
    jobmetadata={}
    # Signal handler used to ensure that cleanup happens if SIGINT, SIGCONT or SIGTERM is received.
    def handler(signum, frame):
        signame = Signals(signum).name
        logger.info(f"Received {signame} signal.  Cleaning up and exiting now.")
        try:
            cluster.close()
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
    distributed_scheduler_logger=logging.getLogger("distributed.scheduler")
    logHandler=logging.StreamHandler(sys.stdout)
    logFormatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(process)d - %(message)s")
    logHandler.setFormatter(logFormatter)
    logger.setLevel("INFO")
    logHandler.setLevel("INFO")
    logger.addHandler(logHandler)
    distributed_scheduler_logger.addHandler(logHandler)

    # Set up the control loop and signal handlers.
    signal(SIGTERM, handler)
    signal(SIGINT, handler)
    signal(SIGCONT, handler)
    client = Client(cluster)

    jobmetadata=preLoop()
    waitTime=30
    prev_tasklist=set()
    failure_cooldown=10
    failure_waits=0
    while True:
        t0=time()
        all_images=readImageSet(args["sessionname"], args["preset"])
        done_images=retrieveDoneImages()
        rejected_images=retrieveRejectedImages(all_images, args["sessionname"], None, None, args["tiltangle"])
        # Not used by motioncor2; used by ctffind4
        reprocess_images=retrieveReprocessImages()
        tasklist=filterImages(all_images, done_images, reprocess_images, rejected_images)
        if prev_tasklist:
            failureset=tasklist & prev_tasklist
            tasklist=tasklist-failureset
            logger.info("%d previously failed images will not be processed this iteration." % len(failureset))
        t1=time()
        logger.info("Constructed task list in %d seconds." % (t1-t0))
        logger.info("Image counts: %d total images, %d done images, %d rejected images, and %d images marked for reprocessing." % (len(all_images), len(done_images), len(rejected_images), len(reprocess_images)))
        node_count=min(max_workers,len(tasklist))
        logger.info("Scaling up to %d nodes." % node_count)
        cluster.scale(node_count)
        if tasklist:
            pipeline_t0=time()
            futures=pipeline(tasklist, args, jobmetadata, client)
            future_complete_counter=0
            images_processed_total_t0=0
            throughput_t0=time()
            for _ in as_completed(futures):
                future_complete_counter+=1
                if future_complete_counter % 100 == 0:
                    throughput_t1=time()
                    done_images=retrieveDoneImages()
                    images_processed_total=len(done_images) - (len(all_images) - len(tasklist))
                    images_processed_t1=images_processed_total-images_processed_total_t0
                    throughput=(images_processed_t1)/(((throughput_t1-throughput_t0))/60.)
                    remaining_image_count=len(tasklist)-images_processed_total
                    logger.info("Progress: %d / %d images processed." % (images_processed_total, len(tasklist)))
                    logger.info("Throughput: %.2f images/min." % throughput)
                    if throughput > 0.0:
                        logger.info("Estimated remaining time: %.2f min." % (remaining_image_count/throughput))
                    else:
                        logger.info("Estimated remaining time: N/A min.")
                    throughput_t0=time()
                    images_processed_total_t0=images_processed_total
            pipeline_t1=time()
            logger.info("Finished processing %d images in %d seconds." % (len(tasklist), (pipeline_t1-pipeline_t0)))
            # Explicitly cancel all futures to prevent dask distributed from recalculating already calculated futures.
            # Possibly unnecessary.
            # See https://github.com/nysbc/appion/issues/17
            logger.debug("Cancelling all futures.")
            for f in futures:
                f.cancel()
            # This is here to accommodate an edge case where a scale down event isn't triggered when processing a very
            # small number of images.
            logger.info("Removing all nodes.")
            cluster.scale(0)
            logger.debug("Futures cancelled.")
            prev_tasklist=tasklist
        else:
            logger.info(f"No new images.  Waiting {waitTime} seconds.")
            sleep(waitTime)
            if prev_tasklist:
                failure_waits+=1
                if failure_waits >= failure_cooldown:
                    prev_tasklist=set()
                    failure_waits=0