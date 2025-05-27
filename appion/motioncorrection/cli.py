import argparse
from .calc import *
from .store import *
from .retrieve import *
from ..base.store import *

def constructMotionCorParser():
    parser = argparse.ArgumentParser(add_help=False)
    # Integer
    parser.add_argument("--ddstartframe", dest="startframe", type=int, default=0,
        help="starting frame for summing the frames. The first frame is 0")
    parser.add_argument("--alignlabel", dest="alignlabel", default='a',
        help="label to be appended to the presetname, e.g. --label=a gives ed-a as the aligned preset for preset ed", metavar="CHAR")
    parser.add_argument("--bin",dest="bin",type=float,default="1.0",
        help="Binning factor relative to the dd stack. MotionCor2 takes float value (optional)")

    # Dosefgpu_driftcoor options
    parser.add_argument("--alignoffset", dest="fod", type=int, default=2,
        help="number of frame offset in alignment in dosefgpu_driftcorr")
    parser.add_argument("--alignccbox", dest="pbx", type=int, default=128,
        help="alignment CC search box size in dosefgpu_driftcorr")

    # Dose weighting, based on Grant & Grigorieff eLife 2015
    parser.add_argument("--doseweight",dest="doseweight", default=False,
        action="store_true", help="dose weight the frame stack, according to Tim / Niko's curves")
    parser.add_argument("--totaldose",dest="totaldose", type=float,
                    help="total dose for the full movie stack in e/A^2. If not specified, will get value from database")

    #parser.add_argument("--override_db", dest="override_db", default=False,
    #	action="store_true", help="Override database for bad rows, columns, and image flips")
    # String

    # Integer


    parser.add_argument("--trim", dest="trim", type=int, default=0,
        help="Trim edge off after frame stack gain/dark correction")
    parser.add_argument("--align", dest="align", default=False,
        action="store_true", help="Make Aligned frame stack")
    parser.add_argument("--refimgid", dest="refimgid", type=int,
        help="Specify a corrected image to do gain/dark correction with")

    parser.add_argument("--gpuid", dest="gpuid", type=int, default=0,
        help="GPU device id used in gpu processing")

    parser.add_argument("--gpuids", dest="gpuids", default='0')
    parser.add_argument("--nrw", dest="nrw", type=int, default=1,
        help="Number (1, 3, 5, ...) of frames in running average window. 0 = disabled", metavar="INT")

    parser.add_argument("--FmRef", dest="FmRef",type=int,default=0,
        help="Specify which frame to be the reference to which all other frames are aligned. Default 0 is aligned to the first frame, other values aligns to the central frame.")

    parser.add_argument("--Iter", dest="Iter",type=int,default=7,
        help="Maximum iterations for iterative alignment, default is 7.")

    parser.add_argument("--Tol", dest="Tol",type=float,default=0.5,
                    help="Tolerance for iterative alignment, in pixels")

    parser.add_argument("--Patchrows",dest="Patchrows",type=int,default="0",
        help="Number of patches divides the y-axis to be used for patch based alignment. Default 0 corresponds to full frame alignment in the direction.")

    parser.add_argument("--Patchcols",dest="Patchcols",type=int,default="0",
        help="Number of patches divides the x-axis to be used for patch based alignment. Default 0 corresponds to full frame alignment in the direction.")

    parser.add_argument("--MaskCentrow",dest="MaskCentrow",type=int,default="0",
        help="Y Coordinates for center of subarea that will be used for alignment. Default 0 corresponds to center coordinate.")

    parser.add_argument("--MaskCentcol",dest="MaskCentcol",type=int,default="0",
        help="X Coordinate for center of subarea that will be used for alignment. Default 0 corresponds to center coordinate.")

    parser.add_argument("--MaskSizecols",dest="MaskSizecols",type=float,default="1.0",
        help="The X size of subarea that will be used for alignment, default 1.0 1.0 corresponding full size.")
    parser.add_argument("--MaskSizerows",dest="MaskSizerows",type=float,default="1.0",
        help="The Y size of subarea that will be used for alignment, default 1.0 corresponding full size.")

    # instead of single align bfactor, bft, this has two entries
    parser.add_argument("--Bft_global",dest="Bft_global",type=float,default=500.0,
                    help=" Global B-Factor for alignment, default 500.0.")

    parser.add_argument("--Bft_local",dest="Bft_local",type=float,default=150.0,
                    help=" Global B-Factor for alignment, default 150.0.")

    # Not used anymore.  Get rid of?  Was this meant for pre-direct detector images (camera CMOS/CCD)?
    parser.add_argument("--force_cpu_flat", dest="force_cpu_flat", default=False,
    	action="store_true", help="Use cpu to make frame flat field corrrection")

    parser.add_argument("--rendered_frame_size", dest="rendered_frame_size", type=int, default=1,
        help="Sum this number of saved frames as a rendered frame in alignment")
    parser.add_argument("--eer_sampling", dest="eer_sampling", type=int, default=1,
        help="Upsampling eer frames. Fourier binning will be added to return the results back", metavar="INT")
    return parser

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
    #TODO Better way to do this using the data in leginon.cfg?
    fpath = readInputPath(imgmetadata['session_image_path'].replace("leginon","frames"),imgmetadata['image_filename'])
    inputType = calcInputType(fpath)
    kwargs[inputType] = fpath

    #TODO
    #OutMrc

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

