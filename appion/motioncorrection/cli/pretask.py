def preTask(imageid, args):
    # Sinedon needs to be reimported and setup within the local scope of this function
    # because the function runs as a Dask task, which means that it is run in a forked process
    # that doesn't have Django initialized.
    import sinedon.setup
    sinedon.setup(args['projectid'])
    import logging
    from .constructors import constructMotionCorKwargs
    from ..retrieve.params import readInputPath, readImageMetadata
    logger=logging.getLogger(__name__)
    logger.info("Gathering image metadata for %d." % imageid)
    imgmetadata=readImageMetadata(imageid, False, args["align"], False)
    if 'refimgid' in args.keys():
        if args['refimgid']:
            logger.info("Updating gain metadata for %d." % imageid)
            gainmetadata=readImageMetadata(args['refimgid'], False, args["align"], False)
            imgmetadata['gain_input']=readInputPath(gainmetadata['session_frame_path'],gainmetadata['image_filename'])
    logger.info("Constructing motion correction command arguments for %d." % imageid)
    kwargs=constructMotionCorKwargs(imgmetadata, args)
    return kwargs, imgmetadata