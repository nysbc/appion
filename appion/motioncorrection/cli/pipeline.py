from dask.distributed import Client
import dask
from .pretask import preTask
from ..calc.internal import motioncor_merge
from ..calc.external import motioncor, checkImageExists
from .posttask import postTask

def pipeline(tasklist: list, args : dict, jobmetadata: dict, client : Client, retries : int = 0):
    # Sets the prior for tracking task duration to 30s so that adaptive scaling
    # is more accurate (30s is estimated time to run a typical motioncor2 job).
    dask.config.set({"distributed.scheduler.unknown-task-duration":"30s"})
    pretask_futures=[]
    futures=[]
    for imageid in tasklist:
        if checkImageExists(imageid):
            pretask_f=client.submit(preTask, imageid, args, pure=True, retries=retries, resources={"MEMORY" : 16})
            pretask_futures.append(pretask_f)
    motioncor_merge_lambda = lambda command_kwargs : motioncor_merge([k[0] for k in command_kwargs], args['rundir'])
    merge_task_f=client.submit(motioncor_merge_lambda, *pretask_futures, pure=True, retries=retries, resources={'GPU': 1, "MEMORY" : 64})
    merged_tasks=merge_task_f.result()
    for merged_task_kwargs in merged_tasks:
        # We give these lambdas names because Dask keeps track of function runtimes with a dict mapping
        # task keys to average durations.  Task keys == function names by default.
        # See (State --> task_duration): https://docs.dask.org/en/latest/deploying-python-advanced.html#id2
        # and ('key' param) https://docs.dask.org/en/stable/futures.html#distributed.Client.submit
        motioncor_lambda = lambda merged_task_kwargs : motioncor(merged_task_kwargs)
        task_f=client.submit(motioncor_lambda, merged_task_kwargs, pure=True, retries=retries, resources={'GPU': 1, "MEMORY" : 64})
        futures.append(task_f)

    for pretask_f in pretask_futures:
        postTask_lambda = lambda pretask_data, task_data : postTask(imageid, pretask_data[0], pretask_data[1], jobmetadata, args, task_data[0], task_data[1])
        posttask_f=client.submit(postTask_lambda, pretask_f, task_f, pure=True, retries=retries, resources={"MEMORY" : 16})
        futures.append(posttask_f)
    return futures
