# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

import os
import numpy
import mrcfile
from sinedon.models.appion import ApDDAlignImagePairData
from sinedon.models.appion import ApDDFrameTrajectoryData
from sinedon.models.appion import ApDDAlignStatsData
from sinedon.models.leginon import AcquisitionImageData, PresetData
from sinedon.models.leginon import ObjIceThicknessData
from sinedon.models.leginon import ZeroLossIceThicknessData
from sinedon.models.appion import ApDDStackParamsData
from sinedon.models.appion import ApDDStackRunData
from sinedon.models.appion import ApPathData
from sinedon.models.leginon import CameraEMData
from .calc.internal import calcAlignedCamera, calcFrameShiftFromPositions, calcFrameStats, calcTotalRenderedFrames

def constructAlignedImage(image_id, preset_id, camera_id, mrc_image, filename):
    imgdata = AcquisitionImageData.objects.get(def_id=image_id)
    if imgdata:
        # https://docs.djangoproject.com/en/5.2/topics/db/queries/#copying-model-instances
        imgdata.pk = None
        imgdata._state.adding = True
        imgdata.ref_presetdata_preset=PresetData.objects.get(def_id=preset_id)
        imgdata.ref_cameraemdata_camera=CameraEMData.objects.get(def_id=camera_id)
        imgdata.mrc_image=mrc_image
        imgdata.filename=filename
        try:
            orig_imgdata = AcquisitionImageData.objects.get(ref_presetdata_preset=imgdata.ref_presetdata_preset,
                                                                       ref_cameraemdata_camera=imgdata.ref_cameraemdata_camera,
                                                                       mrc_image=imgdata.mrc_image,
                                                                       filename=imgdata.filename)
            return orig_imgdata.def_id
        except AcquisitionImageData.DoesNotExist:
            imgdata.save()
            return imgdata.def_id
    return None

# trimming_edge is the same value as kwargs["Trim"]
# binning is cli_args.bin
# framelist is output of filterFrameList
# nframes is output of calcTotalFrames
def constructAlignedCamera(camera_id, square_output, binning : int = 1, trimming_edge : int = 0, framelist : list = [], nframes : int = 0):
    camdata = CameraEMData.objects.get(def_id=camera_id)
    if camdata:
        # https://docs.djangoproject.com/en/5.2/topics/db/queries/#copying-model-instances
        camdata.pk = None
        camdata._state.adding = True
        aligned_binning, aligned_dimensions, aligned_offset, use_frames = calcAlignedCamera((camdata.subd_dimension_x, camdata.subd_dimension_y), 
                                                                                            square_output, 
                                                                                            (camdata.subd_binning_x, camdata.subd_binning_y), 
                                                                                            (camdata.subd_offset_x, camdata.subd_offset_y), 
                                                                                            binning, 
                                                                                            trimming_edge, 
                                                                                            framelist, 
                                                                                            nframes)
        camdata.subd_dimension_x=aligned_dimensions[0]
        camdata.subd_dimension_y=aligned_dimensions[1]
        camdata.subd_binning_x=aligned_binning[0]
        camdata.subd_binning_y=aligned_binning[1]
        camdata.subd_offset_x=aligned_offset[0]
        camdata.subd_offset_y=aligned_offset[1]
        if use_frames:
            camdata.seq_use_frames=str(use_frames)
        else:
            camdata.seq_use_frames=None
        camdata.align_frames=True
        try:
            orig_camdata = CameraEMData.objects.get(subd_dimension_x=camdata.subd_binning_x,
                                                    subd_dimension_y=camdata.subd_binning_y,
                                                    subd_binning_x=camdata.subd_binning_y,
                                                    subd_binning_y=camdata.subd_binning_y,
                                                    subd_offset_x=camdata.subd_offset_x,
                                                    subd_offset_y=camdata.subd_offset_y,
                                                    seq_use_frames=camdata.seq_use_frames,
                                                    align_frames=camdata.align_frames)
            return orig_camdata.def_id
        except CameraEMData.DoesNotExist:
            camdata.save()
            return camdata.def_id
    return None

