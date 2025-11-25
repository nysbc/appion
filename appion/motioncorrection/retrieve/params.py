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
    # Simplify determining how an image's settings agree with other images by creating a unique ID based off of foreign keys.
    # Always starts with zero for purely aesthetic reasons / to prevent starting with a hyphen while still allowing us to reorder
    # the string appends at a later date.
    ref_uuid="0"
    imgmetadata['imgdata']=sb.get("AcquisitionImageData",{"def_id":imageid})
    if "ref_correctorplandata_corrector_plan" in imgmetadata['imgdata'].keys():
        imgmetadata['correctorplandata']=sb.get("CorrectorPlanData",{"def_id":imgmetadata['imgdata']["ref_correctorplandata_corrector_plan"]})
        ref_uuid+="-%d" % imgmetadata['imgdata']["ref_correctorplandata_corrector_plan"]
    else:
        imgmetadata['correctorplandata']={}
        imgmetadata['correctorplandata']["def_id"]=None
        imgmetadata['correctorplandata']["bad_pixels"]=None
        imgmetadata['correctorplandata']["bad_rows"]=None
        imgmetadata['correctorplandata']["bad_cols"]=None
        ref_uuid+="-%d" % 0

    imgmetadata['sessiondata']=sb.get("SessionData",{"def_id":imgmetadata['imgdata']["ref_sessiondata_session"]})
    imgmetadata['cameraemdata']=sb.get("CameraEMData",{"def_id":imgmetadata['imgdata']["ref_cameraemdata_camera"]})
    imgmetadata['ccdcamera']=sb.get("InstrumentData",{"def_id" : imgmetadata['cameraemdata']["ref_instrumentdata_ccdcamera"]})
    imgmetadata['presetdata']=sb.get("PresetData",{"def_id":imgmetadata['imgdata']["ref_presetdata_preset"]})
    imgmetadata['scope']=sb.get("ScopeEMData", {"def_id":imgmetadata['imgdata']["ref_scopeemdata_scope"]})
    ref_uuid+="-%d" % imgmetadata['imgdata']["ref_sessiondata_session"]
    ref_uuid+="-%d" % imgmetadata['imgdata']["ref_cameraemdata_camera"]
    ref_uuid+="-%d" % imgmetadata['cameraemdata']["ref_instrumentdata_ccdcamera"]
    ref_uuid+="-%d" % imgmetadata['imgdata']["ref_presetdata_preset"]
    ref_uuid+="-%d" % imgmetadata['imgdata']["ref_scopeemdata_scope"]
    if "frame_time" not in imgmetadata['cameraemdata'].keys():
        imgmetadata['cameraemdata']["frame_time"]=None   
    if "dose" not in imgmetadata['presetdata'].keys():
        imgmetadata['presetdata']['dose'] = None
    imgmetadata['imgdata']["def_timestamp"]=datetime.fromisoformat(imgmetadata['imgdata']["def_timestamp"])
    imgmetadata['frame_aligner_flat']=not (has_bad_pixels or not is_align or has_non_zero_dark)
    imgmetadata['pixelsizecalibrationdata'] = sb.filter("PixelSizeCalibrationData", dict(magnification=imgmetadata["scope"]['magnification'], 
                                                             ref_instrumentdata_tem=imgmetadata["scope"]['ref_instrumentdata_tem'], 
                                                             ref_instrumentdata_ccdcamera=imgmetadata["ccdcamera"]['def_id']))
    if not imgmetadata['pixelsizecalibrationdata']:
        raise RuntimeError("No pixelsize information was found for image %s with mag %d, tem id %d, ccdcamera id %d."
                        % (imgmetadata['imgdata']["filename"], 
                           imgmetadata["scope"]['magnification'], 
                           imgmetadata["scope"]['tem'], 
                           imgmetadata["ccdcamera"]['def_id']))
    imgmetadata['pixelsizedata']=[{"timestamp": datetime.fromisoformat(p["def_timestamp"]), "pixelsize" : p["pixelsize"] } for p in imgmetadata['pixelsizecalibrationdata']]
    # Gain inputs
    if "ref_normimagedata_norm" in imgmetadata['imgdata'].keys():
        imgmetadata['gainmetadata']={}
        imgmetadata['gainmetadata']['normimagedata']=sb.get("NormImageData", {"def_id" : imgmetadata['imgdata']["ref_normimagedata_norm"]})
        imgmetadata['gainmetadata']['sessiondata']=sb.get("SessionData", {"def_id" : imgmetadata['gainmetadata']['normimagedata']["ref_sessiondata_session"]})
        imgmetadata['gain_input']=os.path.join(imgmetadata['gainmetadata']['sessiondata']["image_path"],imgmetadata['gainmetadata']['normimagedata']["mrc_image"])
        ref_uuid+="-%d" % imgmetadata['imgdata']["ref_normimagedata_norm"]
    else:
        imgmetadata['gainmetadata']={}
        imgmetadata['gainmetadata']['normimagedata']={}
        imgmetadata['gainmetadata']['sessiondata']={}
        imgmetadata['gain_input']=""
        ref_uuid+="-%d" % 0
    if "ref_darkimagedata_dark" in imgmetadata['imgdata'].keys():
        imgmetadata['darkmetadata']={}
        imgmetadata['darkmetadata']['darkimagedata'] = sb.get("DarkImageData", {"def_id" : imgmetadata['imgdata']['ref_darkimagedata_dark']})
        imgmetadata['darkmetadata']['sessiondata']=sb.get("SessionData", {"def_id" : imgmetadata['darkmetadata']['darkimagedata']["ref_sessiondata_session"]})
        imgmetadata['dark_input']=os.path.join(imgmetadata['darkmetadata']['sessiondata']["image_path"],imgmetadata['darkmetadata']['darkimagedata']["mrc_image"])
        imgmetadata['darkmetadata']['cameraemdata']=sb.get("CameraEMData", {"camera":imgmetadata['darkmetadata']['darkimagedata']["ref_cameraemdata_camera"]})
        ref_uuid+="-%d" % imgmetadata['imgdata']["ref_darkimagedata_dark"]
    else:
        imgmetadata['darkmetadata']={}
        imgmetadata['darkmetadata']['darkimagedata']={}
        imgmetadata['darkmetadata']['sessiondata']={}
        imgmetadata['dark_input']=""
        imgmetadata['darkmetadata']['cameraemdata']={}
        imgmetadata['darkmetadata']['cameraemdata']['nframes']=None
        ref_uuid+="-%d" % 0
    imgmetadata["ref_uuid"]=ref_uuid
    return imgmetadata
