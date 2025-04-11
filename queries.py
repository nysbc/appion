#!/usr/bin/env python

import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()
import db.models
import settings
from db.models import SessionData 
from db.models import CameraEMData
from db.models import AcquisitionImageData
from db.models import CorrectorPlanData
from db.models import ScopeEMData
from db.models import PixelSizeCalibrationData
import numpy
import mrcfile

# Functions / dummy variables for user inputs
gainInput=False
force_cpu_flat=False
has_bad_pixels=False
is_align=False
has_non_zero_dark=False

def makeDarkMrc(input):
    """
    Returns a string containing the path to the dark image.
    """
    return "/tmp/tmp.mrc"

# def getSingleFrameDarkArray(self):
#     try:
#         darkdata = self.getRefImageData('dark')
#         nframes = self.getNumberOfFrameSavedFromImageData(darkdata)
#         return darkdata['image'] / nframes
#     except:
#         dimension = self.getDefaultDimension()
#         return numpy.zeros((dimension['y'],dimension['x']))
        
# def setupDarkNormMrcs(frameprocess_dir, use_full_raw_area=False):
#     '''
#     Creates local reference files for gain/dark-correcting the stack of frames
#     '''
#     # apDisplay.printMsg('Will setupDarkNormMrcs make dark/gain? %s' % (self.correct_dark_gain,))
#     if not self.correct_dark_gain or self.getRefImageData('norm') is None: 
#         self.dark_path = None
#         self.norm_path = None
#         return
#     sys.stdout.write('\a')
#     sys.stdout.flush()
#     # if use_full_raw_area is True:
#     #     apDisplay.displayError('use_full_raw_area when image is cropped is not implemented for gpu')
#     get_new_refs = self.__conditionChanged(1,use_full_raw_area)
#     # apDisplay.printMsg('decide to get new refs based on condition change ? %s' % (get_new_refs,))
#     # o.k. to set attribute now that condition change is checked
#     # at least write dark and norm image once
#     if get_new_refs or not hasattr(self,'dark_path'):
#         # set camera info for loading frames
#         self.setCameraInfo(1,use_full_raw_area)

#         # output dark
#         unscaled_darkarray = self.getSingleFrameDarkArray()
#         self.dark_path = os.path.join(frameprocess_dir,'dark-%s-%d-%d.mrc' % (self.hostname,self.gpuid, os.getpid()))
#         mrc.write(dark_path,unscaled_darkarray)

#         # output norm
#         normdata = self.getRefImageData('norm')
#         if normdata['bright']:
#             apDisplay.printWarning('From Bright Reference %s' % (normdata['bright']['filename'],))
#         if self.use_frame_aligner_flat:
#             normarray = normdata['image']
#             self.norm_path = os.path.join(frameprocess_dir,'norm-%s-%d-%d.mrc' % (self.hostname,self.gpuid,os.getpid()))
#             apDisplay.printWarning('Save Norm Reference %s to %s' % (normdata['filename'],self.norm_path))
#             try:
#                 mrc.write(normarray,self.norm_path)
#             except Exception as e:
#                 apDisplay.printError('Norm array not saved. Possible problem of reading from %s' % normdata.getpath())


# A typical run.

imageid=29123390
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
    kwargs["Gain"]="/tmp/tmp.mrc"
else:
    gaindata=AcquisitionImageData.objects.get(def_id=imgdata.ref_normimagedata_norm)
    kwargs["Gain"]=os.path.join(sessiondata.image_path,gaindata.mrc_image)

# Dark - TODO
# Get the dark image.  Create it if it does not exist.
kwargs["Dark"]=imgdata.ref_darkimagedata_dark
if not kwargs["Dark"]:
    kwargs["Dark"]=makeDarkMrc(input)

# DefectMap
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
    # flip and rotate map_array.  Therefore, do the oposite of
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

def testImageDefectMap():
    correctorplandata=CorrectorPlanData.objects.get(def_id=2)
    cameradata=CameraEMData.objects.get(def_id=9)
    map=getImageDefectMap(correctorplandata,cameradata)
    frame_flip = cameradata.frame_flip
    frame_rotate = cameradata.frame_rotate
    print(map)
    makeDefectMrc("/tmp/defect.mrc", map, frame_flip, frame_rotate)
    correctorplandata=CorrectorPlanData.objects.get(def_id=10)
    cameradata=CameraEMData.objects.get(def_id=595080)
    map=getImageDefectMap(correctorplandata,cameradata)
    print(map)
testImageDefectMap()

# FmIntFile - TODO

# FmDose - TODO

# PixSize
def getPixelSize(imgdata):
    """
    use image data object to get pixel size
    multiplies by binning and also by 1e10 to return image pixel size in angstroms
    shouldn't have to lookup db already should exist in imgdict

    return image pixel size in Angstroms
    """
    magnification = imgdata.ref_scopeemdata_scope.magnification
    tem = imgdata.ref_scopeemdata_scope.ref_instrumentdata_tem
    ccdcamera = imgdata.ref_cameraemdata_camera.ref_instrumentdata_ccdcamera
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
kwargs['PixSize']=getPixelSize(imgdata)
print(cameradata.subd_pixel_size_x)

# kV
scopeemdata=imgdata.ref_scopeemdata_scope
kwargs["kV"] = scopeemdata.high_tension/1000.0

# Trunc - TODO

def getShiftsBetweenFrames(logfile):
    '''
    Return a list of shift distance by frames. item 0 is fake. item 1 is distance between
    frame 0 and frame 1
    '''
    if not os.path.isfile(logfile):
        raise RuntimeError('No alignment log file %s found for thresholding drift' % logfile)
    shifts=[]
    #positions = ddinfo.readPositionsFromAlignLog(logfile)
    #shifts = ddinfo.calculateFrameShiftFromPositions(positions)
    #logger.debug('Got %d shifts' % (len(shifts)-1))
    return shifts

def getFrameList(pixelsize : float, total_frames : int, nframe : int = None, startframe : int = None, driftlimit : int = None):
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
        shifts = getShiftsBetweenFrames()
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

# TODO total_frames varies depending upon the camera used.
# Need to account for different camera types.
# Search for getNumberOfFrameSavedFromImageData to see how different cameras
# populate this variable.
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

print(kwargs)