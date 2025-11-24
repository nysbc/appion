
def pipeline(imageids: int, args : dict, jobmetadata: dict):
    # Sinedon needs to be reimported and setup within the local scope of this function
    # because the function runs as a Dask task, which means that it is run in a forked process
    # that doesn't have Django initialized.
    import sinedon.setup
    sinedon.setup(args['projectid'], False)
    from .pretask import preTask
    from ..calc.external import motioncor, checkImageExists
    from .posttask import postTask
    for imageid in imageids:
        if checkImageExists(imageid):
            kwargs, imgmetadata=preTask(imageid, args)
            logData, logStdOut=motioncor(**kwargs)
            postTask(imageid, kwargs, imgmetadata, jobmetadata, args, logData, logStdOut)
