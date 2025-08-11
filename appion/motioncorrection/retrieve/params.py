# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

import sinedon.base as sb
import os
import math
from datetime import datetime

# InMrc, InTiff, InEer functions
def readInputPath(session_frame_path : str, filename : str) -> str:
    # Potential suffixes for filename are determined by rawtransfer
    # https://github.com/nysbc/leginon/blob/48be5325d4645d1591395d3f707bac2161570f98/leginon/rawtransfer.py#L149-L164
    # Suffix does not seem to be saved in the database anywhere.
    dst_suffixes = [".frames.mrc", ".frames.tif",".frames.eer", ".frames"]
    for dst_suffix in dst_suffixes:
        fpath = os.path.join(session_frame_path,filename+dst_suffix)
        # Lazy way to create test files in shoddy test env
        #if not os.path.isdir(session_frame_path):
        #    os.makedirs(session_frame_path)
        #if not os.path.exists(fpath):
        #    with open(fpath,"w") as f:
        #        f.write("")
        if os.path.exists(fpath):
            return fpath
    return None

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
    imgmetadata['imageid']=imageid
    imgdata=sb.get("AcquisitionImageData",{"def_id":imageid})
    if "ref_correctorplandata_corrector_plan" in imgdata.keys():
        correctorplandata=sb.get("CorrectorPlanData",{"def_id":imgdata["ref_correctorplandata_corrector_plan"]})
    else:
        correctorplandata=None
    sessiondata=sb.get("SessionData",{"def_id":imgdata["ref_sessiondata_session"]})
    cameradata=sb.get("CameraEMData",{"def_id":imgdata["ref_cameraemdata_camera"]})
    imgmetadata['camera_id']=cameradata["def_id"]
    # Additional parameters derived from the database
    # Input image parameters
    imgmetadata['session_id']=sessiondata["def_id"]
    imgmetadata['session_image_path']=sessiondata["image_path"]
    imgmetadata['session_frame_path']=sessiondata["frame_path"]
    imgmetadata['image_filename']=imgdata["filename"]
    # Dark inputs
    if "ref_darkimagedata_dark" in imgmetadata.keys():
        imgmetadata['dark_id']=imgdata["ref_darkimagedata_dark"]
    else:
        imgmetadata['dark_id']=None
    ccdcamera=sb.get("InstrumentData",{"def_id" : cameradata["ref_instrumentdata_ccdcamera"]})
    imgmetadata['camera_name']=ccdcamera["name"]
    imgmetadata['eer_frames']=cameradata["eer_frames"]
    # DefectMap inputs
    imgmetadata['dx'] = cameradata["subd_dimension_x"]
    imgmetadata['dy'] = cameradata["subd_dimension_y"]
    if correctorplandata:
        imgmetadata['bad_pixels'] = correctorplandata["bad_pixels"]
        imgmetadata['bad_rows'] = correctorplandata["bad_rows"]
        imgmetadata['bad_cols'] = correctorplandata["bad_cols"]
    else:
        imgmetadata['bad_pixels']=None
        imgmetadata['bad_rows']=None
        imgmetadata['bad_cols']=None
    # FmDose, FmIntFile inputs
    imgmetadata['total_raw_frames'] = cameradata["nframes"]
    imgmetadata['exposure_time'] = cameradata["exposure_time"]
    if "frame_time" in cameradata.keys():
        imgmetadata['frame_time'] = cameradata["frame_time"]
    else:
        imgmetadata['frame_time'] = None
    preset=sb.get("PresetData",{"def_id":imgdata["ref_presetdata_preset"]})
    if "dose" in preset.keys():
        imgmetadata['dose'] = preset["dose"]
    else:
        imgmetadata['dose'] = None
    # PixSize inputs
    scope=sb.get("ScopeEMData", {"def_id":imgdata["ref_scopeemdata_scope"]})
    imgmetadata['magnification']=scope["magnification"]
    imgmetadata['tem']=scope["ref_instrumentdata_tem"]
    imgmetadata['ccdcamera']=ccdcamera["def_id"]
    imgmetadata['binning']=cameradata["subd_binning_x"]
    imgmetadata['imgdata_timestamp']=datetime.fromisoformat(imgdata["def_timestamp"])
    # kV inputs
    imgmetadata['high_tension']=scope["high_tension"]
    # Trunc inputs
    #camera_name is already defined for Dark
    #exposure_time is already defined for FmDose/FmIntFile
    #frame_time is already defined for FmDose/FmIntFile
    imgmetadata['nframes']=cameradata["nframes"]
    #eer_frames is already defined for Dark
    # FlipGain/RotGain inputs
    imgmetadata['frame_rotate']=cameradata["frame_rotate"]
    imgmetadata['frame_flip']=cameradata["frame_flip"]
    imgmetadata['frame_aligner_flat']=not (has_bad_pixels or not is_align or has_non_zero_dark)
    # PixSize inputs
    pixelsizecalibrationdata = sb.filter("PixelSizeCalibrationData", dict(magnification=imgmetadata['magnification'], 
                                                             ref_instrumentdata_tem=imgmetadata['tem'], 
                                                             ref_instrumentdata_ccdcamera=imgmetadata['ccdcamera']))
    if not pixelsizecalibrationdata:
        raise RuntimeError("No pixelsize information was found for image %s with mag %d, tem id %d, ccdcamera id %d."
                        % (imgmetadata['image_filename'], 
                           imgmetadata['magnification'], 
                           imgmetadata['tem'], 
                           imgmetadata['ccdcamera']))
    imgmetadata['pixelsizedata']=[{"timestamp": datetime.fromisoformat(p["def_timestamp"]), "pixelsize" : p["pixelsize"] } for p in pixelsizecalibrationdata]
    # Gain inputs
    #if "ref_normimagedata_norm" in imgdata.keys():
    #    gaindata=sb.get("AcquisitionImageData", {"def_id" : imgdata["ref_normimagedata_norm"]})
    #    gainsessiondata=sb.get("SessionData", {"def_id" : gaindata["ref_sessiondata_session"]})
    #    imgmetadata['gain_input']=os.path.join(gainsessiondata["frame_path"],gaindata["mrc_image"])
    #else:
    imgmetadata['gain_input']=None
    if imgmetadata['dark_id']:
        darkdata = sb.get("AcquisitionImageData", {"def_id" : imgmetadata['dark_id']})
        imgmetadata['dark_input']=darkdata["mrc_image"]
        darkcamera=sb.get("CameraEMData", {"camera":darkdata["ref_cameraemdata_camera"]})
        imgmetadata['dark_nframes']=darkcamera["nframes"]
    else:
        imgmetadata['dark_input']=None
        imgmetadata['dark_nframes']=None
    imgmetadata['preset_id']=imgdata["ref_presetdata_preset"]
    return imgmetadata
