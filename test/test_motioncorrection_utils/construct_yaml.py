import os
from glob import glob
#import shutil
import copy
import appion
import json, yaml
import sinedon.setup
sinedon.setup()
from appion.motioncorrection.retrieve.params import readImageMetadata
from appion.motioncorrection.retrieve.logs import retrieveLogParser
from appion.motioncorrection.calc.internal import calcMotionCorrLogPath, filterFrameList, calcTotalFrames, calcTotalRenderedFrames, calcFrameShiftFromPositions, calcFrameStats, calcAlignedCamera
from appion.motioncorrection.calc.external import constructMotionCorCmd
from sinedon.models.leginon import CameraEMData

with open(os.path.join(os.path.dirname(appion.__file__),"../test","test_motioncorrection_utils","motioncor2_validation.json"), "r") as f:
    validationData=json.load(f)

params={}
params['test_calcInputType']=[]
params['test_calcFmDose']=[]
params['test_calcTotalRenderedFrames']=[]
params['test_calcPixelSize']=[]
params['test_filterFrameList']=[]
params['test_calcTotalFrames']=[]
params['test_calcTrunc']=[]
params["test_calcKV"]=[]
params["test_calcRotFlipGain"]=[]
params["test_calcFrameStats"]=[]
params["test_calcFrameShiftFromPositions"]=[]
params['test_calcAlignedCamera']=[]
params['test_calcMotionCorrLogPath']=[]
params['test_constructMotionCorKwargs']=[]
params['test_constructMotionCorCmd']=[]
params['test_parseMotionCorLog']=[]

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
        
    params['test_calcTotalRenderedFrames'].append({"total_raw_frames" : imgmetadata['total_raw_frames'], 
                                                   "rendered_frame_size" : int(validationData[imageid]["appionflags"]['rendered_frame_size']),
                                                   "expected" : calcTotalRenderedFrames(imgmetadata['total_raw_frames'], int(validationData[imageid]["appionflags"]['rendered_frame_size']))})
    params['test_calcPixelSize'].append({"pixelsizedatas" : imgmetadata['pixelsizedata'], 
                                          "binning" : imgmetadata['binning'], 
                                          "imgdata_timestamp" : imgmetadata['imgdata_timestamp'], 
                                          "expected": float(validationData[imageid]["motioncorflags"]["PixSize"])})
    framelist=list(filterFrameList(float(validationData[imageid]["motioncorflags"]["PixSize"]), imgmetadata['nframes'], []))
    params['test_filterFrameList'].append({"pixsize" : float(validationData[imageid]["motioncorflags"]["PixSize"]),
                                            "nframes" : imgmetadata['nframes'], 
                                            "shifts" : [], 
                                            "expected" : framelist})
    nframes=calcTotalFrames(imgmetadata['camera_name'], imgmetadata['exposure_time'], imgmetadata['frame_time'], imgmetadata['nframes'], imgmetadata['eer_frames'])
    params['test_calcTotalFrames'].append({"camera_name" : imgmetadata['camera_name'], 
                                           "exposure_time" : imgmetadata['exposure_time'], 
                                           "frame_time" : imgmetadata['frame_time'], 
                                           "nframes" : imgmetadata['nframes'], 
                                           "eer_frames" : imgmetadata['eer_frames'],
                                           "expected" : nframes})
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
    
    if "Trim" in validationData[imageid]["motioncorflags"].keys():
        trim=validationData[imageid]["motioncorflags"]["Trim"]
    else:
        trim=0
    camdata = CameraEMData.objects.get(def_id=imgmetadata['camera_id'])
    if "square" in validationData[imageid]["appionflags"].keys():
        square=True
    else:
        square=False
    if "bin" in validationData[imageid]["appionflags"].keys():
        bin=float(validationData[imageid]["appionflags"]['bin'])
    else:
        bin=1.0
    expected_aligned_binning, expected_aligned_dimensions, expected_aligned_offset, expected_use_frames = calcAlignedCamera((camdata.subd_dimension_x, camdata.subd_dimension_y), 
                                                                                        square, 
                                                                                        (camdata.subd_binning_x, camdata.subd_binning_y), 
                                                                                        (camdata.subd_offset_x, camdata.subd_offset_y), 
                                                                                        bin, 
                                                                                        trim, 
                                                                                        framelist, 
                                                                                        nframes)

    params['test_calcAlignedCamera'].append({"subd_dimension_x" : camdata.subd_dimension_x, 
                                             "subd_dimension_y" : camdata.subd_dimension_y, 
                                             "square_output" : square, 
                                             "subd_binning_x" : camdata.subd_binning_x, 
                                             "subd_binning_y" : camdata.subd_binning_y,
                                             "subd_offset_x" : camdata.subd_offset_x, 
                                             "subd_offset_y" : camdata.subd_offset_y, 
                                             "binning" : bin, 
                                             "trimming_edge" : trim, 
                                             "framelist" : framelist, 
                                             "nframes" : nframes,
                                             "expected_aligned_binning_x" : expected_aligned_binning[0], 
                                             "expected_aligned_binning_y" : expected_aligned_binning[1], 
                                             "expected_aligned_dimensions_x" : expected_aligned_dimensions[0], 
                                             "expected_aligned_dimensions_y" : expected_aligned_dimensions[1], 
                                             "expected_aligned_offset_x" : expected_aligned_offset[0], 
                                             "expected_aligned_offset_y" : expected_aligned_offset[1], 
                                             "expected_use_frames" : expected_use_frames})
    framestackpath=os.path.join(validationData[imageid]["appionflags"]["rundir"],os.path.basename(framestackpath))
    motioncorr_log_path=calcMotionCorrLogPath(framestackpath)
    params['test_calcMotionCorrLogPath'].append({"framestackpath":framestackpath, "expected": motioncorr_log_path})
    test_constructMotionCorKwargs={}
    test_constructMotionCorKwargs['imgmetadata']=imgmetadata
    test_constructMotionCorKwargs['args']=validationData[imageid]["appionflags"]
    test_constructMotionCorKwargs['args']['Bft_global'] = int(test_constructMotionCorKwargs['args']['Bft_global'])
    test_constructMotionCorKwargs['args']['Bft_local'] = int(test_constructMotionCorKwargs['args']['Bft_local'])
    test_constructMotionCorKwargs['args']['bin'] = float(test_constructMotionCorKwargs['args']['bin'])
    if "Tol" not in test_constructMotionCorKwargs['args'].keys():
        test_constructMotionCorKwargs['args']["Tol"]=0.5
    if "bin" not in test_constructMotionCorKwargs['args'].keys():
        test_constructMotionCorKwargs['args']["bin"]=1.0
    if 'force_cpu_flat' not in test_constructMotionCorKwargs['args'].keys():
        test_constructMotionCorKwargs['args']['force_cpu_flat']=False
    else:
        test_constructMotionCorKwargs['args']['force_cpu_flat']=True
    if 'totaldose' in test_constructMotionCorKwargs['args'].keys():
        test_constructMotionCorKwargs['args']['totaldose']=float(test_constructMotionCorKwargs['args']['totaldose'])
    if 'FmRef' in test_constructMotionCorKwargs['args'].keys():
        test_constructMotionCorKwargs['args']['FmRef']=int(test_constructMotionCorKwargs['args']['FmRef'])
    test_constructMotionCorKwargs['input_path']=framestackpath
    test_constructMotionCorKwargs['expected_kwargs']=validationData[imageid]["motioncorflags"]
    #if "FtBin" not in test_constructMotionCorKwargs['expected_kwargs'].keys():
    #    test_constructMotionCorKwargs['expected_kwargs']["FtBin"]="1.0"
    #if "FmRef" not in test_constructMotionCorKwargs['expected_kwargs'].keys():
    #    test_constructMotionCorKwargs['expected_kwargs']["FmRef"]="0"
    params['test_constructMotionCorKwargs'].append(test_constructMotionCorKwargs)

    kwargs=copy.deepcopy(validationData[imageid]["motioncorflags"])
    kwargs["FmDose"] = float(kwargs["FmDose"])
    kwargs["kV"] = int(kwargs["kV"])
    kwargs["RotGain"] = int(kwargs["RotGain"])
    kwargs["FlipGain"] = int(kwargs["FlipGain"])
    kwargs["PixSize"] = float(kwargs["PixSize"])
    if "Trunc" in kwargs.keys():
        kwargs["Trunc"] = float(kwargs["Trunc"])
    if "FtBin" in kwargs.keys():
        kwargs['FtBin'] == float(kwargs['FtBin'])
    params['test_constructMotionCorCmd'].append({"kwargs" : kwargs,
                                                 "executable" : "motioncor2",
                                                 "expected" : constructMotionCorCmd("motioncor2", kwargs)})

