import os
import numpy
import math
from sinedon.models.appion import ApDDAlignImagePairData
from sinedon.models.appion import ApDDFrameTrajectoryData
from sinedon.models.appion import ApDDAlignStatsData
from sinedon.models.leginon import AcquisitionImageData
from sinedon.models.leginon import ObjIceThicknessData
from sinedon.models.leginon import ZeroLossIceThicknessData
from sinedon.models.appion import ApDDStackParamsData
from sinedon.models.appion import ApPathData
from sinedon.models.appion import ApDDStackRunData
from sinedon.models.appion import ApStackData
from django.conf import settings

# ApDDAlignImagePairData
# We can only really add insert ref IDs here b/c the raw and aligned images are in a different database from the Appion results.
# If it weren't for this, we'd probably pass objects directly.
def uploadAlignedImage(raw_image_def_id, aligned_image_def_id, rundata_def_id, logData, kwargs):
    commitImagePairData(raw_image_def_id, aligned_image_def_id, rundata_def_id)
    aligned_image=AcquisitionImageData.objects.get(def_id=aligned_image_def_id)
    nframes=aligned_image.ref_cameraemdata_camera.nframes
    commitAlignStats(aligned_image_def_id, rundata_def_id, logData["shifts"], nframes, kwargs["PixSize"])
    transferALSThickness(raw_image_def_id,aligned_image_def_id)
    transferZLPThickness(raw_image_def_id,aligned_image_def_id)

def commitImagePairData(raw_image_def_id, aligned_image_def_id, rundata_def_id):
    pairdata = ApDDAlignImagePairData(ref_acquisitionimagedata_source=raw_image_def_id,
                                    ref_acquisitionimagedata_result=aligned_image_def_id,
                                    ref_apddstackrundata_ddstackrun=rundata_def_id)
    pairdata.save()

# Pass in shifts from dict returned by parseLog
def commitAlignStats(aligned_image_def_id, rundata_def_id, shifts, nframes, pixsize):
    # Issue #6155 need new query to get timestamp
	# JP: Where does a timestamp come into play?
    #aligned_imgdata = AcquisitionImageData.objects.get(def_id=aligned_image_def_id)
    xy={}
    xy['x']=[shift[0] for shift in shifts]
    xy['y']=[shift[1] for shift in shifts]
    trajdata_def_id = saveFrameTrajectory(aligned_image_def_id, rundata_def_id, xy)
    saveAlignStats(aligned_image_def_id, rundata_def_id, shifts, nframes, pixsize, trajdata=trajdata_def_id)
			
def transferALSThickness(unaligned,aligned):
# transfers aperture limited scattering measurements and parameters from the unaligned image to the aligned image
# should it be here or in a different place???
    obthdata = ObjIceThicknessData.objects.get(ref_acquisitionimagedata_image=unaligned)
    if obthdata:
        results = obthdata[0]
        newobjth = ObjIceThicknessData(vacuum_intensity = results.vacuum_intensity,
                                       mfp = results.mfp,
                                       intensity = results.intensity,
                                       thickness = results.thickness,
                                       ref_acquisitionimagedata_image = aligned)
        newobjth.save()
		

def transferZLPThickness(unaligned,aligned):
    # transfers zero loss peak measurements and parameters from the unaligned image to the aligned image
    # should it be here or in a different place???
    zlpthdata = ZeroLossIceThicknessData.objects.get(ref_acquisitionimagedata_image=unaligned)
    if zlpthdata:
        results = zlpthdata[0]
        newzlossth = ZeroLossIceThicknessData(no_slit_mean = results.no_slit_mean,
											  no_slit_sd = results.no_slit_sd,
											  slit_mean = results.slit_mean,
											  slit_sd = results.slit_sd,
											  thickness = results.thickness,
											  ref_acquisitionimagedata_image = aligned
        )
        newzlossth.save()

# ApDDAlignStatsData	
def saveAlignStats(aligned_image_def_id, rundata_def_id, positions, nframes, pixsize, trajdata=None):
    '''
    save appiondata ApDDAlignStatsData
    '''
    max_drifts, median = getFrameStats(positions, nframes)
    drifts={}
    for i, drift_tuple in enumerate(max_drifts):
        key = 'top_shift%d' % (i+1,)
        drifts[key+'_index'] = drift_tuple[1]
        drifts[key+'_value'] = drift_tuple[0]
    alignstatsdata = ApDDAlignStatsData(image=aligned_image_def_id, 
										apix=pixsize,
                                        ddstackrun=rundata_def_id,
                                        median_shift_value=median,
                                        trajectory=trajdata,
                                        **drifts)
    alignstatsdata.save()

