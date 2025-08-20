def constructMotionCorKwargs(imgmetadata : dict, cli_args : dict, input_path : str) -> dict:
    import os
    from ..calc.internal import calcInputType, calcFmDose, calcPixelSize, calcKV, calcTotalFrames, calcTrunc, calcRotFlipGain, filterFrameList
    # Keyword args for motioncor2 function
    kwargs={}

    if 'eer_sampling' in cli_args.keys():
        kwargs['EerSampling'] = cli_args['eer_sampling']
    if 'Patchrows' in cli_args.keys() and 'Patchcols' in cli_args.keys():
        kwargs["Patch"] = "%s %s" % (str(cli_args["Patchcols"]), str(cli_args["Patchrows"]))
    if 'Iter' in cli_args.keys():
        kwargs["Iter"] = cli_args["Iter"]
    if 'Tol' in cli_args.keys():
        kwargs["Tol"] = cli_args["Tol"]
    if 'Bft_global' in cli_args.keys() and 'Bft_local' in cli_args.keys():
        kwargs["Bft"] = "%d %d" % (cli_args["Bft_global"], cli_args["Bft_local"])
    if 'bin' in cli_args.keys():
        if cli_args["bin"] != 1.0:
            kwargs["FtBin"] = cli_args["bin"]
    if 'startframe' in cli_args.keys():
        kwargs["Throw"] = cli_args["startframe"]
    if 'nrw' in cli_args.keys():
        kwargs["Group"] = cli_args["nrw"]
    # This flag doesn't seem to have been supported in motioncor2 since the 01-30-2017 version.
    #if 'MaskSizecols' in cli_args.keys() and 'MaskSizerows' in cli_args.keys():
    #    kwargs["MaskSize"] = "%d %d" % (cli_args["MaskSizecols"], cli_args["MaskSizerows"])
    if 'FmRef' in cli_args.keys():
        if cli_args["FmRef"] != 0:
            kwargs["FmRef"] = cli_args["FmRef"]
    if 'gpuids' in cli_args.keys():
        kwargs["Gpu"] = cli_args["gpuids"]
# TODO Figure out how user input might interact with Trunc calculation
#| `-Trunc` | User Input / Calculated | `setAlignedSumFrameList`, `-nframe`, `-startframe`, `driftlimit`, `apix` | |
    if "totaldose" in cli_args.keys():
        totaldose = cli_args["totaldose"]
    else:
        totaldose = None

    # InMrc, InTiff, InEer
    # Get the path to the input image.
    inputType = calcInputType(input_path)
    kwargs[inputType] = input_path

    #OutMrc
    #Path to the aligned aligned/summed micrograph.
    kwargs['OutMrc'] = os.path.join(cli_args['rundir'],imgmetadata['imgdata']['filename']+'_c.mrc')

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
    dark_path=os.path.join(cli_args["rundir"], imgmetadata['imgdata']['filename']+"_dark.mrc")
    kwargs["Dark"]=dark_path

    # DefectMap
    if imgmetadata['correctorplandata']['bad_pixels'] or imgmetadata['correctorplandata']['bad_cols'] or imgmetadata['correctorplandata']['bad_rows']:
        defect_map_path=os.path.join(cli_args["rundir"], "defectmap-correctorplan-%d_camera-%d.mrc" % (imgmetadata['correctorplandata']["def_id"], imgmetadata['cameraemdata']["def_id"]))
        kwargs["DefectMap"]=defect_map_path

    # FmIntFile
    # FmDose
    if "InEer" in kwargs.keys():
        kwargs["FmDose"] = calcFmDose(imgmetadata['cameraemdata']['nframes'], imgmetadata['cameraemdata']['exposure_time'], imgmetadata['cameraemdata']['frame_time'], imgmetadata['presetdata']['dose'], cli_args['rendered_frame_size'], totaldose, True)
        fmintfile_path=os.path.join(cli_args["rundir"], "fmintfile_camera-%d_rfs-%d_dose-%d.txt" % imgmetadata['cameraemdata']["def_id"], cli_args['rendered_frame_size'], kwargs["FmDose"])
        kwargs["FmIntFile"] = fmintfile_path
    else:
        kwargs["FmDose"] = calcFmDose(imgmetadata['cameraemdata']['nframes'], imgmetadata['cameraemdata']['exposure_time'], imgmetadata['cameraemdata']['frame_time'], imgmetadata['presetdata']['dose'], cli_args['rendered_frame_size'], totaldose, False)

    # PixSize

    kwargs['PixSize'] = calcPixelSize(imgmetadata['pixelsizedata'], imgmetadata['cameraemdata']['subd_binning_x'], imgmetadata['imgdata']['timestamp'])

    # kV
    kwargs["kV"] = calcKV(imgmetadata['scope']['high_tension'])

    # Trunc
    # shifts = readShiftsBetweenFrames()
    shifts=[]
    sumframelist = filterFrameList(kwargs["PixSize"], imgmetadata['cameraemdata']['nframes'], shifts)
    total_frames = calcTotalFrames(imgmetadata['cameraemdata']['name'], imgmetadata['cameraemdata']['exposure_time'], imgmetadata['cameraemdata']['frame_time'], imgmetadata['cameraemdata']['nframes'], imgmetadata['cameraemdata']['eer_frames'])
    kwargs['Trunc'] = calcTrunc(total_frames, sumframelist)
    if not kwargs['Trunc']:
        del kwargs['Trunc']

    # RotGain
    # FlipGain
    kwargs['RotGain'], kwargs['FlipGain'] = calcRotFlipGain(imgmetadata["cameraemdata"]['frame_rotate'], 
                                                           imgmetadata["cameraemdata"]['frame_flip'], 
                                                           cli_args['force_cpu_flat'], 
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


