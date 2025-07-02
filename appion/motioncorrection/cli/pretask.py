def preTask(imageid, args):
    # Sinedon needs to be reimported and setup within the local scope of this function
    # because the function runs as a Dask task, which means that it is run in a forked process
    # that doesn't have Django initialized.
    import sinedon.setup
    sinedon.setup(args['projectid'])
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
            imgmetadata['gain_input']=readInputPath(gainmetadata['session_frame_path'],gainmetadata['image_filename'])
    logger.info("Constructing motion correction command arguments for %d." % imageid)
    input_path = readInputPath(imgmetadata['session_frame_path'],imgmetadata['image_filename'])
    if input_path is None:
        raise RuntimeError("Input file for %d does not exist." % imgmetadata["imageid"])
    kwargs=constructMotionCorKwargs(imgmetadata, args, input_path)
    saveDark(kwargs["Dark"], imgmetadata['camera_name'], imgmetadata['eer_frames'], imgmetadata["dark_input"], imgmetadata["dark_nframes"])
    if "FmIntFile" in kwargs.keys():
        saveFmIntFile(kwargs["FmIntFile"], imgmetadata['total_raw_frames'], args['rendered_frame_size'], kwargs["FmDose"] / args['rendered_frame_size'])
    if 'DefectMap' in kwargs.keys():
        defect_map=calcImageDefectMap(imgmetadata['bad_rows'], imgmetadata['bad_cols'], imgmetadata['bad_pixels'], imgmetadata['dx'], imgmetadata['dy'])
        saveDefectMrc(kwargs['DefectMap'], defect_map, imgmetadata['frame_flip'], imgmetadata['frame_rotate'])
    return kwargs, imgmetadata