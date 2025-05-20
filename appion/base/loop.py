from dask.distributed import Client, wait
from distributed.deploy import Cluster
from time import sleep
import logging
import sys
from signal import signal, SIGINT, SIGTERM, SIGCONT, Signals

# Parameters passed in using lambdas.
def loop(updateTaskList : function, preTask: function, task: function, postTask : function, checkpoint : function, cluster : Cluster, retries : int = 3) -> None:
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
        tasklist=updateTaskList()
        if tasklist:
            pre_task_futures = client.map(tasklist, preTask, retries=retries, pure=False)
            task_futures = client.map(pre_task_futures, task, retries=retries, pure=False)
            post_task_futures = client.map(task_futures, postTask, retries=retries, pure=False)
            checkpoint_futures = client.map(post_task_futures, checkpoint, retries=retries, pure=False)
            wait(pre_task_futures + task_futures + post_task_futures + checkpoint_futures)
        else:
            sleep(30)