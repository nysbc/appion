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
def loop(pipeline, args: dict, cluster : Cluster, retrieveDoneImages : Callable = lambda : set(), preLoop : Callable = lambda args : {}, postLoop : Callable = lambda jobmetadata : None, retrieveReprocessImages : Callable = lambda : set()) -> None:
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
    while True:
        t0=time()
        all_images=readImageSet(args["sessionname"], args["preset"])
        done_images=retrieveDoneImages()
        rejected_images=retrieveRejectedImages(all_images, args["sessionname"], None, None, args["tiltangle"])
        # Not used by motioncor2; used by ctffind4
        reprocess_images=retrieveReprocessImages()
        tasklist=filterImages(all_images, done_images, reprocess_images, rejected_images)
        t1=time()
        logger.info("Constructed task list in %d seconds." % (t1-t0))
        logger.info("Image counts: %d total images, %d done images, %d rejected images, and %d images marked for reprocessing." % (len(all_images), len(done_images), len(rejected_images), len(reprocess_images)))
        if tasklist:
            pipeline_t0=time()
            futures=pipeline(tasklist, args, jobmetadata, client)
            future_complete_counter=0
            images_processed_t0=0
            throughput_t0=time()
            for _ in as_completed(futures):
                future_complete_counter+=1
                if future_complete_counter % 100 == 0:
                    throughput_t1=time()
                    done_images=retrieveDoneImages()
                    images_processed_t1=len(done_images) - (len(all_images) - len(tasklist))
                    throughput=((images_processed_t1-images_processed_t0)/(throughput_t1-throughput_t0))/60.
                    remaining_image_count=len(tasklist)-images_processed_t1
                    logger.info("Progress: %d / %d images processed." % (images_processed_t1, len(tasklist)))
                    logger.info("Throughput: %.2d images/min." % throughput)
                    logger.info("Estimated remaining time: %.2d min." % (remaining_image_count/throughput))
                    throughput_t0=time()
                    images_processed_t0=images_processed_t1
            pipeline_t1=time()
            logger.info("Finished processing %d images in %d seconds." % (len(tasklist), (pipeline_t1-pipeline_t0)))
        else:
            logger.info(f"No new images.  Waiting {waitTime} seconds.")
            sleep(waitTime)