# m25apr22e (7858), m25apr23d (7873), m25apr02e (7605)

logparser=retrieveLogParser("MotionCor2 version 1.5.0")
uploadAlignStatsTest=[30117940, 30157838, 29123499]
for imageid in uploadAlignStatsTest:
    imgmetadata=readImageMetadata(imageid, False, True, False)
    #motioncorlogpath=glob(os.path.join("./logs",imgmetadata['image_filename']+"*motioncor2.txt"))[0]
    #shutil.copy(motioncorlogpath, "./%d.motioncor2.log" % imageid)
    motioncorlogpath="./logs/%d.motioncor2.log" % imageid
    with open(motioncorlogpath, "r") as f:
        outbuffer=f.readlines()
        outbuffer=[s.replace("\n","") for s in outbuffer]
        outbuffer=[s for s in outbuffer if s]
        logdata=logparser(outbuffer)
    shifts=logdata["shifts"]
    nframes=imgmetadata["nframes"]
    pixel_shifts = calcFrameShiftFromPositions(shifts, nframes - len(shifts)+1)
    max_drifts, median = calcFrameStats(pixel_shifts)
    shifts=[list(i) for i in shifts]
    params["test_calcFrameShiftFromPositions"].append({"shifts" : shifts,
                                                      "nframes" : nframes - len(shifts)+1,
                                                      "expected" : pixel_shifts})
    max_drifts=[list(i) for i in max_drifts]
    params["test_calcFrameStats"].append({"pixel_shifts": pixel_shifts,
                                          "expected_max_drifts" : list(max_drifts),
                                          "expected_median" : float(median)})
    

