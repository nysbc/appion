def constructMotionCorKwargs(imgmetadata : dict, args : dict, input_path : str) -> dict:
    import os
    from ..calc.internal import calcInputType, calcFmDose, calcPixelSize, calcKV, calcTotalFrames, calcTrunc, calcRotFlipGain, filterFrameList
    # Keyword args for motioncor2 function
    kwargs={}

    if 'eer_sampling' in args.keys():
        kwargs['EerSampling'] = args['eer_sampling']
    if 'Patchrows' in args.keys() and 'Patchcols' in args.keys():
        kwargs["Patch"] = "%s %s" % (str(args["Patchcols"]), str(args["Patchrows"]))
    if 'Iter' in args.keys():
        kwargs["Iter"] = args["Iter"]
    if 'Tol' in args.keys():
        kwargs["Tol"] = args["Tol"]
    if 'Bft_global' in args.keys() and 'Bft_local' in args.keys():
        kwargs["Bft"] = "%d %d" % (args["Bft_global"], args["Bft_local"])
    if 'bin' in args.keys():
        if args["bin"] != 1.0:
            kwargs["FtBin"] = args["bin"]
    if 'startframe' in args.keys():
        kwargs["Throw"] = args["startframe"]
    if 'nrw' in args.keys():
        kwargs["Group"] = args["nrw"]
    # This flag doesn't seem to have been supported in motioncor2 since the 01-30-2017 version.
    #if 'MaskSizecols' in cli_args.keys() and 'MaskSizerows' in cli_args.keys():
    #    kwargs["MaskSize"] = "%d %d" % (cli_args["MaskSizecols"], cli_args["MaskSizerows"])
    if 'FmRef' in args.keys():
        if args["FmRef"] != 0:
            kwargs["FmRef"] = args["FmRef"]
    if 'gpuids' in args.keys():
        kwargs["Gpu"] = args["gpuids"]