def constructJobMetadata(args : dict):
    jobmetadata={}
    jobmetadata['ref_scriptprogramname_progname']=saveScriptProgramName()
    jobmetadata['ref_scriptusername_username']=saveScriptUsername()
    jobmetadata['ref_scripthostname_hostname']=saveScriptHostName()
    jobmetadata['ref_appathdata_appion_path']=savePathData(__path__)
    jobmetadata['ref_appathdata_rundir']=savePathData(args['rundir'])
    # TODO write a function to generate the run name.
    jobmetadata['runname']=""
    jobmetadata['ref_apappionjobdata_job']=saveApAppionJobData(jobmetadata['ref_appathdata_rundir'], "makeddalignmotioncor2_ucsf", jobmetadata['runname'], pwd.getpwuid(os.getuid())[0], platform.node(), jobmetadata['ref_sessiondata_session'])
    jobmetadata['ref_scriptprogramrun_progrun']=saveScriptProgramRun(jobmetadata['runname'], jobmetadata['ref_scriptprogramname_progname'], jobmetadata['ref_scriptusername_username'], jobmetadata['ref_scripthostname_hostname'], jobmetadata['ref_appathdata_appion_path'], jobmetadata['ref_appathdata_rundir'], jobmetadata['ref_apappionjobdata_job'])
    saveScriptParams(args, jobmetadata['ref_scriptprogramname_progname'], jobmetadata['ref_scriptprogramrun_progrun'])
    return jobmetadata

def preTask(imageid: int, args : dict):
    jobmetadata=constructJobMetadata(args)
    imgmetadata=readImageMetadata(imageid, False, args["align"], False)
    if 'refimgid' in args.keys():
        gainmetadata=readImageMetadata(args['refimgid'], False, args["align"], False)
        imgmetadata['gain_input']=readInputPath(gainmetadata['session_image_path'].replace("leginon","frames"),gainmetadata['image_filename'])
    kwargs=constructMotionCorKwargs(imgmetadata, args)
    return kwargs, jobmetadata, imageid

def task(kwargs, jobmetadata, args, imageid):
    output, _ = motioncor(**kwargs)
    return jobmetadata, args, imageid, output

def postTask(jobmetadata, imgmetadata, args, kwargs, imageid, logData):
    # constructAlignedCamera(camera_id, square_output):
    saveApAssessmentRunData(imgmetadata['session_id'], assessment)
    updateApAppionJobData(jobid, "D")
    # TODO Hardlink motion-corrected output to Leginon directory b/c that's where myamiweb / image viewer expects it to be; symlink as fallback.
    uploadAlignedImage(imageid, aligned_image_def_id, rundata_def_id, logData["shifts"], kwargs["PixSize"])
    saveFrameTrajectory(image_def_id, rundata_def_id, logData["shifts"], limit, reference_index, particle)
    saveDDStackParamsData(args['preset'], args['align'], args['bin'], ref_apddstackrundata_unaligned_ddstackrun, method, ref_apstackdata_stack, ref_apdealignerparamsdata_de_aligner)
    saveDDStackRunData(args['preset'], args['align'], args['bin'], jobmetadata['runname'], args['rundir'], imgmetadata["session_id"])
    saveMotionCorrLog(logData, outputLogPath, args['startframe'], calcTotalRenderedFrames(imgmetadata['total_raw_frames'], args['rendered_frame_size']), args['bin'])
    return imageid