params['test_calcImageDefectMap']=[]
for dm in glob(os.path.join(os.path.dirname(appion.__file__),"../test","*.npz")):
    params['test_calcImageDefectMap'].append({"dm":os.path.basename(dm)})

outbuffer=[]
with open(os.path.join(os.path.dirname(appion.__file__),"../test","test_motioncorrection_utils","motioncor2_1.5.0_log.txt"), "r") as f:
    for line in f:
        outbuffer.append(line.rstrip("\n"))
logparser=retrieveLogParser("MotionCor2 version 1.5.0")
logdata=logparser(copy.deepcopy(outbuffer))
logdata["shifts"]=[list(coords) for coords in logdata["shifts"]]
params['test_parseMotionCorLog'].append({
    "outbuffer" : outbuffer,
    "shift_start" : "Full-frame alignment shift",
    "expected" : logdata
})

outbuffer=[]
with open(os.path.join(os.path.dirname(appion.__file__),"../test","test_motioncorrection_utils","motioncor2_1.6.4_log.txt"), "r") as f:
    for line in f:
        outbuffer.append(line.rstrip("\n"))
logparser=retrieveLogParser("MotionCor2 version 1.6.4")
logdata=logparser(copy.deepcopy(outbuffer))
logdata["shifts"]=[list(coords) for coords in logdata["shifts"]]
params['test_parseMotionCorLog'].append({
    "outbuffer" : outbuffer,
    "shift_start" : "Frame   x Shift   y Shift",
    "expected" : logdata
})

with open(os.path.join(os.path.dirname(appion.__file__),"../test","./test_motioncorrection.yml"),"w") as f:
    yaml.dump(params, f)