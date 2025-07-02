import os
from glob import glob
import appion
import json, yaml
import sinedon.setup
sinedon.setup()
from appion.motioncorrection.retrieve.params import readImageMetadata
from appion.motioncorrection.calc.internal import calcMotionCorrLogPath, filterFrameList, calcTotalFrames

with open(os.path.join(os.getcwd(),"motioncor2_validation.json"), "r") as f:
    validationData=json.load(f)

params={}
params['test_calcInputType']=[]
params['test_calcFmDose']=[]
params['test_calcPixelSize']=[]
params['test_filterFrameList']=[]
params['test_calcTotalFrames']=[]
params['test_calcTrunc']=[]
params["test_calcKV"]=[]
params["test_calcRotFlipGain"]=[]
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
    params['test_filterFrameList'].append({"pixsize" : float(validationData[imageid]["motioncorflags"]["PixSize"]),
                                            "nframes" : imgmetadata['nframes'], 
                                            "shifts" : [], 
                                            "expected" : list(filterFrameList(float(validationData[imageid]["motioncorflags"]["PixSize"]), imgmetadata['nframes'], []))})
    params['test_calcTotalFrames'].append({"camera_name" : imgmetadata['camera_name'], 
                                           "exposure_time" : imgmetadata['exposure_time'], 
                                           "frame_time" : imgmetadata['frame_time'], 
                                           "nframes" : imgmetadata['nframes'], 
                                           "eer_frames" : imgmetadata['eer_frames'],
                                           "expected" : calcTotalFrames(imgmetadata['camera_name'], imgmetadata['exposure_time'], imgmetadata['frame_time'], imgmetadata['nframes'], imgmetadata['eer_frames'])})
    if "Trunc" in validationData[imageid]["motioncorflags"].keys():
        trunc=validationData[imageid]["motioncorflags"]["Trunc"]
    else:
        trunc="%.2f" % 0
    params['test_calcTrunc'].append({"total_frames" : calcTotalFrames(imgmetadata['camera_name'], imgmetadata['exposure_time'], imgmetadata['frame_time'], imgmetadata['nframes'], imgmetadata['eer_frames']),
                                     "sumframelist" : list(filterFrameList(float(validationData[imageid]["motioncorflags"]["PixSize"]), imgmetadata['nframes'], [])),
                                     "expected" : trunc})                
    params['test_calcKV'].append({"high_tension": imgmetadata['high_tension'],"expected": float(validationData[imageid]["motioncorflags"]["kV"])})
    force_cpu_flat= 'force_cpu_flat' in validationData[imageid]["appionflags"].keys()
    params["test_calcRotFlipGain"].append({"frame_rotate":imgmetadata["frame_rotate"], 
                                           "frame_flip" : imgmetadata["frame_flip"], 
                                           "force_cpu_flat" : force_cpu_flat, 
                                           "frame_aligner_flat" : imgmetadata["frame_aligner_flat"], 
                                           "expected_RotGain" : int(validationData[imageid]["motioncorflags"]["RotGain"]), 
                                           "expected_FlipGain" : int(validationData[imageid]["motioncorflags"]["FlipGain"])})
    framestackpath=os.path.join(validationData[imageid]["appionflags"]["rundir"],os.path.basename(framestackpath))
    motioncorr_log_path=calcMotionCorrLogPath(framestackpath)
    params['test_calcMotionCorrLogPath'].append({"framestackpath":framestackpath, "expected": motioncorr_log_path})

params['test_calcImageDefectMap']=[]
for dm in glob(os.path.join(os.path.dirname(appion.__file__),"../test","*.npz")):
    params['test_calcImageDefectMap'].append({"dm":os.path.basename(dm)})

with open("./test_motioncorrection.yml","w") as f:
    yaml.dump(params, f)