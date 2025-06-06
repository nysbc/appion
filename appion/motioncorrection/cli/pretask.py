def preTask(imageid, args):
    import sinedon.setup
    sinedon.setup(args['projectid'])
    from ..retrieve import readInputPath, readImageMetadata
    from .constructors import constructMotionCorKwargs
    imgmetadata=readImageMetadata(imageid, False, args["align"], False)
    if 'refimgid' in args.keys():
        gainmetadata=readImageMetadata(args['refimgid'], False, args["align"], False)
        imgmetadata['gain_input']=readInputPath(gainmetadata['session_frame_path'],gainmetadata['image_filename'])
    kwargs=constructMotionCorKwargs(imgmetadata, args)
    return kwargs, imgmetadata