def constructAlignedPresets(preset_id, camera_id, magnification=None, defocus=None, tem=None, session=None, alignlabel='a'):
    try:
        align_presetdata = PresetData.objects.get(def_id=preset_id)
    except PresetData.DoesNotExist:
        align_presetdata = None
    camdata = CameraEMData.objects.get(def_id=camera_id)
    if not align_presetdata:
        align_presetdata=PresetData(name="ma-%s" % alignlabel,
                                    magnification=magnification,
                                    defocus=defocus,
                                    ref_instrumentdata_tem=tem,
                                    ref_instrumentdata_ccdcamera=camdata,
                                    ref_sessiondata_session=session)
    else:
        # https://docs.djangoproject.com/en/5.2/topics/db/queries/#copying-model-instances
        align_presetdata.pk = None
        align_presetdata._state.adding = True
        align_presetdata.name = "%s-%s" % (align_presetdata.name, alignlabel)
    align_presetdata.dimension_x = camdata.subd_dimension_x
    align_presetdata.dimension_y = camdata.subd_dimension_y
    align_presetdata.binning_x = camdata.subd_binning_x
    align_presetdata.binning_y = camdata.subd_binning_y
    align_presetdata.offset_x = camdata.subd_offset_x
    align_presetdata.offset_y = camdata.subd_offset_y
    align_presetdata.exposure_time = camdata.exposure_time
    try:
        fields={}
        for field in align_presetdata._meta.get_fields():
            fields[field.name]=getattr(align_presetdata, field.name)
        orig_align_presetdata = PresetData.objects.get(**fields)
        return orig_align_presetdata.def_id
    except PresetData.DoesNotExist:
        align_presetdata.save()
        return align_presetdata.def_id

def calcVersionedFilename(basepath, filename):
    '''
    Make a unique image filename in the same session
    '''
    imgpath=os.path.join(basepath, filename)
    img_version=0
    while os.path.isfile(imgpath):
        img_version+=1
        imglist=os.path.splitext(imgpath)
        imgpath="%s_v%02d%s" % (imglist[0], img_version, imglist[1])
    return os.path.basename(imgpath)

# Filename should be output of makeUniqueImageFilename(?)
def constructAlignedImageData(imageid, presetid, cameraid, aligned_filename):
    '''
    Prepare ImageData to be uploaded after alignment
    '''
    # make new imagedata with the align_preset amd aligned CameraEMData
    imgdata=AcquisitionImageData.objects.get(def_id=imageid)
    if imgdata:
        # https://docs.djangoproject.com/en/5.2/topics/db/queries/#copying-model-instances
        imgdata.pk = None
        imgdata._state.adding = True
        imgdata.ref_presetdata_preset=PresetData.objects.get(def_id=presetid)
        imgdata.ref_cameraemdata_camera=CameraEMData.objects.get(def_id=cameraid)
        imgdata.mrc_image = aligned_filename
        imgdata.filename = os.path.splitext(aligned_filename)[0]
        try:
            orig_imgdata=AcquisitionImageData.objects.get(ref_presetdata_preset=imgdata.ref_presetdata_preset,
                                                          ref_cameraemdata_camera=imgdata.ref_cameraemdata_camera,
                                                          mrc_image=imgdata.mrc_image,
                                                          filename=imgdata.filename)
            return orig_imgdata.def_id
        except AcquisitionImageData.DoesNotExist:
            imgdata.save()
            return imgdata.def_id
    return None

# ApDDAlignImagePairData
# We can only really add insert ref IDs here b/c the raw and aligned images are in a different database from the Appion results.
# If it weren't for this, we'd probably pass objects directly.
def uploadAlignedImage(raw_image_def_id, aligned_image_def_id, rundata_def_id, shifts, pixsize, doseweighted=False, trajdata_def_id=None):
    saveImagePairData(raw_image_def_id, aligned_image_def_id, rundata_def_id)
    aligned_image=AcquisitionImageData.objects.get(def_id=aligned_image_def_id)
    nframes=aligned_image.ref_cameraemdata_camera.nframes
    if not doseweighted:
        max_drifts, median = uploadAlignStats(shifts, nframes)
        saveAlignStats(aligned_image_def_id, rundata_def_id, max_drifts, median, pixsize, trajdata_def_id)
    copyALSThicknessParams(raw_image_def_id,aligned_image_def_id)
    copyZLPThicknessParams(raw_image_def_id,aligned_image_def_id)

def saveImagePairData(raw_image_def_id, aligned_image_def_id, rundata_def_id):
    pairdata = ApDDAlignImagePairData(ref_acquisitionimagedata_source=raw_image_def_id,
                                    ref_acquisitionimagedata_result=aligned_image_def_id,
                                    ref_apddstackrundata_ddstackrun=rundata_def_id)
    try:
        orig_pairdata = ApDDAlignImagePairData.objects.get(ref_acquisitionimagedata_source=raw_image_def_id,
                                                           ref_acquisitionimagedata_result=aligned_image_def_id,
                                                           ref_apddstackrundata_ddstackrun=rundata_def_id)
        return orig_pairdata.def_id
    except ApDDAlignImagePairData.DoesNotExist:
        pairdata.save()
        return pairdata.def_id
			
