# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

# Settings file must be specified via the DJANGO_SETTINGS_MODULE environment variable.
# Possible solution for storing settings that will make our life easier:
# https://code.djangoproject.com/wiki/SplitSettings#ini-stylefilefordeployment
# My current thinking is that we can make it so that Django/sinedon
# can read the current sinedon.cfg file and use that to populate settings.py.

import django
django.setup()
import os
from sinedon.models.leginon import SessionData 
from sinedon.models.leginon import CameraEMData
from sinedon.models.leginon import AcquisitionImageData
from sinedon.models.leginon import CorrectorPlanData
from sinedon.models.leginon import ScopeEMData
from sinedon.models.leginon import PixelSizeCalibrationData
import numpy
import mrcfile
import math

# DefectMap functions
def getImageDefectMap(correctorplandata : CorrectorPlanData, cameradata : CameraEMData):
    bad_rows = correctorplandata.bad_rows
    bad_rows = eval(bad_rows) if bad_rows else []
    bad_cols = correctorplandata.bad_cols
    bad_cols = eval(bad_cols) if bad_cols else []
    bad_pixels = correctorplandata.bad_pixels
    bad_pixels = eval(bad_pixels) if bad_pixels else []
    dx = cameradata.subd_dimension_x
    dy = cameradata.subd_dimension_y
    defect_map = numpy.zeros((dy,dx),dtype=numpy.int8)
    defect_map[bad_rows,:] = 1
    defect_map[:,bad_cols] = 1
    for px, py in bad_pixels:
        defect_map[py,px] = 1
    return defect_map

def makeDefectMrc(defect_map_path : str, defect_map : numpy.ndarray, frame_flip : int = 0, frame_rotate : int = 0, modified : bool = True) -> None:
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

# FmIntFile functions

def makeFmIntFile(fmintpath, nraw, size, raw_dose):
    '''
    calculate and set frame dose and create FmIntFile
    '''
    modulo = nraw % size
    int_div = nraw // size
    lines = []
    total_rendered_frames = int_div
    if modulo != 0:
        total_rendered_frames += 1
        lines.append('%d\t%d\t%.3f\n' % (modulo, modulo, raw_dose))
    lines.append('%d\t%d\t%.3f\n' % (int_div*size+modulo, size, raw_dose))
    with open(fmintpath,'w') as f:
        f.write(''.join(lines))
    return total_rendered_frames

# PixSize functions

def getPixelSize(imgdata):
    """
    use image data object to get pixel size
    multiplies by binning and also by 1e10 to return image pixel size in angstroms
    shouldn't have to lookup db already should exist in imgdict

    return image pixel size in Angstroms
    """
    magnification = imgdata.ref_scopeemdata_scope.magnification
    tem = imgdata.ref_scopeemdata_scope.ref_instrumentdata_tem
    ccdcamera = imgdata.ref_cameraemdata_camera.ref_instrumentdata_ccdcamera.def_id
    pixelsizedatas = PixelSizeCalibrationData.objects.filter(magnification=magnification, ref_instrumentdata_tem=tem, ref_instrumentdata_ccdcamera=ccdcamera)
    if not pixelsizedatas:
        raise RuntimeError("No pixelsize information was found for image %s with mag %d, tem id %d, ccdcamera id %d."
                        % (imgdata.filename, magnification, tem.def_id, ccdcamera))
    
    idx = 0
    pixelsizedata = pixelsizedatas[idx]
    oldestpixelsizedata = pixelsizedata
    while pixelsizedata.def_timestamp > imgdata.def_timestamp and idx < len(pixelsizedatas):
        idx += 1
        pixelsizedata = pixelsizedatas[idx]
        if pixelsizedata.def_timestamp < oldestpixelsizedata.def_timestamp:
            oldestpixelsizedata = pixelsizedata
    if pixelsizedata.def_timestamp > imgdata.def_timestamp:
        #logger.warning("There is no pixel size calibration data for this image, using oldest value.")
        pixelsizedata = oldestpixelsizedata
    binning = imgdata.ref_cameraemdata_camera.subd_binning_x
    pixelsize = pixelsizedata.pixelsize * binning
    return(pixelsize*1e10)

# Trunc Functions

# Forming the path to the log file is a problem for future me.
def getShiftsBetweenFrames(logfile):
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

def getFrameList(pixelsize : float, total_frames : int, nframe : int = None, startframe : int = None, driftlimit : int = None, logfile : str = ""):
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
        shifts = getShiftsBetweenFrames(logfile)
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

