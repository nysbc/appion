# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

import sinedon.setup
sinedon.setup()
from django.db.models import F
from sinedon.models.leginon import AcquisitionImageData
from sinedon.models.leginon import PixelSizeCalibrationData
import os
import math
from glob import glob
from ..calc import *
from ..store import *

# InMrc, InTiff, InEer functions
def readInputPath(session_image_path : str, filename : str) -> str:
    fpath = os.path.join(session_image_path,filename+".*")
    fpath=glob(fpath)
    return fpath[0] if fpath else ""

# Trunc Functions
# Forming the path to the log file is a problem for future me.
# Why not just pass in the data extracted from the original log?
def readShiftsBetweenFrames(logfile : str) -> list:
    '''
    Return a list of shift distance by frames. item 0 is fake. item 1 is distance between
    frame 0 and frame 1
    '''
    if not os.path.isfile(logfile):
        raise RuntimeError('No alignment log file %s found for thresholding drift.' % logfile)
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
    darkdata = AcquisitionImageData.objects.get(def_id=imgmetadata['dark_id'])
    imgmetadata['dark_input']=darkdata.mrc_image
    imgmetadata['dark_nframes']=darkdata.ref_cameraemdata_camera.nframes
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