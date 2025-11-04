import numpy
import math
import os
import hashlib
from copy import deepcopy

## Calculations for parameters used in motioncor2 command
# InMrc, InTiff, InEer functions
def calcInputType(fpath):
    if fpath.endswith(".mrc"):
        return "InMrc"
    elif fpath.endswith(".tif") or fpath.endswith(".tiff"):
        return "InTiff"
    elif fpath.endswith(".eer"):
        return "InEer"
    else:
        raise RuntimeError("Unsupported file format for input path: %s." % fpath)

# DefectMap functions   
def calcImageDefectMap(bad_rows : str, bad_cols : str, bad_pixels : str, dx : int, dy : int, frame_flip : int = 0, frame_rotate : int = 0):
    bad_rows = eval(bad_rows) if bad_rows else []
    bad_cols = eval(bad_cols) if bad_cols else []
    bad_pixels = eval(bad_pixels) if bad_pixels else []
    defect_map = numpy.zeros((dy,dx),dtype=numpy.int8)
    defect_map[bad_rows,:] = 1
    defect_map[:,bad_cols] = 1
    for px, py in bad_pixels:
        defect_map[py,px] = 1
    # flip and rotate map_array.  Therefore, do the opposite of
    # frames
    if frame_flip:
        if frame_rotate and frame_rotate == 2:
            # Faster to just flip left-right than up-down flip + rotate
            # flipping the frame left-right
            defect_map = numpy.fliplr(defect_map)
            frame_rotate = 0
            # reset flip
            frame_flip = 0
    if frame_rotate:
        # rotating the frame by %d degrees" % (frame_rotate*90,)
        defect_map = numpy.rot90(defect_map,4-frame_rotate)
    if frame_flip:
        #flipping the frame up-down
        defect_map = numpy.flipud(defect_map)
    return defect_map

# FmIntFile/FmDose functions
def calcFmDose(total_raw_frames: int, exposure_time, frame_time, dose, rendered_frame_size, totaldose, is_eer):
    # This depends on whether or not we're using an EER formatted-input.
    # see https://github.com/nysbc/appion-slurm/blob/f376758762771073c0450d2bc3badc0fed6f8e66/appion/appionlib/apDDFrameAligner.py#L395-L399

    if total_raw_frames is None:
        # older data or k2
        total_raw_frames =  int(exposure_time / frame_time)
    # avoid 0 for dark image scaling and frame list creation
    if total_raw_frames == 0:
        total_raw_frames = 1

    # totaldose is user-specified when the doseweight flag is passed
    # If this flag isn't specified, the database is queried.
    if not totaldose:
        if not dose:
            dose = 0.0
        totaldose = dose / 1e20
    if totaldose > 0:
        raw_dose = totaldose / total_raw_frames
    else:
        raw_dose = 0.03 #make fake dose similar to Falcon4EC 7 e/p/s

    if not is_eer:
        return totaldose/total_raw_frames
    else:
        return raw_dose*rendered_frame_size

def calcTotalRenderedFrames(nraw, size):
    # total_rendered_frames is used when writing out the motioncorr log
    return nraw // size

# PixSize functions

def calcPixelSize(pixelsizedatas, binning, imgdata_timestamp):
    """
    use image data object to get pixel size
    multiplies by binning and also by 1e10 to return image pixel size in angstroms
    Assumes that pixelsizedata is in descending order sorted by timestamp.

    return image pixel size in Angstroms
    """
    i = 0
    pixelsizedata = pixelsizedatas[i]
    oldestpixelsizedata = pixelsizedata
    while pixelsizedata["timestamp"] > imgdata_timestamp and i < len(pixelsizedatas):
        i += 1
        pixelsizedata = pixelsizedatas[i]
        if pixelsizedata["timestamp"] < oldestpixelsizedata["timestamp"]:
            oldestpixelsizedata = pixelsizedata
    if pixelsizedata["timestamp"] > imgdata_timestamp:
        # There is no pixel size calibration data for this image. Use oldest value.
        pixelsizedata = oldestpixelsizedata
    pixelsize = oldestpixelsizedata["pixelsize"] * binning
    return pixelsize*1e10

# Trunc Functions
def filterFrameList(pixelsize : float, total_frames : int, shifts : list, nframe : int = None, startframe : int = None, driftlimit : int = None):
    '''
    Get list of frames
    '''
    framelist=[]
    # frame list according to start frame and number of frames
    if nframe is None:
        if startframe is None:
            framelist = range(total_frames)
        else:
            framelist = range(startframe,total_frames)
    else:
        framelist = range(startframe,startframe+nframe)
    if driftlimit is not None:
        # drift limit considered
        threshold = driftlimit / pixelsize
        stillframes = []
        # pick out passed frames
        for i in range(len(shifts[:-1])):
            # keep the frame if at least one shift around the frame is small enough
            if min(shifts[i],shifts[i+1]) < threshold:
                # index is off by 1 because of the duplication
                stillframes.append(i)
        if stillframes:
            framelist = list(set(framelist).intersection(set(stillframes)))
            framelist.sort()
        #apDisplay.printMsg('Limit frames used to %s' % (framelist,))
    return framelist

def calcKV(high_tension):
    return high_tension/1000.0


def calcTotalFrames(camera_name : str, exposure_time : float, frame_time : float, nframes : int, eer_frames : bool):
    if camera_name in ["GatanK2","GatanK3"]:
        total_frames = max(1,int(exposure_time / frame_time))
    elif 'DE':
        total_frames = nframes
    elif camera_name in ['TIA','Falcon','Falcon3','Falcon4'] or (camera_name == 'Falcon4EC' and eer_frames):
        total_frames = nframes
    else:
        total_frames = nframes
    return total_frames

