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
import numpy
import mrcfile

# Functions / dummy variables for user inputs
gainInput=False

def makeDarkMrc(input):
    """
    Returns a string containing the path to the dark image.
    """
    return "/tmp/tmp.mrc"

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

# A typical run.

imageid=29123390
imgdata=AcquisitionImageData.objects.get(def_id=imageid)
correctorplandata=CorrectorPlanData.objects.get(def_id=imgdata.ref_correctorplandata_corrector_plan)
sessiondata=imgdata.ref_sessiondata_session
cameradata=imgdata.ref_cameraemdata_camera
# keyword args for motioncor2 function
kwargs={}

# Get the path to the input image.
if imgdata.mrc_image.endswith(".mrc"):
    kwargs["InMrc"]=os.path.join(sessiondata.image_path,imgdata.mrc_image)
elif imgdata.mrc_image.endswith(".tif") or imgdata.filename.endswith(".tiff"):
    kwargs["InTiff"]=os.path.join(sessiondata.image_path,imgdata.mrc_image)
elif imgdata.mrc_image.endswith(".eer"):
    kwargs["InEer"]=os.path.join(sessiondata.image_path,imgdata.mrc_image)
else:
    raise RuntimeError("Unsupported file format for input path: %s." % imgdata.filename)

# Get the reference image
if gainInput:
    kwargs["Gain"]="/tmp/tmp.mrc"
else:
    gaindata=AcquisitionImageData.objects.get(def_id=imgdata.ref_normimagedata_norm)
    kwargs["Gain"]=os.path.join(sessiondata.image_path,gaindata.mrc_image)

# Get the dark image.  Create it if it does not exist.
kwargs["Dark"]=imgdata.ref_darkimagedata_dark
if not kwargs["Dark"]:
    kwargs["Dark"]=makeDarkMrc(input)

print(imgdata.ref_correctorplandata_corrector_plan)
print(imgdata.ref_scopeemdata_scope)
print(cameradata.subd_pixel_size_x)
print(cameradata.frame_flip)
print(cameradata.frame_rotate)
print(kwargs)
testImageDefectMap()