def getFrameStats(positions, nframes):
    '''
    get alignment frame stats for faster graphing.
    '''
    pixel_shifts = calculateFrameShiftFromPositions(positions, nframes - len(positions)+1)
    if not pixel_shifts:
        raise ValueError('no pixel shift found for calculating stats')
    if len(pixel_shifts) < 3:
        raise ValueError('Not enough pixel shifts found for stats calculation')
    pixel_shifts_sort = list(pixel_shifts)
    pixel_shifts_sort.sort()
    median = numpy.median(numpy.array(pixel_shifts_sort))
    max1 = pixel_shifts_sort[-1]
    max2 = pixel_shifts_sort[-2]
    max3 = pixel_shifts_sort[-3]
    m1index = pixel_shifts.index(max1)
    m2index = pixel_shifts.index(max2)
    m3index = pixel_shifts.index(max3)
    return [(max1,m1index),(max2,m2index),(max3,m3index)], median

def calculateFrameShiftFromPositions(positions,running=1):
	# place holder for running first frame shift duplication
	offset = int((running-1)/2)
	shifts = offset*[None,]
	for p in range(len(positions)-1):
		shift = math.hypot(positions[p][0]-positions[p+1][0],positions[p][1]-positions[p+1][1])
		shifts.append(shift)
	# duplicate first and last shift for the end points if running
	for i in range(offset):
		shifts.append(shifts[-1])
		shifts[i] = shifts[offset]
	return shifts
	
# ApDDFrameTrajectoryData

def saveFrameTrajectory(image_def_id, rundata_def_id, xy, limit=20, reference_index=None, particle=None):
    '''
    Save appiondata ApDDFrameTrajectoryData
    '''
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
                                    seq_pos_x=str(list(xy['y'][:limit])), #position relative to reference
                                    last_x=xy['x'][-1],
                                    last_y=xy['y'][-1],
                                    number_of_positions= n_positions,
                                    reference_index= reference_index)
    trajdata.save()
    return trajdata.def_id

#ApDDStackParamsData
def uploadPathData(preset, align, bin, ref_apddstackrundata_unaligned_ddstackrun, method, ref_apstackdata_stack=None, ref_apdealignerparamsdata_de_aligner=None):
	ddstackparamsdata = ApDDStackParamsData.objects.get(preset=preset, align=align, bin=bin, 
                                 ref_apddstackrundata_unaligned_ddstackrun=ref_apddstackrundata_unaligned_ddstackrun, 
                                         ref_apstackdata_stack=ref_apstackdata_stack,
                                         method=method,
                                         ref_apdealignerparamsdata_de_aligner=ref_apdealignerparamsdata_de_aligner)
	if not ddstackparamsdata:
		ddstackparamsdata = ApDDStackParamsData(preset=preset, align=align, bin=bin, 
									ref_apddstackrundata_unaligned_ddstackrun=ref_apddstackrundata_unaligned_ddstackrun, 
											ref_apstackdata_stack=ref_apstackdata_stack,
											method=method,
											ref_apdealignerparamsdata_de_aligner=ref_apdealignerparamsdata_de_aligner)
		ddstackparamsdata.save()
			
# ApDDStackRunData
def uploadDDStackRunData(preset, align, bin, runname, rundir, ref_sessiondata_session, stackid = None):
      # Maybe remove this since we don't use ApStackData?
		if stackid:
			stackdata = ApStackData.objects.get(stackid=stackid)
			stack = stackdata.def_id
		else:
			stack = None
		params = ApDDStackParamsData.objects.get(preset=preset,align=align,bin=bin,stack=stack)
		path = ApPathData.objects.get(path=os.path.abspath(rundir))
		results = ApDDStackRunData.objects.get(runname=runname,ref_apddstackparamsdata_params=params,ref_sessiondata_session=ref_sessiondata_session,ref_appathdata_path=path)
		if not results:
			ddstackrundata = ApDDStackRunData(runname=runname,ref_apddstackparamsdata_params=params,ref_sessiondata_session=ref_sessiondata_session,ref_appathdata_path=path)
			ddstackrundata.save()

		
# ApPathData
def uploadPathData(path):
	appath = ApPathData.objects.get(path=path)
	if not appath:
		appath = ApPathData(path=path)
		appath.save()