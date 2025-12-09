import submitit
import os
from .pretask import preTask
from .posttask import postTask

# def pipeline(batchid: int, imageids: int, args : dict, jobmetadata: dict):
#     # Sinedon needs to be reimported and setup within the local scope of this function
#     # because the function runs in a forked process
#     # that doesn't have Django initialized.
#     import sinedon.setup
#     sinedon.setup(args['projectid'], False)
#     from .pretask import preTask
#     from ..calc.external import motioncor, checkImageExists
#     from .posttask import postTask
#     import os
#     image_pretask_results={}
#     batchdir=os.path.join(args["run_dir"],"batch-%d" % batchid)
#     if not os.path.isdir(batchdir):
#         os.makedirs(batchdir)
#     for imageid in imageids:
#         if checkImageExists(imageid):
#             kwargs, imgmetadata=preTask(imageid, args)
#             image_pretask_results[imageid]={}
#             image_pretask_results[imageid]['kwargs']=kwargs
#             image_pretask_results[imageid]['imgmetadata']=imgmetadata
#     kwargs, image_pretask_results=construct_serial_kwargs(image_pretask_results, args, batchdir)
#     logData, logStdOut=motioncor(**kwargs)
#     for imageid in image_pretask_results.keys():
#         postTask(imageid, image_pretask_results[imageid]['kwargs'], image_pretask_results[imageid]['imgmetadata'], jobmetadata, args, logData, logStdOut)

def pipeline(tasklist, args, jobmetadata, batch_size : int = 1):
    from ...base.loop import futures_wait
    batches=preTask(tasklist, args, batch_size)
    futures=task(batches, args, batch_size)
    futures_wait(futures)
    for idx, batch in enumerate(batches):
        logData, logStdOut = futures[idx].result()
        postTask(batch["imgmetadata"]['imgdata']["def_id"], batch["kwargs"], batch["imgmetadata"], jobmetadata, args, logData, logStdOut)

def task(batches, args, batch_size):
    from ..calc.internal import optimized_motioncor
    cpu_count=batch_size+2
    executor = submitit.AutoExecutor(folder=os.path.join(args["rundir"], "working"))
    executor.update_parameters(timeout_min=6, slurm_partition="appion-motioncorrection", slurm_gres="gpu:1", slurm_cpus_per_task=cpu_count, slurm_array_parallelism=32)
    futures=[]
    with executor.batch():
        for batch in batches:
            future = executor.submit(optimized_motioncor, [img["kwargs"] for img in batch], cpu_count)
            futures.append(future)
    return futures
