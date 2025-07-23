#!/usr/bin/env python

import sinedon.setup
sinedon.setup()
from appion.motioncorrection.retrieve.params import readImageMetadata
import appion
import json
import os
from time import time

t=time()

testdatadir=os.path.join(os.path.dirname(appion.__file__),"../test","test_motioncorrection_utils","readimagemetadata_check","samples",str(t))
if not os.path.isdir(testdatadir):
    os.makedirs(testdatadir)

images=list(range(25,500, 10))

for image in images:
    imgmetadata=readImageMetadata(image)
    imgmetadata["imgdata_timestamp"]=imgmetadata["imgdata_timestamp"].isoformat()
    newpixelsizedata=[]
    for record in imgmetadata["pixelsizedata"]:
        record["timestamp"]=record["timestamp"].isoformat()
        newpixelsizedata.append(record)
    print(imgmetadata)
    fname="%d.json" % image
    with open(os.path.join(testdatadir,fname), "w") as f:
        json.dump(imgmetadata, f)