from appion.motioncor import getParams
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
    if "totaldose" in validationData[imageid]["appionflags"].keys():
        if validationData[imageid]["appionflags"]["totaldose"]:
            totaldose = int(validationData[imageid]["appionflags"]["totaldose"])
        else:
            totaldose = 0.0
    else:
        totaldose = 0.0
    # Globbing the input file can fail because users may have deleted their data after transfer.
    try:
        kwargs=getParams(int(imageid), gain_input="/tmp/gain.mrc", dark_input = "/tmp/dark.mrc", fmintfile="/tmp/fmintfile.txt", force_cpu_flat=force_cpu_flat,is_align=is_align,rendered_frame_size=rendered_frame_size, totaldose=totaldose)
    except Exception as e:
        print(e)
        continue
    # if "InMrc" in kwargs.keys():
    #     print(validationData[imageid]["motioncorflags"]["InMrc"])
    #     assert kwargs["InMrc"] == validationData[imageid]["motioncorflags"]["InMrc"]
    # elif "InTiff" in kwargs.keys():
    #     print(validationData[imageid]["motioncorflags"]["InTiff"])
    #     assert kwargs["InTiff"] == validationData[imageid]["motioncorflags"]["InTiff"]
    # elif "InEer" in kwargs.keys():
    #     print(validationData[imageid]["motioncorflags"]["InEer"])
    #     assert kwargs["InEer"] == validationData[imageid]["motioncorflags"]["InEer"]
    # print("FmDose: Does %.3f == %s?" % (kwargs["FmDose"], validationData[imageid]["motioncorflags"]["FmDose"]))
    # assert "%.3f" % kwargs["FmDose"] == validationData[imageid]["motioncorflags"]["FmDose"]
    # print("kV: Does %d == %s?" % (kwargs["kV"], validationData[imageid]["motioncorflags"]["kV"]))
    # assert "%d" % kwargs["kV"] == validationData[imageid]["motioncorflags"]["kV"]
    #print("RotGain: Does %d == %s?" % (kwargs["RotGain"], validationData[imageid]["motioncorflags"]["RotGain"]))
    #assert "%d" % kwargs["RotGain"] == validationData[imageid]["motioncorflags"]["RotGain"]
    #print("FlipGain: Does %d == %s?" % (kwargs["FlipGain"], validationData[imageid]["motioncorflags"]["FlipGain"]))
    #assert "%d" % kwargs["FlipGain"] == validationData[imageid]["motioncorflags"]["FlipGain"]
    try:
        print("PixSize: Does %.3f == %s?" % (kwargs["PixSize"], validationData[imageid]["motioncorflags"]["PixSize"]))
        assert "%.3f" % kwargs["PixSize"] == validationData[imageid]["motioncorflags"]["PixSize"]
    except Exception as e:
        print(e)
        continue
    # print("Trunc: Does %d == %s?" % (kwargs["Trunc"], validationData[imageid]["motioncorflags"]["Trunc"]))
    # assert "%.3f" % kwargs["Trunc"] == validationData[imageid]["motioncorflags"]["Trunc"]