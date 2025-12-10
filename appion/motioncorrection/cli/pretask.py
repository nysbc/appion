import os
import submitit

def preTask(tasklist, args, batch_size):
    from ..calc.internal import calcImageDefectMap
    from ..store import saveDefectMrc, saveDark, saveFmIntFile
    from .constructors import constructMotionCorKwargs
    futures=[]
    executor = submitit.AutoExecutor(folder=os.path.join(args["rundir"], "working"))
    executor.update_parameters(timeout_min=6, slurm_partition="appion-motioncorrection", slurm_cpus_per_task=batch_size*2, slurm_array_parallelism=32)
    with executor.batch():
        for imageid in tasklist:
            future = executor.submit(preTaskMap, imageid, args)
            futures.append(future)
    map_outputs=[future.result() for future in futures]
    merged_imgmetadata=preTaskReduce(map_outputs)
    batches=[]
    for ref_uuid in merged_imgmetadata.keys():
        input_count=len(merged_imgmetadata[ref_uuid]["inputs"])
        imgmetadata=merged_imgmetadata[ref_uuid]["imgmetadata"]
        for idx in range(0, input_count, batch_size):
            batch=[]
            if idx + batch_size >= input_count:
                input_paths=merged_imgmetadata[ref_uuid]["inputs"][idx:]
            else:
                input_paths=merged_imgmetadata[ref_uuid]["inputs"][idx:batch_size]
            for input_path in input_paths:
                img_input={}
                kwargs=constructMotionCorKwargs(imgmetadata, args, input_path)
                if not os.path.exists(kwargs["Dark"]):
                    saveDark(kwargs["Dark"], imgmetadata["ccdcamera"]['name'], imgmetadata['cameraemdata']['eer_frames'], imgmetadata["dark_input"], imgmetadata['darkmetadata']['cameraemdata']["nframes"])
                if "FmIntFile" in kwargs.keys():
                    if not os.path.exists(kwargs["FmIntFile"]):
                        saveFmIntFile(kwargs["FmIntFile"], imgmetadata['cameraemdata']['nframes'], args['rendered_frame_size'], kwargs["FmDose"] / args['rendered_frame_size'])
                if 'DefectMap' in kwargs.keys():
                    if not os.path.exists(kwargs['DefectMap']):
                        defect_map=calcImageDefectMap(imgmetadata["correctorplandata"]['bad_rows'], 
                                                    imgmetadata["correctorplandata"]['bad_cols'], 
                                                    imgmetadata["correctorplandata"]['bad_pixels'], 
                                                    imgmetadata['cameraemdata']["subd_dimension_x"], 
                                                    imgmetadata['cameraemdata']["subd_dimension_y"], 
                                                    imgmetadata['cameraemdata']['frame_flip'], 
                                                    imgmetadata['cameraemdata']['frame_rotate'])
                        saveDefectMrc(kwargs['DefectMap'], defect_map)
                img_input["kwargs"]=kwargs
                img_input["imgmetadata"]=imgmetadata
                batch.append(img_input)
            batches.append(batch)
    return batches

def preTaskMap(imageid, args):
    import logging, sys
    import sinedon.setup
    sinedon.setup(args["projectid"])
    from ..retrieve.params import readInputPath, readImageMetadata
    logger=logging.getLogger(__name__)
    logHandler=logging.StreamHandler(sys.stdout)
    logFormatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(process)d - %(message)s")
    logHandler.setFormatter(logFormatter)
    logger.setLevel("INFO")
    logHandler.setLevel("INFO")
    logger.addHandler(logHandler)
    logger.info("Gathering image metadata for %d." % imageid)
    imgmetadata=readImageMetadata(imageid, False, args["align"], False)
    if 'refimgid' in args.keys():
        if args['refimgid']:
            logger.info("Updating gain metadata for %d." % imageid)
            gainmetadata=readImageMetadata(args['refimgid'], False, args["align"], False)
            imgmetadata['gain_input']=readInputPath(gainmetadata['sessiondata']["frame_path"],gainmetadata['imgdata']['filename'])
    logger.info("Constructing motion correction command arguments for %d." % imageid)
    input_path = readInputPath(imgmetadata['sessiondata']['frame_path'],imgmetadata['imgdata']['filename'])
    if input_path is None:
        raise RuntimeError("Input file for %d does not exist." % imgmetadata["imgdata"]["def_id"])
    return imgmetadata, input_path

def preTaskReduce(map_outputs):
    merged_imgmetadata={}
    for imgmetadata, input_path in map_outputs:
        ref_uuid=imgmetadata["ref_uuid"]
        if ref_uuid not in merged_imgmetadata.keys():
            merged_imgmetadata[ref_uuid]={}
            merged_imgmetadata[ref_uuid]["imgmetadata"]=imgmetadata
            merged_imgmetadata[ref_uuid]["inputs"]=[input_path]
        else:
            merged_imgmetadata[ref_uuid]["inputs"].append(input_path)
    return merged_imgmetadata
