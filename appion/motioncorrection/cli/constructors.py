import os
from ..calc import calcInputType, calcImageDefectMap, calcFmDose, calcPixelSize, calcKV, calcTotalFrames, calcTrunc, calcRotFlipGain, filterFrameList, calcMotionCorrLogPath, calcTotalRenderedFrames, motioncor
from ..store import saveDark, saveDefectMrc, saveFmIntFile, saveDDStackRunData, saveFrameTrajectory, constructAlignedCamera, constructAlignedPresets, constructAlignedImage, uploadAlignedImage, saveDDStackParamsData, saveMotionCorrLog
from ..retrieve import readInputPath, readImageMetadata
from ...base.retrieve import readSessionData
from ...base.cli import constructJobMetadata


def constructMotionCorKwargs(imgmetadata : dict, cli_args : dict) -> dict:

    # Keyword args for motioncor2 function
    kwargs={}

    if 'eer_sampling' in cli_args.keys():
        kwargs['EerSampling'] = cli_args['eer_sampling']
    if 'Patchrows' in cli_args.keys() and 'Patchcols' in cli_args.keys():
        kwargs["Patch"] = cli_args["Patch"]
    if 'Iter' in cli_args.keys():
        kwargs["Iter"] = cli_args["Iter"]
    if 'Tol' in cli_args.keys():
        kwargs["Tol"] = cli_args["Tol"]
    if 'Bft_global' in cli_args.keys() and 'Bft_local' in cli_args.keys():
        kwargs["Bft"] = "%d %d" % (cli_args["Bft_global"], cli_args["Bft_local"])
    if 'bin' in cli_args.keys():
        kwargs["FtBin"] = cli_args["bin"]
    if 'startframe' in cli_args.keys():
        kwargs["Throw"] = cli_args["startframe"]
    if 'nrw' in cli_args.keys():
        kwargs["Group"] = cli_args["nrw"]
    # This flag doesn't seem to have been supported in motioncor2 since the 01-30-2017 version.
    #if 'MaskSizecols' in cli_args.keys() and 'MaskSizerows' in cli_args.keys():
    #    kwargs["MaskSize"] = "%d %d" % (cli_args["MaskSizecols"], cli_args["MaskSizerows"])
    if 'FmRef' in cli_args.keys():
        kwargs["FmRef"] = cli_args["FmRef"]
    if 'gpuids' in cli_args.keys():
        kwargs["Gpu"] = cli_args["gpuids"]
# TODO Figure out how user input might interact with Trunc calculation
#| `-Trunc` | User Input / Calculated | `setAlignedSumFrameList`, `-nframe`, `-startframe`, `driftlimit`, `apix` | |
    if "totaldose" in cli_args.keys():
        totaldose = cli_args["totaldose"]
    else:
        totaldose = imgmetadata['dose']

    # InMrc, InTiff, InEer
    # Get the path to the input image.
    fpath = readInputPath(imgmetadata['session_frame_path'],imgmetadata['image_filename'])
    inputType = calcInputType(fpath)
    kwargs[inputType] = fpath

    #OutMrc
    #Path to the aligned aligned/summed micrograph.
    kwargs['OutMrc'] = os.path.join(cli_args['rundir'],imgmetadata['image_filename']+'_c.mrc')

    # Gain
    # Get the reference image
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
    dark_path=os.path.join(cli_args["rundir"], imgmetadata['filename']+"_dark.mrc")
    saveDark(dark_path, imgmetadata['camera_name'], imgmetadata['eer_frames'], imgmetadata["dark_input"], imgmetadata["dark_nframes"])
    kwargs["Dark"]=dark_path

    # DefectMap
    if imgmetadata['bad_pixels'] or imgmetadata['bad_cols'] or imgmetadata['bad_rows']:
        defect_map_path=os.path.join(cli_args["rundir"], imgmetadata['filename']+"_defect.mrc")
        defect_map=calcImageDefectMap(imgmetadata['bad_rows'], imgmetadata['bad_cols'], imgmetadata['bad_pixels'], imgmetadata['dx'], imgmetadata['dy'])
        saveDefectMrc(defect_map_path, defect_map, imgmetadata['frame_flip'], imgmetadata['frame_rotate'])

    # FmIntFile
    # FmDose
    if "InEer" in kwargs.keys():
        kwargs["FmDose"] = calcFmDose(imgmetadata['total_raw_frames'], imgmetadata['exposure_time'], imgmetadata['frame_time'], imgmetadata['dose'], cli_args['rendered_frame_size'], totaldose, True)
        fmintfile_path=os.path.join(cli_args["rundir"], imgmetadata['filename']+"_fmintfile.txt")
        saveFmIntFile(fmintfile_path, imgmetadata['total_raw_frames'], cli_args['rendered_frame_size'], kwargs["FmDose"] / cli_args['rendered_frame_size'])
        kwargs["FmIntFile"] = fmintfile_path
    else:
        kwargs["FmDose"] = calcFmDose(imgmetadata['total_raw_frames'], imgmetadata['exposure_time'], imgmetadata['frame_time'], imgmetadata['dose'], cli_args['rendered_frame_size'], totaldose, False)

    # PixSize

    kwargs['PixSize'] = calcPixelSize(imgmetadata['pixelsizedata'], imgmetadata['binning'], imgmetadata['imgdata_timestamp'])

    # kV
    kwargs["kV"] = calcKV(imgmetadata['high_tension'])

    # Trunc
    # shifts = readShiftsBetweenFrames()
    shifts=[]
    sumframelist = filterFrameList(kwargs["PixSize"], imgmetadata['nframes'], shifts)
    total_frames = calcTotalFrames(imgmetadata['camera_name'], imgmetadata['exposure_time'], imgmetadata['frame_time'], imgmetadata['nframes'], imgmetadata['eer_frames'])
    kwargs['Trunc'] = calcTrunc(total_frames, sumframelist)
    if not kwargs['Trunc']:
        del kwargs['Trunc']

    # RotGain
    # FlipGain
    kwargs['RotGain'], kwargs['FlipGain'] = calcRotFlipGain(imgmetadata['frame_rotate'], 
                                                           imgmetadata['frame_flip'], 
                                                           cli_args['force_cpu_flat'], 
                                                           imgmetadata['frame_aligner_flat'])


    return kwargs

def constructMotionCor2JobMetadata(args : dict):
    progname="makeddalignmotioncor2_ucsf"
    jobmetadata=constructJobMetadata(args, progname)
    sessionmetadata=readSessionData(args["sessionname"])
    jobmetadata['ref_apddstackrundata_ddstackrun']=saveDDStackRunData(args['preset'], args['align'], args['bin'], args['runname'], args['rundir'], sessionmetadata["session_id"])
    return jobmetadata


