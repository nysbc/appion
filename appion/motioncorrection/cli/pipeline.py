import os
from fcntl import flock, LOCK_EX, LOCK_UN
from dask.distributed import Client
import dask
from .pretask import preTask
from ..calc.external import motioncor, checkImageExists
from .posttask import postTask

def warmpagecache_motioncor(kwargs : dict):
    ondisk_keys=["Gain", "Dark", "DefectMap", "FmIntFile", "InMrc", "InTiff", "InEer"]
    for k in ondisk_keys:
        if k in kwargs.keys():
            if os.path.exists(kwargs[k]):
                with open(kwargs[k], "rb") as f:
                    f.read()

def sliced_motioncor(kwargs : dict):
    warmpagecache_motioncor(kwargs)
    jobid=os.environ.get("SLURM_JOB_ID",None)
    lockfile_path=os.path.join("/tmp", "%s.lock" % jobid)
    if jobid:
        with open(lockfile_path, "r") as f:
            flock(f, LOCK_EX)
            motioncor(**kwargs)
            flock(f, LOCK_UN)
    else:
        raise RuntimeError("Could not determine Slurm job ID for motioncor time-slicing.")

def pipeline(tasklist: list, args : dict, jobmetadata: dict, client : Client, retries : int = 0):
    # Sets the prior for tracking task duration to 30s so that adaptive scaling
    # is more accurate (30s is estimated time to run a typical motioncor2 job).
    dask.config.set({"distributed.scheduler.unknown-task-duration":"30s"})
    futures=[]
    for imageid in tasklist:
        if checkImageExists(imageid):
            pretask_f=client.submit(preTask, imageid, args, pure=True, retries=retries, resources={"MEMORY" : 16})
            futures.append(pretask_f)

            # We give these lambdas names because Dask keeps track of function runtimes with a dict mapping
            # task keys to average durations.  Task keys == function names by default.
            # See (State --> task_duration): https://docs.dask.org/en/latest/deploying-python-advanced.html#id2
            # and ('key' param) https://docs.dask.org/en/stable/futures.html#distributed.Client.submit
            motioncor_lambda = lambda pretask_data : sliced_motioncor(pretask_data[0])
            task_f=client.submit(motioncor_lambda, pretask_f, pure=True, retries=retries, resources={'GPU': 1, "MEMORY" : 64})
            futures.append(task_f)

            postTask_lambda = lambda pretask_data, task_data : postTask(imageid, pretask_data[0], pretask_data[1], jobmetadata, args, task_data[0], task_data[1])
            posttask_f=client.submit(postTask_lambda, pretask_f, task_f, pure=True, retries=retries, resources={"MEMORY" : 16})
            futures.append(posttask_f)
    return futures