def calcTrunc(total_frames: int, sumframelist : list,):
    return total_frames - sumframelist[-1] - 1

# RotGain and FlipGain functions
def calcRotFlipGain(frame_rotate : int, frame_flip: int, force_cpu_flat : bool, frame_aligner_flat: bool) -> tuple:
    if not force_cpu_flat and frame_aligner_flat:
        return frame_rotate, frame_flip
    else:
        return 0, 0
    
## Calculations for metadata outputs
def calcFrameStats(pixel_shifts):
    '''
    get alignment frame stats for faster graphing.
    '''
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

def calcFrameShiftFromPositions(positions,running=1):
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

def calcAlignedCamera(dimensions : tuple, square_output : bool, binning : tuple, offset : tuple, stack_binning, trimming_edge, framelist, nframes):
    '''
    DD aligned image will be uploaded into database with the specified binning.
    If self.square_output is True, with a square
    camera dimension at the center and the specificed binning
    '''
    # First element is x, second element is y in tuples.
    if square_output:
        mindim = min(dimensions)
        dimensions = (mindim, mindim)
    unaligned_binning = binning[0]
    aligned_binning = unaligned_binning * stack_binning
    aligned_dimensions = []
    aligned_offset = []
    for axis in [0,1]:
        camerasize = (offset[axis]*2+dimensions[axis])*binning[axis]
        aligned_dimensions.append(dimensions[axis] * binning[axis] / aligned_binning - 2*trimming_edge / aligned_binning)
        aligned_offset.append((camerasize/aligned_binning -dimensions[axis])/2)
    aligned_dimensions = tuple(aligned_dimensions)
    aligned_offset = tuple(aligned_offset)
    # see Issue 12298
    if framelist and framelist != range(nframes):
        use_frames = framelist
    else:
        # assume all frames that are saved are used by not defining the list
        use_frames = None
    return (aligned_binning, aligned_binning), aligned_dimensions, aligned_offset, use_frames

def calcMotionCorrLogPath(framestackpath):
    return os.path.splitext(framestackpath)[0]+"_Log.txt"

def motioncor_merge(kwarg_list, rundir, max_batch_size=10):
    merged_tasks=[]
    serial_inputs={}
    merged_kwargs={}
    flags=['EerSampling', 'Patch', 'Iter', 'Tol','Bft','FtBin','Throw','Group',
            'FmRef', 'Gpu', 'Gain', 'Dark', 'DefectMap', 'FmDose', 'FmIntFile', 'PixSize',
            'kV', 'Trunc', 'RotGain', 'FlipGain','InMrc', 'InTiff', 'InEer']
    for kwargs in kwarg_list:
        flags_cat=""
        for flag in flags:
            if flag in kwargs.keys():
                flags_cat+=str(kwargs[flag])
        flag_hash = hashlib.md5(flags_cat)
        if flag_hash not in serial_inputs.keys():
            serial_inputs[flag_hash]=[]
        for input_flag in ['InMrc', 'InTiff', 'InEer']:
            if input_flag in kwargs.keys():
                serial_inputs[flag_hash].append(kwargs[input_flag])
        if flag_hash not in merged_kwargs.keys():
            tmp_kwargs={}
            for flag in flags:
                if flag in kwargs.keys():
                    tmp_kwargs[flag]=kwargs[flag]
            merged_kwargs[flag_hash]=tmp_kwargs
    for s_input_k in serial_inputs.keys():
        if s_input_k not in merged_kwargs.keys():
            raise RuntimeError("Merging error: serial_inputs and merged_kwargs don't have matching keys.")
        if len(serial_inputs[s_input_k]) > max_batch_size:
            partitions=round(len(serial_inputs[s_input_k])/max_batch_size)
            for p in range(partitions):
                part_name="%s-%d" % (s_input_k, p)
                part_dir=os.path.join(rundir,"merged_inputs", part_name)
                if not os.path.exists(part_dir):
                    os.makedirs(part_dir)
                for _ in range(max_batch_size):
                    if serial_inputs[s_input_k]:
                        s_input=serial_inputs[s_input_k].pop()
                    else:
                        break
                    os.symlink(s_input, os.path.join(part_dir, os.path.basename(s_input)))
                tmp_kwargs=deepcopy(merged_kwargs[s_input_k])
                tmp_kwargs['Serial']=1
                for input_flag in ['InMrc', 'InTiff', 'InEer']:
                    if input_flag in tmp_kwargs:
                        tmp_kwargs[input_flag]=part_dir
                merged_tasks.append(tmp_kwargs)
        else:      
            s_input_dir=os.path.join(rundir,"merged_inputs", s_input_k)
            if not os.path.exists(s_input_dir):
                os.makedirs(s_input_dir)
            for _ in range(max_batch_size):
                if serial_inputs[s_input_k]:
                    s_input=serial_inputs[s_input_k].pop()
                else:
                    break
                os.symlink(s_input, os.path.join(s_input_dir, os.path.basename(s_input)))
            tmp_kwargs=deepcopy(merged_kwargs[s_input_k])
            tmp_kwargs['Serial']=1
            for input_flag in ['InMrc', 'InTiff', 'InEer']:
                if input_flag in tmp_kwargs:
                    tmp_kwargs[input_flag]=s_input_dir
            merged_tasks.append(tmp_kwargs)
    return merged_tasks