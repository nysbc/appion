def preTask(imageid, args):
    import logging, sys
    from .constructors import constructMotionCorKwargs
    from ..retrieve.params import readInputPath, readImageMetadata
    from ..calc.internal import calcImageDefectMap
    from ..store import saveDefectMrc, saveDark, saveFmIntFile
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
    kwargs=constructMotionCorKwargs(imgmetadata, args, input_path)
    saveDark(kwargs["Dark"], imgmetadata["ccdcamera"]['name'], imgmetadata['cameraemdata']['eer_frames'], imgmetadata["dark_input"], imgmetadata['darkmetadata']['cameraemdata']["nframes"])
    if "FmIntFile" in kwargs.keys():
        saveFmIntFile(kwargs["FmIntFile"], imgmetadata['cameraemdata']['nframes'], args['rendered_frame_size'], kwargs["FmDose"] / args['rendered_frame_size'])
    if 'DefectMap' in kwargs.keys():
        defect_map=calcImageDefectMap(imgmetadata["correctorplandata"]['bad_rows'], 
                                      imgmetadata["correctorplandata"]['bad_cols'], 
                                      imgmetadata["correctorplandata"]['bad_pixels'], 
                                      imgmetadata['cameraemdata']["subd_dimension_x"], 
                                      imgmetadata['cameraemdata']["subd_dimension_y"], 
                                      imgmetadata['cameraemdata']['frame_flip'], 
                                      imgmetadata['cameraemdata']['frame_rotate'])
        saveDefectMrc(kwargs['DefectMap'], defect_map)
    return kwargs, imgmetadata
