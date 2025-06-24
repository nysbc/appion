def preTask(imageid, args):
    # Sinedon needs to be reimported and setup within the local scope of this function
    # because the function runs as a Dask task, which means that it is run in a forked process
    # that doesn't have Django initialized.
    import sinedon.setup
    sinedon.setup(args['projectid'])
    from .constructors import constructMotionCorKwargs
    from ..retrieve.params import readInputPath, readImageMetadata
    imgmetadata=readImageMetadata(imageid, False, args["align"], False)
    if 'refimgid' in args.keys():
        if args['refimgid']:
            gainmetadata=readImageMetadata(args['refimgid'], False, args["align"], False)
            imgmetadata['gain_input']=readInputPath(gainmetadata['session_frame_path'],gainmetadata['image_filename'])
    kwargs=constructMotionCorKwargs(imgmetadata, args)
    return kwargs, imgmetadata