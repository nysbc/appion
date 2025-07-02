import parametrize_from_file

import appion
import os
import numpy
from appion.motioncorrection.calc.internal import calcInputType, calcImageDefectMap, calcFmDose, calcTotalRenderedFrames, calcKV, calcTotalFrames, calcTrunc, calcPixelSize, filterFrameList, calcRotFlipGain, calcAlignedCamera, calcMotionCorrLogPath

@parametrize_from_file
def test_calcInputType(fpath, expected):
    assert calcInputType(fpath) == expected

@parametrize_from_file
def test_calcImageDefectMap(dm):
    dm=os.path.join(os.path.dirname(appion.__file__),"../test",dm)
    dm_npz=numpy.load(dm)
    defect_map_args=[str(element) for element in dm_npz["defect_map_args"]]
    defect_map_args[3]=int(defect_map_args[3])
    defect_map_args[4]=int(defect_map_args[4])
    defect_map_args=tuple(defect_map_args)
    defect_map=dm_npz["defect_map"]
    calculated_defect_map=calcImageDefectMap(*defect_map_args)
    assert list(defect_map.flatten()) == list(calculated_defect_map.flatten())

@parametrize_from_file
def test_calcFmDose(total_raw_frames, exposure_time, frame_time, dose, rendered_frame_size, totaldose, is_eer, expected):
    assert "%.3f" % calcFmDose(total_raw_frames, exposure_time, frame_time, dose, rendered_frame_size, totaldose, is_eer) == expected

@parametrize_from_file
def test_calcTotalRenderedFrames(total_raw_frames, rendered_frame_size, expected ):
    assert calcTotalRenderedFrames(total_raw_frames, rendered_frame_size) == expected

@parametrize_from_file
def test_calcPixelSize(pixelsizedatas, binning, imgdata_timestamp, expected):
    assert "%.2f" % calcPixelSize(pixelsizedatas, binning, imgdata_timestamp) == "%.2f" % expected

@parametrize_from_file
def test_filterFrameList(pixsize, nframes, shifts, expected):
    assert list(filterFrameList(pixsize, nframes, shifts)) == expected

@parametrize_from_file
def test_calcKV(high_tension, expected):
    assert calcKV(high_tension) == expected

@parametrize_from_file
def test_calcTotalFrames(camera_name, exposure_time, frame_time, nframes, eer_frames, expected):
    assert calcTotalFrames(camera_name, exposure_time, frame_time, nframes, eer_frames) == expected

@parametrize_from_file
def test_calcTrunc(total_frames, sumframelist, expected):
    assert "%.2f" % calcTrunc(total_frames, sumframelist) == expected

@parametrize_from_file
def test_calcRotFlipGain(frame_rotate, frame_flip, force_cpu_flat, frame_aligner_flat, expected_RotGain, expected_FlipGain):
    RotGain, FlipGain = calcRotFlipGain(frame_rotate, frame_flip, force_cpu_flat, frame_aligner_flat) 
    assert RotGain == expected_RotGain
    assert FlipGain == expected_FlipGain

def test_calcFrameStats():
    pass

def test_calcFrameShiftFromPositions():
    pass

@parametrize_from_file
def test_calcAlignedCamera(subd_dimension_x, subd_dimension_y, square_output, subd_binning_x, subd_binning_y,
                           subd_offset_x, subd_offset_y, binning, trimming_edge, framelist, nframes,
                           expected_aligned_binning_x, expected_aligned_binning_y,
                           expected_aligned_dimensions_x, expected_aligned_dimensions_y,
                           expected_aligned_offset_x, expected_aligned_offset_y,
                           expected_use_frames):
    aligned_binning, aligned_dimensions, aligned_offset, use_frames = calcAlignedCamera((subd_dimension_x, subd_dimension_y), 
                                                                                        square_output, 
                                                                                        (subd_binning_x, subd_binning_y), 
                                                                                        (subd_offset_x, subd_offset_y), 
                                                                                        binning, 
                                                                                        trimming_edge, 
                                                                                        framelist, 
                                                                                        nframes)
    assert aligned_binning[0] == expected_aligned_binning_x
    assert aligned_binning[1] == expected_aligned_binning_y
    assert aligned_dimensions[0] == expected_aligned_dimensions_x
    assert aligned_dimensions[1] == expected_aligned_dimensions_y
    assert aligned_offset[0] == expected_aligned_offset_x
    assert aligned_offset[1] == expected_aligned_offset_y
    assert use_frames == expected_use_frames

@parametrize_from_file
def test_calcMotionCorrLogPath(framestackpath, expected):
    assert calcMotionCorrLogPath(framestackpath) == expected

