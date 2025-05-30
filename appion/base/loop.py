from dask.distributed import Client, wait
from distributed.deploy import Cluster
from time import sleep
import logging
import sys
from signal import signal, SIGINT, SIGTERM, SIGCONT, Signals
from base.calc import filterImages

# Parameters passed in using lambdas.
def loop(pipeline, args: dict, cluster : Cluster, checkpoint_path : str, retries : int = 3) -> None:
    # Signal handler used to ensure that cleanup happens if SIGINT, SIGCONT or SIGTERM is received.
    def handler(signum, frame):
        signame = Signals(signum).name
        logger.info(f"Received {signame} signal.  Cleaning up and exiting now.")
        try:
            cluster.close()
            logger.info("Server has exited cleanly.  Bye!")
        except SystemExit:
            logger.debug("Function lower on the stack has received exited midway.")
        except:
            logger.exception("Exception occurred while server was trying to exit cleanly.", stack_info=True)
            sys.exit(1)
        sys.exit(0)

    # Set up logging
    logger=logging.getLogger()
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

    while True:
        done=reloadCheckpoint(checkpoint_path)
        tasklist=filterImages()
        if tasklist:
            futures=pipeline(tasklist, args, client)
            wait(futures)
        else:
            sleep(30)