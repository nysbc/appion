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

# Functions / dummy variables for user inputs
gainInput=False

def makeDark(input):
    """
    Returns a string containing the path to the dark image.
    """
    return "/tmp/tmp.mrc"

def getImageDefectMap(correctorplandata, cameradata):
    plan = {}
    bad_rows = list(correctorplandata.bad_rows)
    bad_cols = list(correctorplandata.bad_cols)
    if correctorplandata.bad_pixels:
        bad_pixels  = list(correctorplandata.bad_pixels)
    else:
        bad_pixels = []
    dx = cameradata.subd_dimension_x
    dy = cameradata.subd_dimension_y
    map_array = numpy.zeros((dy,dx),dtype=numpy.int8)
    for r in bad_rows:
        map_array[r,:] = 1
    for c in bad_cols:
        map_array[:,c] = 1
    for p in bad_pixels:
        px, py = p
        map_array[py,px] = 1
    return map_array

imageid=29123390
imgdata=AcquisitionImageData.objects.get(def_id=imageid)
correctorplandata=imgdata.ref_correctorplandata_corrector_plan
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
    kwargs["Dark"]=makeDark(input)

print(imgdata.ref_correctorplandata_corrector_plan)
print(imgdata.ref_scopeemdata_scope)
print(cameradata.subd_pixel_size_x)
print(cameradata.frame_flip)
print(cameradata.frame_rotate)
print(kwargs)
