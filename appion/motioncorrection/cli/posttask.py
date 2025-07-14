
def postTask(imageid, kwargs, imgmetadata, jobmetadata, args, logData, logStdOut):
    # Sinedon needs to be reimported and setup within the local scope of this function
    # because the function runs as a Dask task, which means that it is run in a forked process
    # that doesn't have Django initialized.
    import sinedon.setup
    sinedon.setup(args['projectid'])
    import os, sys
    import logging
    from ..calc.internal import calcTotalFrames, filterFrameList, calcMotionCorrLogPath, calcMotionCor2LogPath, calcTotalRenderedFrames
    from ..store import saveFrameTrajectory, constructAlignedCamera, constructAlignedPresets, constructAlignedImage, uploadAlignedImage, saveDDStackParamsData, saveMotionCorrLog
    logger=logging.getLogger(__name__)
    logHandler=logging.StreamHandler(sys.stdout)
    logFormatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(process)d - %(message)s")
    logHandler.setFormatter(logFormatter)
    logger.setLevel("INFO")
    logHandler.setLevel("INFO")
    logger.addHandler(logHandler)
    shifts=[]
    # Find way to not calculate these twice?
    framelist=filterFrameList(kwargs["PixSize"], imgmetadata['nframes'], shifts)
    nframes=calcTotalFrames(imgmetadata['camera_name'], imgmetadata['exposure_time'], imgmetadata['frame_time'], imgmetadata['nframes'], imgmetadata['eer_frames'])
    if "Trim" in kwargs.keys():
        trim=kwargs["Trim"]
    else:
        trim=0
    aligned_camera_id = constructAlignedCamera(imgmetadata['camera_id'], args['square'], args['bin'], trim, framelist, nframes)
    aligned_preset_id = constructAlignedPresets(imgmetadata['preset_id'], aligned_camera_id, alignlabel=args['alignlabel'])
    aligned_image_filename = imgmetadata['image_filename']+"-%s" % args['alignlabel']
    aligned_image_mrc_image = aligned_image_filename + ".mrc"
    if not os.path.exists(imgmetadata["session_image_path"]):
        raise RuntimeError("Session path does not exist at %s." % imgmetadata["session_image_path"])
    abs_path_aligned_image_mrc_image=os.path.join(imgmetadata["session_image_path"],aligned_image_mrc_image)
    if os.path.lexists(abs_path_aligned_image_mrc_image):
        os.unlink(abs_path_aligned_image_mrc_image)
    try:
        os.link(kwargs["OutMrc"], abs_path_aligned_image_mrc_image)
    except OSError:
        os.symlink(kwargs["OutMrc"], abs_path_aligned_image_mrc_image)
    logger.info("%s linked to %s." % (abs_path_aligned_image_mrc_image, kwargs["OutMrc"]))
    logger.info("Constructing aligned image record for %d." % imageid)
    aligned_image_id = constructAlignedImage(imageid, aligned_preset_id, aligned_camera_id, aligned_image_mrc_image, aligned_image_filename)
    logger.info("Uploading aligned image record for %d." % imageid)
    uploadAlignedImage(imageid, aligned_image_id, jobmetadata['ref_apddstackrundata_ddstackrun'], logData["shifts"], kwargs["PixSize"], False)
    aligned_preset_dw_id = constructAlignedPresets(imgmetadata['preset_id'], aligned_camera_id, alignlabel=args['alignlabel']+"-DW")
    aligned_image_dw_filename = imgmetadata['image_filename']+"-%s-DW" % args['alignlabel']
    aligned_image_dw_mrc_image = aligned_image_dw_filename + ".mrc"
    abs_path_aligned_image_dw_mrc_image = os.path.join(imgmetadata["session_image_path"],aligned_image_dw_mrc_image)
    outmrc_dw=kwargs["OutMrc"].replace(".mrc","_DW.mrc")
    outmrc_dws=kwargs["OutMrc"].replace(".mrc","_DWS.mrc")
    if os.path.lexists(abs_path_aligned_image_dw_mrc_image):
        os.unlink(abs_path_aligned_image_dw_mrc_image)
    try:
        os.link(outmrc_dw, abs_path_aligned_image_dw_mrc_image)
    except OSError:
        os.symlink(outmrc_dw, abs_path_aligned_image_dw_mrc_image)
    logger.info("%s linked to %s." % (abs_path_aligned_image_dw_mrc_image, kwargs["OutMrc"].replace(".mrc","_DW.mrc")))
    logger.info("Constructing aligned, dose-weighted image record for %d." % imageid)
    aligned_image_dw_id = constructAlignedImage(imageid, aligned_preset_dw_id, aligned_camera_id, aligned_image_dw_mrc_image, aligned_image_dw_filename)
    # Frame trajectory only saved for aligned_image_id: https://github.com/nysbc/appion-slurm/blob/814544a7fee69ba7121e7eb1dd3c8b63bc4bb75a/appion/appionlib/apDDLoop.py#L89-L107
    trajdata_id=saveFrameTrajectory(aligned_image_id, jobmetadata['ref_apddstackrundata_ddstackrun'], logData["shifts"])
    logger.info("Uploading aligned, dose-weighted image record for %d." % imageid)
    uploadAlignedImage(imageid, aligned_image_dw_id, jobmetadata['ref_apddstackrundata_ddstackrun'], logData["shifts"], kwargs["PixSize"], True, trajdata_id)
    # This is only used by manualpicker.py so it can go away.  Just making a note of it in a commit for future me / someone.
    #saveApAssessmentRunData(imgmetadata['session_id'], assessment)
    # Seems mostly unused?  Might have been used with a prior implementation of motion correction?  Fields seem to mostly be filled with nulls in the MEMC database.
    saveDDStackParamsData(args['preset'], args['align'], args['bin'], None, None, None, None)
    #saveDDStackParamsData(args['preset'], args['align'], args['bin'], ref_apddstackrundata_unaligned_ddstackrun, method, ref_apstackdata_stack, ref_apdealignerparamsdata_de_aligner)
    
    # Is this really the right/best way to determine the framestack path?  It works for our purposes ( I think )
    # but the original codebase has more elaborate logic that works for both aligned and unaligned images:
    # https://github.com/nysbc/appion-slurm/blob/814544a7fee69ba7121e7eb1dd3c8b63bc4bb75a/appion/appionlib/apDDprocess.py#L104-L123
    # Not sure that really is necessary for what we're trying to achieve in the immediate future.
    if 'InMrc' in kwargs.keys():
        framestackpath=kwargs['InMrc']
    elif 'InTiff' in kwargs.keys():
        framestackpath=kwargs['InTiff']
    elif 'InEer' in kwargs.keys():
        framestackpath=kwargs['InEer']
    # These need to go in the Appion directory / working directory.
    framestackpath=os.path.join(args["rundir"],os.path.basename(framestackpath))

    motioncor2_log_path=calcMotionCor2LogPath(framestackpath)
    logger.info("Saving out motioncor2-formatted log for %d to %s." % (imageid, motioncor2_log_path))
    with open(motioncor2_log_path, "w") as f:
        f.write(logStdOut)

    motioncorr_log_path=calcMotionCorrLogPath(framestackpath)
    logger.info("Saving out motioncorr-formatted log for %d to %s." % (imageid, motioncorr_log_path))
    saveMotionCorrLog(logData, motioncorr_log_path, args['startframe'], calcTotalRenderedFrames(imgmetadata['total_raw_frames'], args['rendered_frame_size']), args['bin'])

    if args["clean"]:
        if os.path.exists(kwargs["Dark"]):
            os.remove(kwargs["Dark"])
        # Don't remove if symbolic links were used instead of hard links
        if not os.path.islink(abs_path_aligned_image_mrc_image):
            if os.path.exists(kwargs["OutMrc"]):
                os.remove(kwargs["OutMrc"])
        if not os.path.islink(abs_path_aligned_image_dw_mrc_image):
            if os.path.exists(outmrc_dw):
                os.remove(outmrc_dw)
        if os.path.exists(outmrc_dws):
            os.remove(outmrc_dws)