from dask.distributed import Client
from .pretask import preTask
from ..calc.external import motioncor
from .posttask import postTask

def pipeline(tasklist: list, args : dict, jobmetadata: dict, client : Client):
    futures=[]
    for imageid in tasklist:
        pretask_f=client.submit(preTask, imageid, args, pure=False)
        futures.append(pretask_f)

        task_f=client.submit(lambda pretask_data : motioncor(**pretask_data[0]), pretask_f, pure=False)
        futures.append(task_f)

        posttask_f=client.submit(lambda pretask_data, task_data : postTask(imageid, pretask_data[0], pretask_data[1], jobmetadata, args, task_data[0]), pretask_f, task_f, pure=False)
        futures.append(posttask_f)
    return futures