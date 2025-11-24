def preTask(imageid, args):
    import logging, sys
    from .constructors import constructMotionCorKwargs
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
    kwargs=constructMotionCorKwargs(imgmetadata, args, input_path)
    return kwargs, imgmetadata