# TODO Figure out how user input might interact with Trunc calculation
#| `-Trunc` | User Input / Calculated | `setAlignedSumFrameList`, `-nframe`, `-startframe`, `driftlimit`, `apix` | |
    if "totaldose" in args.keys():
        totaldose = args["totaldose"]
    else:
        totaldose = None

    # InMrc, InTiff, InEer
    # Get the path to the input image.
    inputType = calcInputType(input_path)
    kwargs[inputType] = input_path

    #OutMrc
    #Path to the aligned aligned/summed micrograph.
    kwargs['OutMrc'] = os.path.join(args['rundir'],imgmetadata['imgdata']['filename']+'_c.mrc')

    # Gain
    # Get the reference image
    if imgmetadata['gain_input']:
        kwargs["Gain"]=imgmetadata['gain_input']

    # TODO - what exactly is the bright reference?  It isn't passed as a param into motioncor2, but
    # Appion still prints out its path.  To what end / why?

    # Dark
    # The following line appeared in the original Appion, but it doesn't seem to have any function.
    # It creates an internal data structure that contains cached data that is queried from the database.
    # The use_full_raw_area parameter seems to be used to tell Appion to apply a corrector plan to the dark image,
    # but it never gets set to True as near as I can tell, and a False value always gets passed around from method
    # to method.
    # self.setCameraInfo(1,use_full_raw_area)
        
    # Get the dark image.  Create it if it does not exist.
    ccdcamera_id=0
    cameraem_eerframes=0
    cameraemdata_id=0
    darkmetadata_darkimagedata_id=0
    darkmetadata_sessiondata_id=0
    darkmetadata_cameraemdata_nframes=0
    if imgmetadata["ccdcamera"]:
        if "def_id" in imgmetadata["ccdcamera"].keys():
            ccdcamera_id=imgmetadata["ccdcamera"]["def_id"]
    if imgmetadata["cameraemdata"]:
        if "eer_frames" in imgmetadata["cameraemdata"].keys():
            cameraem_eerframes=imgmetadata['cameraemdata']['eer_frames']
            if not cameraem_eerframes:
                cameraem_eerframes=0
    if imgmetadata['darkmetadata']:
        if imgmetadata['darkmetadata']['darkimagedata']:
            if "def_id" in imgmetadata['darkmetadata']['darkimagedata'].keys():
                darkmetadata_darkimagedata_id=imgmetadata['darkmetadata']['darkimagedata']['def_id']
        if imgmetadata['darkmetadata']['sessiondata']:
            if "def_id" in imgmetadata['darkmetadata']['sessiondata'].keys():
                darkmetadata_sessiondata_id=imgmetadata['darkmetadata']['sessiondata']["def_id"]
        if imgmetadata['darkmetadata']['cameraemdata']:
            if "nframes" in imgmetadata['darkmetadata']['cameraemdata'].keys():
                darkmetadata_cameraemdata_nframes=imgmetadata['darkmetadata']['cameraemdata']["nframes"]
                if not darkmetadata_cameraemdata_nframes:
                    darkmetadata_cameraemdata_nframes=0

    dark_unique_id="ccd-%d_eerframes-%d_nframes-%d_image-%d_session-%d" % (ccdcamera_id, cameraem_eerframes, darkmetadata_cameraemdata_nframes, darkmetadata_darkimagedata_id, darkmetadata_sessiondata_id)
    dark_path=os.path.join(args["rundir"], "dark-%s.mrc" % dark_unique_id)
    kwargs["Dark"]=dark_path

    # DefectMap
    if imgmetadata['correctorplandata']['bad_pixels'] or imgmetadata['correctorplandata']['bad_cols'] or imgmetadata['correctorplandata']['bad_rows']:
        correctorplan_id=0
        if imgmetadata["correctorplandata"]:
            if "def_id" in imgmetadata["correctorplandata"].keys():
                correctorplan_id=imgmetadata["correctorplandata"]["def_id"]
        defect_map_unique_id="cameraem-%d_correctorplan-%d" % (cameraemdata_id, correctorplan_id)
        defect_map_path=os.path.join(args["rundir"], "defectmap-%s.mrc" % defect_map_unique_id)
        kwargs["DefectMap"]=defect_map_path

    # FmIntFile
    # FmDose
    if "InEer" in kwargs.keys():
        kwargs["FmDose"] = calcFmDose(imgmetadata['cameraemdata']['nframes'], imgmetadata['cameraemdata']['exposure_time'], imgmetadata['cameraemdata']['frame_time'], imgmetadata['presetdata']['dose'], args['rendered_frame_size'], totaldose, True)
        fmintfile_unique_id="cameraem-%d_framesize-%d_fmdose-%d" % (cameraemdata_id, args['rendered_frame_size'], kwargs["FmDose"])
        fmintfile_path=os.path.join(args["rundir"], "fmintfile-%s.txt" % fmintfile_unique_id)
        kwargs["FmIntFile"] = fmintfile_path
    else:
        kwargs["FmDose"] = calcFmDose(imgmetadata['cameraemdata']['nframes'], imgmetadata['cameraemdata']['exposure_time'], imgmetadata['cameraemdata']['frame_time'], imgmetadata['presetdata']['dose'], args['rendered_frame_size'], totaldose, False)

    # PixSize

    kwargs['PixSize'] = calcPixelSize(imgmetadata['pixelsizedata'], imgmetadata['cameraemdata']['subd_binning_x'], imgmetadata['imgdata']['def_timestamp'])

    # kV
    kwargs["kV"] = calcKV(imgmetadata['scope']['high_tension'])

    # Trunc
    # shifts = readShiftsBetweenFrames()
    shifts=[]
    sumframelist = filterFrameList(kwargs["PixSize"], imgmetadata['cameraemdata']['nframes'], shifts)
    total_frames = calcTotalFrames(imgmetadata['ccdcamera']['name'], imgmetadata['cameraemdata']['exposure_time'], imgmetadata['cameraemdata']['frame_time'], imgmetadata['cameraemdata']['nframes'], imgmetadata['cameraemdata']['eer_frames'])
    kwargs['Trunc'] = calcTrunc(total_frames, sumframelist)
    if not kwargs['Trunc']:
        del kwargs['Trunc']

    # RotGain
    # FlipGain
    kwargs['RotGain'], kwargs['FlipGain'] = calcRotFlipGain(imgmetadata["cameraemdata"]['frame_rotate'], 
                                                           imgmetadata["cameraemdata"]['frame_flip'], 
                                                           args['force_cpu_flat'], 
                                                           imgmetadata['frame_aligner_flat'])


    return kwargs

def constructMotionCor2JobMetadata(args : dict):
    from ...base.retrieve import readSessionData
    from ...base.cli import constructJobMetadata
    from ..store import saveDDStackRunData
    progname="makeddalignmotioncor2_ucsf"
    jobmetadata=constructJobMetadata(args, progname)
    sessionmetadata=readSessionData(args["sessionname"])
    jobmetadata['ref_apddstackrundata_ddstackrun']=saveDDStackRunData(args['preset'], args['align'], args['bin'], args['runname'], args['rundir'], sessionmetadata["session_id"])
    return jobmetadata


