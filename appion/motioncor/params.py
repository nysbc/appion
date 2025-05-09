# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

# Settings file must be specified via the DJANGO_SETTINGS_MODULE environment variable.
# Possible solution for storing settings that will make our life easier:
# https://code.djangoproject.com/wiki/SplitSettings#ini-stylefilefordeployment
# My current thinking is that we can make it so that Django/sinedon
# can read the current sinedon.cfg file and use that to populate settings.py.

import django
django.setup()
from django.db.models import F
import os
from sinedon.models.leginon import AcquisitionImageData
from sinedon.models.leginon import PixelSizeCalibrationData
import numpy
import mrcfile
import math
from glob import glob

# InMrc, InTiff, InEer functions
def readInputPath(session_image_path : str, filename : str) -> str:
    fpath = os.path.join(session_image_path,filename+".*")
    fpath=glob(fpath)
    return fpath[0] if fpath else ""

def calcInputType(fpath):
    if fpath.endswith(".mrc"):
        return "InMrc"
    elif fpath.endswith(".tif") or fpath.endswith(".tiff"):
        return "InTiff"
    elif fpath.endswith(".eer"):
        return "InEer"
    else:
        raise RuntimeError("Unsupported file format for input path: %s." % fpath)

# Dark functions

def saveDark(dark_id : int, dark_path : str, camera_name : str, eer_frames : bool):
    if not dark_id:
        # Why is this switch statement necessary?  Why not save default dimensions into the database instead of
        # hardcoding them in here?  (Original Appion has these hardcoded as part of object initialization.)
        if camera_name == "GatanK2":
            dimensions = (3710,3838)
        elif camera_name == 'GatanK3':
            dimensions = (8184,11520)
        elif camera_name == 'DE':
            dimensions = (4096,3072)
        elif camera_name in ['TIA','Falcon','Falcon3','Falcon4'] or (camera_name == 'Falcon4EC' and eer_frames):
            dimensions = (4096,4096)
        else:
            dimensions = None
        unscaled_darkarray =  numpy.zeros((dimensions[1],dimensions[0]), dtype=numpy.float32)
    else:
        darkdata = AcquisitionImageData.objects.get(def_id=dark_id)
        unscaled_darkarray = mrcfile.read(darkdata.mrc_image) / darkdata.ref_cameraemdata_camera.nframes
    mrcfile.write(dark_path, unscaled_darkarray, overwrite=True)

# DefectMap functions
def calcImageDefectMap(bad_rows : str, bad_cols : str, bad_pixels : str, dx : int, dy : int):
    bad_rows = eval(bad_rows) if bad_rows else []
    bad_cols = eval(bad_cols) if bad_cols else []
    bad_pixels = eval(bad_pixels) if bad_pixels else []
    defect_map = numpy.zeros((dy,dx),dtype=numpy.int8)
    defect_map[bad_rows,:] = 1
    defect_map[:,bad_cols] = 1
    for px, py in bad_pixels:
        defect_map[py,px] = 1
    return defect_map

def saveDefectMrc(defect_map_path : str, defect_map : numpy.ndarray, frame_flip : int = 0, frame_rotate : int = 0) -> None:
    # flip and rotate map_array.  Therefore, do the opposite of
    # frames
    if frame_flip:
        if frame_rotate and frame_rotate == 2:
            # Faster to just flip left-right than up-down flip + rotate
            # flipping the frame left-right
            defect_map = numpy.fliplr(defect_map)
            frame_rotate = 0
            # reset flip
            frame_flip = 0
    if frame_rotate:
        # rotating the frame by %d degrees" % (frame_rotate*90,)
        defect_map = numpy.rot90(defect_map,4-frame_rotate)
    if frame_flip:
        #flipping the frame up-down
        defect_map = numpy.flipud(defect_map)
    mrcfile.write(defect_map_path, defect_map, overwrite=True)

# FmIntFile/FmDose functions

def calcFmDose(total_raw_frames: int, exposure_time, frame_time, dose, rendered_frame_size, totaldose, is_eer):
    # This depends on whether or not we're using an EER formatted-input.
    # see https://github.com/nysbc/appion-slurm/blob/f376758762771073c0450d2bc3badc0fed6f8e66/appion/appionlib/apDDFrameAligner.py#L395-L399

    if total_raw_frames is None:
        # older data or k2
        total_raw_frames =  int(exposure_time / frame_time)
    # avoid 0 for dark image scaling and frame list creation
    if total_raw_frames == 0:
        total_raw_frames = 1

    # totaldose is user-specified when the doseweight flag is passed
    # If this flag isn't specified, the database is queried.
    if not totaldose:
        if not dose:
            dose = 0.0
        totaldose = dose / 1e20
    if totaldose > 0:
        raw_dose = totaldose / total_raw_frames
    else:
        raw_dose = 0.03 #make fake dose similar to Falcon4EC 7 e/p/s

    if not is_eer:
        return totaldose/total_raw_frames
    else:
        return raw_dose*rendered_frame_size

def calcTotalRenderedFrames(nraw, size):
    # total_rendered_frames is used when writing out the motioncorr log
    return nraw // size

