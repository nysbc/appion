from dask.distributed import Client, as_completed
from distributed.deploy import Cluster
import logging
import sys
from signal import signal, SIGINT, SIGTERM, SIGCONT, Signals

# Parameters passed in using lambdas.
def loop(updateTaskList : function, preTask: function, task: function, postTask : function, checkpoint : function, cluster : Cluster) -> None:
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
        futures = []
        for t in tasklist:
            f_pre=client.submit(preTask, t)
            futures.append(f_pre)
            f_task=client.submit(task, f_pre)
            futures.append(f_task)
            f_post=client.submit(postTask, f_task)
            futures.append(f_post)
            f_checkpoint=client.submit(checkpoint, f_post)
            futures.append(f_checkpoint)
        for future, result in as_completed(futures, with_results=True):
            logger.info("Task has completed: %s" % str(result))