# Retrieves parameters from the database or calculates them.
def fetchParams(imageid : int, gainInput : str = "/tmp/tmp.mrc", force_cpu_flat : bool = False, has_bad_pixels : bool = False, 
                             is_align : bool = False, has_non_zero_dark : bool = False, rendered_frame_size : int = 1,
                             totaldose : bool = False) -> dict:
    imgdata=AcquisitionImageData.objects.get(def_id=imageid)
    correctorplandata=imgdata.ref_correctorplandata_corrector_plan
    sessiondata=imgdata.ref_sessiondata_session
    cameradata=imgdata.ref_cameraemdata_camera
    # keyword args for motioncor2 function
    kwargs={}

    # InMrc, InTiff, InEer
    # Get the path to the input image.
    if imgdata.mrc_image.endswith(".mrc"):
        kwargs["InMrc"]=os.path.join(sessiondata.image_path,imgdata.mrc_image)
    elif imgdata.mrc_image.endswith(".tif") or imgdata.filename.endswith(".tiff"):
        kwargs["InTiff"]=os.path.join(sessiondata.image_path,imgdata.mrc_image)
    elif imgdata.mrc_image.endswith(".eer"):
        kwargs["InEer"]=os.path.join(sessiondata.image_path,imgdata.mrc_image)
    else:
        raise RuntimeError("Unsupported file format for input path: %s." % imgdata.filename)

    # Gain
    # Get the reference image
    if gainInput:
        kwargs["Gain"]=gainInput
    else:
        gaindata=AcquisitionImageData.objects.get(def_id=imgdata.ref_normimagedata_norm)
        kwargs["Gain"]=os.path.join(sessiondata.image_path,gaindata.mrc_image)

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
    if not imgdata.ref_darkimagedata_dark:
        camera_name=imgdata.ref_cameraemdata_camera.ref_instrumentdata_ccdcamera.name
        # Why is this switch statement necessary?  Why not save default dimensions into the database instead of
        # hardcoding them in here?  (Original Appion has these hardcoded as part of object initialization.)
        if camera_name == "GatanK2":
            dimensions = (3710,3838)
        elif camera_name == 'GatanK3':
            dimensions = (8184,11520)
        elif camera_name == 'DE':
            dimensions = (4096,3072)
        elif camera_name in ['TIA','Falcon','Falcon3','Falcon4'] or (camera_name == 'Falcon4EC' and imgdata.ref_cameraemdata_camera.eer_frames):
            dimensions = (4096,4096)
        else:
            dimensions = None
        unscaled_darkarray =  numpy.zeros((dimensions[1],dimensions[0]), dtype=numpy.float32)
    else:
        darkdata = AcquisitionImageData.objects.get(def_id=imgdata.ref_darkimagedata_dark)
        unscaled_darkarray = mrcfile.read(darkdata.mrc_image) / darkdata.ref_cameraemdata_camera.nframes
    dark_path="/tmp/dark.mrc"
    mrcfile.write(dark_path, unscaled_darkarray, overwrite=True)
    kwargs["Dark"]=dark_path

    # DefectMap
 
    # TODO - conditional that triggers generation of the Defect Map?

    # FmIntFile
    # FmDose

    # This depends on whether or not we're using an EER formatted-input.
    # see https://github.com/nysbc/appion-slurm/blob/f376758762771073c0450d2bc3badc0fed6f8e66/appion/appionlib/apDDFrameAligner.py#L395-L399
    total_raw_frames = imgdata.ref_cameraemdata_camera.nframes
    if total_raw_frames is None:
        # older data or k2
        total_raw_frames =  int(imgdata.ref_cameraemdata_camera.exposure_time / imgdata.ref_cameraemdata_camera.frame_time)
    # avoid 0 for dark image scaling and frame list creation
    if total_raw_frames == 0:
        total_raw_frames = 1

    # totaldose is user-specified when the doseweight flag is passed
    # If this flag isn't specified, the database is queried.
    if not totaldose:
        totaldose = imgdata.ref_presetdata_preset.dose / 1e20
    if totaldose > 0:
        raw_dose = totaldose / total_raw_frames
    else:
        raw_dose = 0.03 #make fake dose similar to Falcon4EC 7 e/p/s

    if "InEer" not in kwargs.keys():
        kwargs['FmDose'] = totaldose/total_raw_frames
    else:
        kwargs['FmDose'] = raw_dose*rendered_frame_size
        fmintpath=os.path.abspath("/tmp/intfile.txt")
        # total_rendered_frames is used when writing out the motioncorr log
        total_rendered_frames = makeFmIntFile(fmintpath, total_raw_frames, rendered_frame_size, raw_dose)
        kwargs['FmInt'] = fmintpath

    # PixSize
    kwargs['PixSize']=getPixelSize(imgdata)

    # kV
    scopeemdata=imgdata.ref_scopeemdata_scope
    kwargs["kV"] = scopeemdata.high_tension/1000.0

    # Trunc
    camera_name=imgdata.ref_cameraemdata_camera.ref_instrumentdata_ccdcamera.name
    if camera_name in ["GatanK2","GatanK3"]:
        total_frames = max(1,int(imgdata.ref_cameraemdata_camera.exposure_time / imgdata.ref_cameraemdata_camera.frame_time))
    elif 'DE':
        total_frames = imgdata.ref_cameraemdata_camera.nframes
    elif camera_name in ['TIA','Falcon','Falcon3','Falcon4'] or (camera_name == 'Falcon4EC' and imgdata.ref_cameraemdata_camera.eer_frames):
        total_frames = imgdata.ref_cameraemdata_camera.nframes
    else:
        total_frames = imgdata.ref_cameraemdata_camera.nframes
    sumframelist = getFrameList(kwargs['PixSize'], total_frames)
    kwargs['Trunc'] = total_frames - sumframelist[-1] - 1

    # RotGain
    # FlipGain
    frame_aligner_flat = not (has_bad_pixels or not is_align or has_non_zero_dark)
    if not force_cpu_flat and frame_aligner_flat:
        kwargs['RotGain'] = cameradata.frame_rotate
        kwargs['FlipGain'] = cameradata.frame_flip
    else:
        kwargs['RotGain'] = 0
        kwargs['FlipGain'] = 0
    return kwargs

if __name__ == '__main__':
    imageid = 29123390
    kwargs = fetchParams(imageid)
    print(kwargs)