def copyALSThicknessParams(unaligned,aligned):
# transfers aperture limited scattering measurements and parameters from the unaligned image to the aligned image
# should it be here or in a different place???
    unaligned_image = AcquisitionImageData.objects.get(def_id=unaligned)
    obthdata = ObjIceThicknessData.objects.filter(ref_acquisitionimagedata_image=unaligned_image)
    aligned_image = AcquisitionImageData.objects.get(def_id=aligned)
    if obthdata:
        obthdata = obthdata[len(obthdata) - 1]
        newobjth = ObjIceThicknessData(vacuum_intensity = obthdata.vacuum_intensity,
                                       mfp = obthdata.mfp,
                                       intensity = obthdata.intensity,
                                       thickness = obthdata.thickness,
                                       ref_acquisitionimagedata_image = aligned_image)
        try:
            orig_newobjth = ObjIceThicknessData.objects.get(vacuum_intensity = obthdata.vacuum_intensity,
                                                            mfp = obthdata.mfp,
                                                            intensity = obthdata.intensity,
                                                            thickness = obthdata.thickness,
                                                            ref_acquisitionimagedata_image = aligned_image)
            return orig_newobjth.def_id
        except ObjIceThicknessData.DoesNotExist:
            newobjth.save()
            return newobjth.def_id
    return None
		

def copyZLPThicknessParams(unaligned,aligned):
    # transfers zero loss peak measurements and parameters from the unaligned image to the aligned image
    # should it be here or in a different place???
    unaligned_image = AcquisitionImageData.objects.get(def_id=unaligned)
    zlpthdata = ZeroLossIceThicknessData.objects.filter(ref_acquisitionimagedata_image=unaligned_image)
    aligned_image = AcquisitionImageData.objects.get(def_id=aligned)
    if zlpthdata:
        zlpthdata = zlpthdata[len(zlpthdata) - 1]
        newzlossth = ZeroLossIceThicknessData(no_slit_mean = zlpthdata.no_slit_mean,
											  no_slit_sd = zlpthdata.no_slit_sd,
											  slit_mean = zlpthdata.slit_mean,
											  slit_sd = zlpthdata.slit_sd,
											  thickness = zlpthdata.thickness,
											  ref_acquisitionimagedata_image = aligned_image
        )
        try:
            orig_newzlossth = ZeroLossIceThicknessData.objects.get(no_slit_mean = zlpthdata.no_slit_mean,
                                                       no_slit_sd = zlpthdata.no_slit_sd,
                                                       slit_mean = zlpthdata.slit_mean,
                                                       slit_sd = zlpthdata.slit_sd,
                                                       thickness = zlpthdata.thickness,
                                                       ref_acquisitionimagedata_image = aligned_image)
            return orig_newzlossth.def_id
        except ZeroLossIceThicknessData.DoesNotExist:
            newzlossth.save()
            return newzlossth.def_id
    return None

def uploadAlignStats(shifts, nframes):
    pixel_shifts = calcFrameShiftFromPositions(shifts, nframes - len(shifts)+1)
    max_drifts, median = calcFrameStats(pixel_shifts)
    return max_drifts, median

# ApDDAlignStatsData
# Pass in shifts from dict returned by parseLog
# Run saveFrameTrajectory beforehand to get trajdata_def_id.
def saveAlignStats(aligned_image_def_id, rundata_def_id, max_drifts, median, pixsize, trajdata_def_id=None):
    # Issue #6155 need new query to get timestamp
	# JP: Where does a timestamp come into play?
    #aligned_imgdata = AcquisitionImageData.objects.get(def_id=aligned_image_def_id)
    drifts={}
    for i, drift_tuple in enumerate(max_drifts):
        key = 'top_shift%d' % (i+1,)
        drifts[key+'_index'] = drift_tuple[1]
        drifts[key+'_value'] = drift_tuple[0]
    aligned_image = AcquisitionImageData.objects.get(def_id=aligned_image_def_id)
    rundata = ApDDStackRunData.objects.get(def_id=rundata_def_id)
    if trajdata_def_id:
        trajdata = ApDDFrameTrajectoryData.objects.get(def_id=trajdata_def_id)
        alignstatsdata = ApDDAlignStatsData(ref_acquisitionimagedata_image=aligned_image, 
                                            apix=pixsize,
                                            ref_apddstackrundata_ddstackrun=rundata,
                                            median_shift_value=median,
                                            ref_apddframetrajectorydata_trajectory=trajdata,
                                            **drifts)
    else:
        alignstatsdata = ApDDAlignStatsData(ref_acquisitionimagedata_image=aligned_image, 
                                            apix=pixsize,
                                            ref_apddstackrundata_ddstackrun=rundata,
                                            median_shift_value=median,
                                            **drifts)
    try:
        if trajdata_def_id:
            #trajdata = ApDDFrameTrajectoryData.objects.get(def_id=trajdata_def_id)
            orig_alignstatsdata = ApDDAlignStatsData.objects.get(ref_acquisitionimagedata_image=aligned_image, 
                                                apix=pixsize,
                                                ref_apddstackrundata_ddstackrun=rundata,
                                                median_shift_value=median,
                                                ref_apddframetrajectorydata_trajectory=trajdata,
                                                **drifts)
        else:
            orig_alignstatsdata = ApDDAlignStatsData.objects.get(ref_acquisitionimagedata_image=aligned_image, 
                                                apix=pixsize,
                                                ref_apddstackrundata_ddstackrun=rundata,
                                                median_shift_value=median,
                                                **drifts)
        return orig_alignstatsdata.def_id
    except ApDDAlignStatsData.DoesNotExist:
        alignstatsdata.save()
        return alignstatsdata.def_id
	
