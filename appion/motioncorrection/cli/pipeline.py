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
    batches=preTask(tasklist, args, batch_size)
    posttask_kwargs=task(batches, args, batch_size)
    for kw in posttask_kwargs:    
        postTask(kw["imageid"], kw["kwargs"], kw["imgmetadata"], jobmetadata, args, kw["logData"], kw["logStdOut"])

def task(batches, args, batch_size):
    from ..calc.internal import optimized_motioncor
    from ...base.loop import futures_wait
    cpu_count=batch_size+2
    executor = submitit.AutoExecutor(folder=os.path.join(args["rundir"], "working"))
    executor.update_parameters(timeout_min=6, slurm_partition="appion-motioncorrection", slurm_gres="gpu:1", slurm_cpus_per_task=cpu_count, slurm_array_parallelism=32)
    futures=[]
    with executor.batch():
        for batch in batches:
            future = executor.submit(optimized_motioncor, [img["kwargs"] for img in batch], cpu_count)
            futures.append(future)
    futures_wait(futures)
    posttask_kwargs=[]
    for batch_idx, batch in enumerate(batches):
        results=futures[batch_idx].result()
        for img_input_idx, img_input in enumerate(batch):
            img_posttask_kwargs={}
            img_posttask_kwargs["imageid"]=img_input["imgmetadata"]['imgdata']["def_id"]
            img_posttask_kwargs["kwargs"]=img_input["kwargs"]
            img_posttask_kwargs["imgmetadata"]=img_input["imgmetadata"]
            img_posttask_kwargs["logData"]=results[img_input_idx][0]
            img_posttask_kwargs["logStdOut"]=results[img_input_idx][1]
            posttask_kwargs.append(img_posttask_kwargs)
    return posttask_kwargs
