import os
from glob import glob
import appion
import json, yaml
import sinedon.setup
sinedon.setup()
from appion.motioncorrection.retrieve.params import readImageMetadata
from appion.motioncorrection.calc.internal import calcMotionCorrLogPath, filterFrameList, calcTotalFrames, calcTotalRenderedFrames, calcAlignedCamera
from sinedon.models.leginon import CameraEMData

with open(os.path.join(os.getcwd(),"motioncor2_validation.json"), "r") as f:
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
params['test_calcAlignedCamera']=[]
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

params['test_calcImageDefectMap']=[]
for dm in glob(os.path.join(os.path.dirname(appion.__file__),"../test","*.npz")):
    params['test_calcImageDefectMap'].append({"dm":os.path.basename(dm)})

with open("./test_motioncorrection.yml","w") as f:
    yaml.dump(params, f)