# ApDDFrameTrajectoryData

# Default args used by motioncor2 for limit, reference_index, particle.
# Separate pure calculations from storage functionality?
def saveFrameTrajectory(image_def_id, rundata_def_id, shifts, limit=20, reference_index=None, particle=None):
    '''
    Save appiondata ApDDFrameTrajectoryData
    '''
    xy={}
    xy['x']=[shift[0] for shift in shifts]
    xy['y']=[shift[1] for shift in shifts]
    n_positions = len(xy['x'])
    limit = min([n_positions,limit])
    if limit < 2:
        raise ValueError('Not enough frames to save trajectory')
    if reference_index == None:
        reference_index = n_positions // 2
    trajdata = ApDDFrameTrajectoryData(ref_acquisitionimagedata_image=image_def_id,
									ref_apstackparticledata_particle=particle,
									ref_apddstackrundata_ddstackrun=rundata_def_id,
                                    seq_pos_x=str(list(xy['x'][:limit])), #position relative to reference
                                    seq_pos_y=str(list(xy['y'][:limit])), #position relative to reference
                                    last_x=xy['x'][-1],
                                    last_y=xy['y'][-1],
                                    number_of_positions= n_positions,
                                    reference_index= reference_index)
    try:
        orig_trajdata = ApDDFrameTrajectoryData.objects.get(ref_acquisitionimagedata_image=trajdata.ref_acquisitionimagedata_image,
                                        ref_apstackparticledata_particle=trajdata.ref_apstackparticledata_particle,
                                        ref_apddstackrundata_ddstackrun=trajdata.ref_apddstackrundata_ddstackrun,
                                        seq_pos_x=trajdata.seq_pos_x,
                                        seq_pos_y=trajdata.seq_pos_y,
                                        last_x=trajdata.last_x,
                                        last_y=trajdata.last_y,
                                        number_of_positions=trajdata.number_of_positions,
                                        reference_index=trajdata.reference_index)
        return orig_trajdata.def_id
    except ApDDFrameTrajectoryData.DoesNotExist:
        trajdata.save()
        return trajdata.def_id

#ApDDStackParamsData
def saveDDStackParamsData(preset, align, binning, ref_apddstackrundata_unaligned_ddstackrun, method, ref_apstackdata_stack=None, ref_apdealignerparamsdata_de_aligner=None):
    ddstackparamsdata = ApDDStackParamsData.objects.filter(preset=preset, align=align, binning=binning, 
                                                           ref_apddstackrundata_unaligned_ddstackrun=ref_apddstackrundata_unaligned_ddstackrun, 
                                                           ref_apstackdata_stack=ref_apstackdata_stack,
                                                           method=method,
                                                           ref_apdealignerparamsdata_de_aligner=ref_apdealignerparamsdata_de_aligner)
    if not ddstackparamsdata:
        ddstackparamsdata = ApDDStackParamsData(preset=preset, align=align, binning=binning, 
                                                ref_apddstackrundata_unaligned_ddstackrun=ref_apddstackrundata_unaligned_ddstackrun, 
                                                ref_apstackdata_stack=ref_apstackdata_stack,
                                                method=method,
                                                ref_apdealignerparamsdata_de_aligner=ref_apdealignerparamsdata_de_aligner)
        ddstackparamsdata.save()
    else:
        ddstackparamsdata=ddstackparamsdata[len(ddstackparamsdata)-1]
    return ddstackparamsdata.def_id
			
