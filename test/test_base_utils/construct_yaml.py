import os
import appion
import yaml
from random import random, randint
from math import radians
from appion.base.calc import filterImages, calcSkipTiltAngle, calcSlicedImageSet

params={}
params['test_filterImages']=[]
params['test_calcSkipTiltAngle']=[]
params['test_calcSlicedImageSet']=[]

for _ in range(5):
    first_image=int(random()*10000)
    all_images=set(range(first_image, first_image+5000))
    done_images=set(range(first_image, first_image+128))
    reprocess_images=set([first_image + int(random()*10) for _ in range(2)])
    rejected_images=set([first_image+50])
    expected=filterImages(all_images, done_images, reprocess_images, rejected_images)
    params['test_filterImages'].append({
        "all_images" : list(all_images),
        "done_images" : list(done_images),
        "reprocess_images" : list(reprocess_images),
        "rejected_images" : list(rejected_images),
        "expected" : list(expected)
    })

tilt_angles=[4.0, 25.0, 35.0, -1.0, 1.0]
angle_types=["notilt", "hightilt", "lowtilt", "minustilt", "plustilt"]
units=["degrees", "radians", "zorkmids"]
for tilt_angle in tilt_angles:
    for tilt_angle_type in angle_types:
        for unit in units:
            if unit == "radians":
                tilt_angle=radians(tilt_angle)
            try:
                expected=calcSkipTiltAngle(tilt_angle, tilt_angle_type, unit)
            except RuntimeError:
                expected=None
            params['test_calcSkipTiltAngle'].append({
                "tilt_angle" : tilt_angle,
                "tilt_angle_type" : tilt_angle_type,
                "unit" : unit,
                "expected" : expected
            })

for _ in range(5):
    first_image=int(random()*10000)
    images=set(range(first_image, first_image+5000))
    startstop=[randint(first_image, first_image+5000) for _ in range(2)]
    startimgid=min(startstop)
    endimgid=max(startstop)
    expected=calcSlicedImageSet(images, startimgid, endimgid)
    params['test_calcSlicedImageSet'].append({
        "images" : list(images),
        "startimgid" : startimgid,
        "endimgid" : endimgid,
        "expected" : list(expected)
    })

with open(os.path.join(os.path.dirname(appion.__file__),"../test","./test_base.yml"),"w") as f:
    yaml.dump(params, f)