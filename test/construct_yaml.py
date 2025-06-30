import os
import json, yaml
import sinedon.setup
sinedon.setup()
from appion.motioncorrection.retrieve.params import readImageMetadata

with open(os.path.join(os.getcwd(),"motioncor2_validation.json"), "r") as f:
    validationData=json.load(f)

params={}
params['test_calcInputType']=[]
params['test_calcPixelSize']=[]
params["test_calcKV"]=[]


for imageid in validationData.keys():
    imgmetadata=readImageMetadata(imageid, False, True, False)

    if "InEer" in validationData[imageid]["motioncorflags"].keys():
        params['test_calcInputType'].append({"fpath": validationData[imageid]["motioncorflags"]["InEer"], "expected" : "InEer"})
    elif "InMrc" in validationData[imageid]["motioncorflags"].keys():
        params['test_calcInputType'].append({"fpath": validationData[imageid]["motioncorflags"]["InMrc"], "expected" : "InMrc"})
    elif "InTiff" in validationData[imageid]["motioncorflags"].keys():
        params['test_calcInputType'].append({"fpath": validationData[imageid]["motioncorflags"]["InTiff"], "expected" : "InTiff"})
    params['test_calcPixelSize'].append({"pixelsizedatas" : imgmetadata['pixelsizedata'], 
                                          "binning" : imgmetadata['binning'], 
                                          "imgdata_timestamp" : imgmetadata['imgdata_timestamp'], 
                                          "expected": float(validationData[imageid]["motioncorflags"]["PixSize"])})
    params['test_calcKV'].append({"high_tension": imgmetadata['high_tension'],"expected": float(validationData[imageid]["motioncorflags"]["kV"])})

with open("./test_motioncorrection.yml","w") as f:
    yaml.dump(params, f)