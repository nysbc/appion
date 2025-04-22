from appion.motioncor import fetchParams
import os
import json

with open(os.path.join(os.getcwd(),"motioncor2_validation.json"), "r") as f:
    validationData=json.load(f)

for imageid in validationData.keys():
    #gainInput : str = "/tmp/tmp.mrc", 
    if "force_cpu_flat" in validationData[imageid]["appionflags"].keys():
        force_cpu_flat = True
    else:
        force_cpu_flat = False
    if "align" in validationData[imageid]["appionflags"].keys():
        is_align = True
    else:
        is_align = False
    if "rendered_frame_size" in validationData[imageid]["appionflags"].keys():
        rendered_frame_size = int(validationData[imageid]["appionflags"]["rendered_frame_size"])
    else:
        rendered_frame_size = 1
    if "doseweight" in validationData[imageid]["appionflags"].keys():
        if validationData[imageid]["appionflags"]["doseweight"]:
            totaldose = int(validationData[imageid]["appionflags"]["doseweight"])
        else:
            totaldose = 0.0
    else:
        totaldose = 0.0
    kwargs=fetchParams(int(imageid), force_cpu_flat=force_cpu_flat,is_align=is_align,rendered_frame_size=rendered_frame_size, totaldose=totaldose)
    print(kwargs)