# ApDDStackRunData
def saveDDStackRunData(preset, align, binning, runname, rundir, ref_sessiondata_session, stack=None):
    # We don't use ApStackData so that stack is always set to None.
    params = ApDDStackParamsData.objects.filter(preset=preset,align=align,binning=binning,ref_apstackdata_stack=stack)
    params = params[len(params) - 1]
    path = ApPathData.objects.filter(path=os.path.abspath(rundir))
    path = path[len(path) - 1]
    results = ApDDStackRunData.objects.filter(runname=runname,ref_apddstackparamsdata_params=params.def_id,ref_sessiondata_session=ref_sessiondata_session,ref_appathdata_path=path.def_id)
    if not results:
        ddstackrundata = ApDDStackRunData(runname=runname,ref_apddstackparamsdata_params=params.def_id,ref_sessiondata_session=ref_sessiondata_session,ref_appathdata_path=path.def_id)
        ddstackrundata.save()
    else:
        ddstackrundata=ddstackrundata[0]
    return ddstackrundata.def_id


def saveMotionCorrLog(logData: dict, outputLogPath: str, throw: int, totalRenderedFrames: int, binning: float = 1.0) -> None:
    ''' 
    Takes the output log from motioncor2/motioncor3 and converts it to a motioncorr-formatted log.
    This is necessary because the myamiweb web UI reads motioncorr logs directly / doesn't query the database for information about shifts.
    See here: https://github.com/leginon-org/leginon/blob/34bf9ab9a7a7ec8ae2d9a6ab818a4538cb925787/myamiweb/processing/inc/particledata.inc#L2505-L2533
    '''
    # Convert to the convention used in motioncorr
    # so that shift is in pixels of the aligned image.
    adjusted_shifts = []
    midval = int(len(logData["shifts"])/2)
    midshx = logData["shifts"][midval][0]
    midshy = logData["shifts"][midval][1]
    for shift in logData["shifts"]:
        shxa = -(shift[0] - midshx) / binning
        shya = -(shift[1] - midshy) / binning
        adjusted_shifts.append((shxa, shya))

    # Formats the shifts in motioncorr format.
    with open(outputLogPath,"w") as f:
        f.write("Sum Frame #%.3d - #%.3d (Reference Frame #%.3d):\n" % (0, totalRenderedFrames, totalRenderedFrames/2))
        # Eer nframe is not predictable.
        for idx, adjusted_shift in enumerate(adjusted_shifts):
            f.write("......Add Frame #%.3d with xy shift: %.5f %.5f\n" % (idx+throw, adjusted_shift[0], adjusted_shift[1]))

# Dark functions

def saveDark(dark_output_path : str, camera_name : str, eer_frames : bool, dark_input_path : str = "", nframes : int = 1):
    if not dark_input_path:
        # Why is this switch statement necessary?  Why not save default dimensions into the database instead of
        # hardcoding them in here?  (Original Appion has these hardcoded as part of object initialization.)
        if camera_name == "GatanK2":
            dimensions = (3710,3838)
        elif camera_name == 'GatanK3':
            dimensions = (8184,11520)
        elif camera_name == 'DE':
            dimensions = (4096,3072)
        elif camera_name in ['TIA','Falcon','Falcon3','Falcon4'] or (camera_name == 'Falcon4EC' and eer_frames):
            dimensions = (4096,4096)
        else:
            dimensions = (0,0)
        unscaled_darkarray =  numpy.zeros((dimensions[1],dimensions[0]), dtype=numpy.float32)
    else:
        unscaled_darkarray = mrcfile.read(dark_input_path) / nframes
    mrcfile.write(dark_output_path, unscaled_darkarray, overwrite=True)

# DefectMap functions
def saveDefectMrc(defect_map_path : str, defect_map : numpy.ndarray) -> None:
    mrcfile.write(defect_map_path, defect_map, overwrite=True)

# FmIntFile/FmDose functions
def saveFmIntFile(fmintpath, nraw, size, raw_dose):
    '''
    calculate and set frame dose and create FmIntFile
    '''
    modulo = nraw % size
    int_div = nraw // size
    lines = []
    total_rendered_frames = calcTotalRenderedFrames(nraw, size)
    if modulo != 0:
        total_rendered_frames += 1
        lines.append('%d\t%d\t%.3f\n' % (modulo, modulo, raw_dose))
    lines.append('%d\t%d\t%.3f\n' % (int_div*size+modulo, size, raw_dose))
    with open(fmintpath,'w') as f:
        f.write(''.join(lines))