def saveFmIntFile(fmintpath, nraw, size, raw_dose):
    '''
    calculate and set frame dose and create FmIntFile
    '''
    modulo = nraw % size
    int_div = nraw // size
    lines = []
    total_rendered_frames = calcTotalRenderedFrames(nraw, size)
    if modulo != 0:
        total_rendered_frames += 1
        lines.append('%d\t%d\t%.3f\n' % (modulo, modulo, raw_dose))
    lines.append('%d\t%d\t%.3f\n' % (int_div*size+modulo, size, raw_dose))
    with open(fmintpath,'w') as f:
        f.write(''.join(lines))

# PixSize functions

def calcPixelSize(pixelsizedatas, binning, imgdata_timestamp):
    """
    use image data object to get pixel size
    multiplies by binning and also by 1e10 to return image pixel size in angstroms
    Assumes that pixelsizedata is in descending order sorted by timestamp.

    return image pixel size in Angstroms
    """
    i = 0
    pixelsizedata = pixelsizedatas[i]
    oldestpixelsizedata = pixelsizedata
    while pixelsizedata["timestamp"] > imgdata_timestamp and i < len(pixelsizedatas):
        i += 1
        pixelsizedata = pixelsizedatas[i]
        if pixelsizedata["timestamp"] < oldestpixelsizedata["timestamp"]:
            oldestpixelsizedata = pixelsizedata
    if pixelsizedata["timestamp"] > imgdata_timestamp:
        # There is no pixel size calibration data for this image. Use oldest value.
        pixelsizedata = oldestpixelsizedata
    pixelsize = oldestpixelsizedata["pixelsize"] * binning
    return pixelsize*1e10

# Trunc Functions

# Forming the path to the log file is a problem for future me.
# Why not just pass in the data extracted from the original log?
def readShiftsBetweenFrames(logfile : str = "") -> list:
    '''
    Return a list of shift distance by frames. item 0 is fake. item 1 is distance between
    frame 0 and frame 1
    '''
    if not os.path.isfile(logfile):
        raise RuntimeError('No alignment log file %s found for thresholding drift' % logfile)
    shifts=[]
    # Reads from dosefgpu_driftcorr log file the shifts applied to each frame
    with open(logfile, 'r') as f:
        text = f.read()
    lines = text[text.find('Sum Frame'):text.find('Save Sum')].split('\n')[1:-2]
    positions = []
    for line in lines:
        shift_bits = line.split('shift:')
        # Issue #4234
        if len(shift_bits) <=1:
            continue
        position_strings = shift_bits[1].split()
        position_x = float(position_strings[0])
        position_y = float(position_strings[1])
        positions.append((position_x,position_y))
    # place holder for running first frame shift duplication
    running=1
    offset = int((running-1)/2)
    shifts = offset*[None,]
    for p in range(len(positions)-1):
        shift = math.hypot(positions[p][0]-positions[p+1][0],positions[p][1]-positions[p+1][1])
        shifts.append(shift)
    # duplicate first and last shift for the end points if running
    for i in range(offset):
        shifts.append(shifts[-1])
        shifts[i] = shifts[offset]
    return shifts

def filterFrameList(pixelsize : float, total_frames : int, shifts : list, nframe : int = None, startframe : int = None, driftlimit : int = None):
    '''
    Get list of frames
    '''
    framelist=[]
    # frame list according to start frame and number of frames
    if nframe is None:
        if startframe is None:
            framelist = range(total_frames)
        else:
            framelist = range(startframe,total_frames)
    else:
        framelist = range(startframe,startframe+nframe)
    if driftlimit is not None:
        # drift limit considered
        threshold = driftlimit / pixelsize
        stillframes = []
        # pick out passed frames
        for i in range(len(shifts[:-1])):
            # keep the frame if at least one shift around the frame is small enough
            if min(shifts[i],shifts[i+1]) < threshold:
                # index is off by 1 because of the duplication
                stillframes.append(i)
        if stillframes:
            framelist = list(set(framelist).intersection(set(stillframes)))
            framelist.sort()
        #apDisplay.printMsg('Limit frames used to %s' % (framelist,))
    return framelist

def calcKV(high_tension):
    return high_tension/1000.0

def calcTrunc(camera_name : str, exposure_time : float, sumframelist : list, frame_time : float, nframes : int, eer_frames : bool):
    if camera_name in ["GatanK2","GatanK3"]:
        total_frames = max(1,int(exposure_time / frame_time))
    elif 'DE':
        total_frames = nframes
    elif camera_name in ['TIA','Falcon','Falcon3','Falcon4'] or (camera_name == 'Falcon4EC' and eer_frames):
        total_frames = nframes
    else:
        total_frames = nframes
    return total_frames - sumframelist[-1] - 1

# RotGain and FlipGain functions
def calcRotFlipGain(frame_rotate : int, frame_flip: int, force_cpu_flat : bool, frame_aligner_flat: bool) -> tuple:
    if not force_cpu_flat and frame_aligner_flat:
        return frame_rotate, frame_flip
    else:
        return 0, 0
    
