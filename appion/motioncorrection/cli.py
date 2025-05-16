import argparse
from .calc import *
from .store import *
from .retrieve import *

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

    #parser.add_argument("--force_cpu_flat", dest="force_cpu_flat", default=False,
    #	action="store_true", help="Use cpu to make frame flat field corrrection")

    parser.add_argument("--rendered_frame_size", dest="rendered_frame_size", type=int, default=1,
        help="Sum this number of saved frames as a rendered frame in alignment", metavar="INT")
    parser.add_argument("--eer_sampling", dest="eer_sampling", type=int, default=1,
        help="Upsampling eer frames. Fourier binning will be added to return the results back", metavar="INT")
    return parser

def constructMotionCorKwargs(imgmetadata : dict, cli_args : dict, gain_input : str = "/tmp/gain.mrc", 
               dark_input : str = "/tmp/dark.mrc", defect_map_path : str ="/tmp/defect.mrc", 
               fmintfile : str ="/tmp/fmintfile.txt", force_cpu_flat : bool = False,
               rendered_frame_size : int = 1) -> dict:

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
    fpath = readInputPath(imgmetadata['session_image_path'].replace("leginon","frames"),imgmetadata['image_filename'])
    inputType = calcInputType(fpath)
    kwargs[inputType] = fpath

    # Gain
    # Get the reference image
    if gain_input:
        kwargs["Gain"]=gain_input
    else:
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

    saveDark(dark_input, imgmetadata['camera_name'], imgmetadata['eer_frames'], imgmetadata["dark_input"], imgmetadata["dark_nframes"])
    kwargs["Dark"]=dark_input

    # DefectMap
    if imgmetadata['bad_pixels'] or imgmetadata['bad_cols'] or imgmetadata['bad_rows']:
        defect_map=calcImageDefectMap(imgmetadata['bad_rows'], imgmetadata['bad_cols'], imgmetadata['bad_pixels'], imgmetadata['dx'], imgmetadata['dy'])
        saveDefectMrc(defect_map_path, defect_map, imgmetadata['frame_flip'], imgmetadata['frame_rotate'])

    # FmIntFile
    # FmDose
    if "InEer" in kwargs.keys():
        kwargs["FmDose"] = calcFmDose(imgmetadata['total_raw_frames'], imgmetadata['exposure_time'], imgmetadata['frame_time'], imgmetadata['dose'], rendered_frame_size, totaldose, True)
        saveFmIntFile(fmintfile, imgmetadata['total_raw_frames'], rendered_frame_size, kwargs["FmDose"] / rendered_frame_size)
        kwargs["FmIntFile"] = fmintfile
    else:
        kwargs["FmDose"] = calcFmDose(imgmetadata['total_raw_frames'], imgmetadata['exposure_time'], imgmetadata['frame_time'], imgmetadata['dose'], rendered_frame_size, totaldose, False)

    # PixSize

    kwargs['PixSize'] = calcPixelSize(imgmetadata['pixelsizedata'], imgmetadata['binning'], imgmetadata['imgdata_timestamp'])

    # kV
    kwargs["kV"] = calcKV(imgmetadata['high_tension'])

    # Trunc
    # shifts = readShiftsBetweenFrames()
    shifts=[]
    sumframelist = filterFrameList(kwargs["PixSize"], imgmetadata['nframes'], shifts)
    kwargs['Trunc'] = calcTrunc(imgmetadata['camera_name'], imgmetadata['exposure_time'], sumframelist, imgmetadata['frame_time'], imgmetadata['nframes'], imgmetadata['eer_frames'])
    if not kwargs['Trunc']:
        del kwargs['Trunc']

    # RotGain
    # FlipGain
    kwargs['RotGain'], kwargs['FlipGain'] = calcRotFlipGain(imgmetadata['frame_rotate'], 
                                                           imgmetadata['frame_flip'], 
                                                           force_cpu_flat, 
                                                           imgmetadata['frame_aligner_flat'])


    return kwargs

def preTask(imageid: int, args : dict):
    imgmetadata=readImageMetadata(imageid, False, args["align"], False)
    return constructMotionCorKwargs(imgmetadata, args)
    (imgmetadata : dict, cli_args : dict, gain_input : str = "/tmp/gain.mrc", 
               dark_input : str = "/tmp/dark.mrc", defect_map_path : str ="/tmp/defect.mrc", 
               fmintfile : str ="/tmp/fmintfile.txt", force_cpu_flat : bool = False,
               rendered_frame_size : int = 1, totaldose : float = False) 

def postTask():
    #updateDb
    # write out motioncorr log
    pass