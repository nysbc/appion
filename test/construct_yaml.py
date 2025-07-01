import os
import json, yaml
import sinedon.setup
sinedon.setup()
from appion.motioncorrection.retrieve.params import readImageMetadata
from appion.motioncorrection.calc.internal import calcMotionCorrLogPath

with open(os.path.join(os.getcwd(),"motioncor2_validation.json"), "r") as f:
    validationData=json.load(f)

params={}
params['test_calcInputType']=[]
params['test_calcFmDose']=[]
params['test_calcPixelSize']=[]
params["test_calcKV"]=[]
params['test_calcMotionCorrLogPath']=[]


for imageid in validationData.keys():
    imgmetadata=readImageMetadata(imageid, False, True, False)

    if "InEer" in validationData[imageid]["motioncorflags"].keys():
        params['test_calcInputType'].append({"fpath": validationData[imageid]["motioncorflags"]["InEer"], "expected" : "InEer"})
        framestackpath=validationData[imageid]["motioncorflags"]["InEer"]
    elif "InMrc" in validationData[imageid]["motioncorflags"].keys():
        params['test_calcInputType'].append({"fpath": validationData[imageid]["motioncorflags"]["InMrc"], "expected" : "InMrc"})
        framestackpath=validationData[imageid]["motioncorflags"]["InMrc"]
    elif "InTiff" in validationData[imageid]["motioncorflags"].keys():
        params['test_calcInputType'].append({"fpath": validationData[imageid]["motioncorflags"]["InTiff"], "expected" : "InTiff"})
        framestackpath=validationData[imageid]["motioncorflags"]["InTiff"]
    else:
        framestackpath=None
    if "totaldose" in validationData[imageid]["appionflags"].keys():
        totaldose = float(validationData[imageid]["appionflags"]["totaldose"])
    else:
        totaldose = None
    if "InEer" in validationData[imageid]["motioncorflags"].keys():
        params['test_calcFmDose'].append({"total_raw_frames" : imgmetadata['total_raw_frames'], 
                                          "exposure_time" : imgmetadata['exposure_time'], 
                                          "frame_time" : imgmetadata['frame_time'], 
                                          "dose" : imgmetadata['dose'], 
                                          "rendered_frame_size" : validationData[imageid]["appionflags"]['rendered_frame_size'], 
                                          "totaldose" : totaldose, 
                                          "is_eer" : True,
                                          "expected": validationData[imageid]["motioncorflags"]["FmDose"] })
    else:
        params['test_calcFmDose'].append({"total_raw_frames" : imgmetadata['total_raw_frames'], 
                                          "exposure_time" : imgmetadata['exposure_time'], 
                                          "frame_time" : imgmetadata['frame_time'], 
                                          "dose" : imgmetadata['dose'], 
                                          "rendered_frame_size" : validationData[imageid]["appionflags"]['rendered_frame_size'], 
                                          "totaldose" : totaldose, 
                                          "is_eer" : False,
                                          "expected": validationData[imageid]["motioncorflags"]["FmDose"]})
    params['test_calcPixelSize'].append({"pixelsizedatas" : imgmetadata['pixelsizedata'], 
                                          "binning" : imgmetadata['binning'], 
                                          "imgdata_timestamp" : imgmetadata['imgdata_timestamp'], 
                                          "expected": float(validationData[imageid]["motioncorflags"]["PixSize"])})
    params['test_calcKV'].append({"high_tension": imgmetadata['high_tension'],"expected": float(validationData[imageid]["motioncorflags"]["kV"])})
    framestackpath=os.path.join(validationData[imageid]["appionflags"]["rundir"],os.path.basename(framestackpath))
    motioncorr_log_path=calcMotionCorrLogPath(framestackpath)
    params['test_calcMotionCorrLogPath'].append({"framestackpath":framestackpath, "expected": motioncorr_log_path})

with open("./test_motioncorrection.yml","w") as f:
    yaml.dump(params, f)