# Retrieves metadata from the database that is used to calculate inputs to motioncor2/motioncor3
def readImageMetadata(imageid: int, has_bad_pixels : bool = False, is_align : bool = False, has_non_zero_dark : bool = False):
    imgmetadata={}
    imgdata=AcquisitionImageData.objects.get(def_id=imageid)
    correctorplandata=imgdata.ref_correctorplandata_corrector_plan
    sessiondata=imgdata.ref_sessiondata_session
    cameradata=imgdata.ref_cameraemdata_camera
    # Additional parameters derived from the database
    # Input image parameters
    imgmetadata['session_image_path']=sessiondata.image_path
    imgmetadata['image_filename']=imgdata.filename
    # Dark inputs
    imgmetadata['dark_id']=imgdata.ref_darkimagedata_dark
    imgmetadata['camera_name']=imgdata.ref_cameraemdata_camera.ref_instrumentdata_ccdcamera.name
    imgmetadata['eer_frames']=imgdata.ref_cameraemdata_camera.eer_frames
    # DefectMap inputs
    imgmetadata['dx'] = cameradata.subd_dimension_x
    imgmetadata['dy'] = cameradata.subd_dimension_y
    if correctorplandata:
        imgmetadata['bad_pixels'] = correctorplandata.bad_pixels
        imgmetadata['bad_rows'] = correctorplandata.bad_rows
        imgmetadata['bad_cols'] = correctorplandata.bad_cols
    else:
        imgmetadata['bad_pixels']=None
        imgmetadata['bad_rows']=None
        imgmetadata['bad_cols']=None
    # FmDose, FmIntFile inputs
    imgmetadata['total_raw_frames'] = imgdata.ref_cameraemdata_camera.nframes
    imgmetadata['exposure_time'] = imgdata.ref_cameraemdata_camera.exposure_time
    imgmetadata['frame_time'] = imgdata.ref_cameraemdata_camera.frame_time
    imgmetadata['dose'] = imgdata.ref_presetdata_preset.dose
    # PixSize inputs
    imgmetadata['magnification']=imgdata.ref_scopeemdata_scope.magnification
    imgmetadata['tem']=imgdata.ref_scopeemdata_scope.ref_instrumentdata_tem.def_id
    imgmetadata['ccdcamera']=imgdata.ref_cameraemdata_camera.ref_instrumentdata_ccdcamera.def_id
    imgmetadata['binning']=imgdata.ref_cameraemdata_camera.subd_binning_x
    imgmetadata['imgdata_timestamp']=imgdata.def_timestamp
    # kV inputs
    imgmetadata['high_tension']=imgdata.ref_scopeemdata_scope.high_tension
    # Trunc inputs
    #camera_name is already defined for Dark
    #exposure_time is already defined for FmDose/FmIntFile
    #frame_time is already defined for FmDose/FmIntFile
    imgmetadata['nframes']=imgdata.ref_cameraemdata_camera.nframes
    #eer_frames is already defined for Dark
    # FlipGain/RotGain inputs
    imgmetadata['frame_rotate']=cameradata.frame_rotate
    imgmetadata['frame_flip']=cameradata.frame_flip
    imgmetadata['frame_aligner_flat']=not (has_bad_pixels or not is_align or has_non_zero_dark)
    # PixSize inputs
    pixelsizecalibrationdata = PixelSizeCalibrationData.objects.filter(magnification=imgmetadata['magnification'], 
                                                             ref_instrumentdata_tem=imgmetadata['tem'], 
                                                             ref_instrumentdata_ccdcamera=imgmetadata['ccdcamera']).order_by(F("def_timestamp").desc())
    if not pixelsizecalibrationdata:
        raise RuntimeError("No pixelsize information was found for image %s with mag %d, tem id %d, ccdcamera id %d."
                        % (imgmetadata['image_filename'], 
                           imgmetadata['magnification'], 
                           imgmetadata['tem'], 
                           imgmetadata['ccdcamera']))
    imgmetadata['pixelsizedata']=[{"timestamp": p.def_timestamp, "pixelsize" : p.pixelsize } for p in pixelsizecalibrationdata]
    # Gain inputs
    gaindata=AcquisitionImageData.objects.get(def_id=imgdata.ref_normimagedata_norm)
    imgmetadata['gain_input']=os.path.join(imgmetadata['session_image_path'],gaindata.mrc_image)
    return imgmetadata

def calcParams(imgmetadata : dict, gain_input : str = "/tmp/gain.mrc", 
               dark_input : str = "/tmp/dark.mrc", defect_map_path : str ="/tmp/defect.mrc", 
               fmintfile : str ="/tmp/fmintfile.txt", force_cpu_flat : bool = False,
               rendered_frame_size : int = 1, totaldose : float = False) -> dict:

    # Keyword args for motioncor2 function
    kwargs={}

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
    saveDark(imgmetadata['dark_id'], dark_input, imgmetadata['camera_name'], imgmetadata['eer_frames'])
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
    #shifts = readShiftsBetweenFrames()
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
