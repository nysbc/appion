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
imageid=29123390
x=AcquisitionImageData.objects.get(def_id=imageid)
print(x.filename)
print(x.ref_normimagedata_norm)
print(x.ref_darkimagedata_dark)
print(x.ref_correctorplandata_corrector_plan)
print(x.ref_scopeemdata_scope
y=x.ref_cameraemdata_camera
print(y.subd_pixel_size_x)
print(y.frame_flip)
print(y.frame_rotate)
