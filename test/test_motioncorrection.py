import parametrize_from_file

import appion
import os
import numpy
from appion.motioncorrection.calc.internal import calcInputType, calcImageDefectMap, calcFmDose, calcFrameStats, calcTotalRenderedFrames, calcKV, calcTotalFrames, calcTrunc, calcPixelSize, filterFrameList, calcRotFlipGain, calcFrameShiftFromPositions, calcAlignedCamera, calcMotionCorrLogPath
from appion.motioncorrection.calc.external import constructMotionCorCmd
from appion.motioncorrection.cli.constructors import constructMotionCorKwargs
from appion.motioncorrection.retrieve.logs import parseMotionCorLog

"""
This file contains tests for the motioncor2 related functionality of Appion.
It compares the outputs of pure functions against their expected values.
These expected values are derived from observed outputs of a series of classic Appion
runs that took place in Feb/March 2025.

The defect maps and the expected flags/kwargs for motioncor2 commands are included
and live in separate files (test_motioncorrection.yml and test_motioncorrection_defect_map_*.npz) 
that are loaded via parametrize_from_file and numpy.load.

A few of the expected outputs are generated by the functions that they are intended to test
because empirical observations were unavailable.  These expected outputs are for the following functions:
calcMotionCorrLogPath, filterFrameList, calcTotalFrames, calcTotalRenderedFrames, calcFrameShiftFromPositions, calcFrameStats, calcAlignedCamera

Expected outputs for these functions were generated using version 2025.07.03a of SEMC Appion.
These are meant to primarily serve as a way to detect future regressions and may not be faithful 
to the expected results that may have been calculated by classic Appion object methods.
"""

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

@parametrize_from_file
def test_calcFrameStats(pixel_shifts, expected_max_drifts, expected_median):
    max_drifts, median = calcFrameStats(pixel_shifts)
    max_drifts=[list(i) for i in max_drifts]
    assert max_drifts == expected_max_drifts
    assert float(median) == expected_median

@parametrize_from_file
def test_calcFrameShiftFromPositions(shifts, nframes, expected):
    pixel_shifts = calcFrameShiftFromPositions(shifts, nframes)
    assert pixel_shifts == expected

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

@parametrize_from_file
def test_constructMotionCorKwargs(imgmetadata, args, input_path, expected_kwargs):
    kwargs=constructMotionCorKwargs(imgmetadata, args, input_path)
    if "InMrc" in expected_kwargs.keys():
        assert "InMrc" in kwargs.keys()
    elif "InTiff" in expected_kwargs.keys():
        assert "InTiff" in kwargs.keys()
    elif "InEer" in expected_kwargs.keys():
        assert "InEer" in kwargs.keys()
    assert "%.3f" % kwargs["FmDose"] == expected_kwargs["FmDose"]
    if 'FmIntFile' in expected_kwargs.keys() and 'FmIntFile' in kwargs.keys():
        assert kwargs['FmIntFile'] == expected_kwargs['FmIntFile']
    elif 'FmIntFile' in expected_kwargs.keys() or 'FmIntFile' in kwargs.keys():
        assert False
    assert "%d" % kwargs["kV"] == expected_kwargs["kV"]
    assert "%d" % kwargs["RotGain"] == expected_kwargs["RotGain"]
    assert "%d" % kwargs["FlipGain"] == expected_kwargs["FlipGain"]
    assert "%.3f" % kwargs["PixSize"] == expected_kwargs["PixSize"]
    if "Trunc" in kwargs.keys():
        assert "%.3f" % kwargs["Trunc"] == expected_kwargs["Trunc"]
    if 'EerSampling' in expected_kwargs.keys() and 'EerSampling' in kwargs.keys():
        assert kwargs['EerSampling'] == expected_kwargs['EerSampling']
    elif 'EerSampling' in expected_kwargs.keys() or 'EerSampling' in kwargs.keys():
        assert False
    if 'Patch' in expected_kwargs.keys() and 'Patch' in kwargs.keys():
        assert kwargs['Patch'] == expected_kwargs['Patch']
    elif 'Patch' in expected_kwargs.keys() or 'Patch' in kwargs.keys():
        assert False
    if 'Iter' in expected_kwargs.keys() and 'Iter' in kwargs.keys():
        assert kwargs['Iter'] == expected_kwargs['Iter']
    elif 'Iter' in expected_kwargs.keys() or 'Iter' in kwargs.keys():
        assert False
    if 'Tol' in expected_kwargs.keys() and 'Tol' in kwargs.keys():
       assert kwargs['Tol'] == float(expected_kwargs['Tol'])
    elif 'Tol' in expected_kwargs.keys() or 'Tol' in kwargs.keys():
        if not 'Tol' in expected_kwargs.keys():
            raise AssertionError("%s not in expected_kwargs but present in kwargs." % "Tol")
        elif not 'Tol' in kwargs.keys():
            raise AssertionError("%s not in kwargs but present in expected_kwargs." % "Tol")
    if 'Bft' in expected_kwargs.keys() and 'Bft' in kwargs.keys():
        assert kwargs['Bft'] == expected_kwargs['Bft']
    elif 'Bft' in expected_kwargs.keys() or 'Bft' in kwargs.keys():
        assert False
    if 'FtBin' in expected_kwargs.keys() and 'FtBin' in kwargs.keys():
        assert kwargs['FtBin'] == float(expected_kwargs['FtBin'])
    elif 'FtBin' in expected_kwargs.keys() or 'FtBin' in kwargs.keys():
        if not 'FtBin' in expected_kwargs.keys():
            raise AssertionError("%s not in expected_kwargs but present in kwargs." % "FtBin")
        elif not 'FtBin' in kwargs.keys():
            raise AssertionError("%s not in kwargs but present in expected_kwargs." % "FtBin")
    if 'Throw' in expected_kwargs.keys() and 'Throw' in kwargs.keys():
        assert kwargs['Throw'] == expected_kwargs['Throw']
    elif 'Throw' in expected_kwargs.keys() or 'Throw' in kwargs.keys():
        assert False
    if 'Group' in expected_kwargs.keys() and 'Group' in kwargs.keys():
        assert kwargs['Group'] == expected_kwargs['Group']
    elif 'Group' in expected_kwargs.keys() or 'Group' in kwargs.keys():
        assert False
    if 'FmRef' in expected_kwargs.keys() and 'FmRef' in kwargs.keys():
       assert kwargs['FmRef'] == expected_kwargs['FmRef']
    elif 'FmRef' in expected_kwargs.keys() or 'FmRef' in kwargs.keys():
        if not 'FmRef' in expected_kwargs.keys():
            raise AssertionError("%s not in expected_kwargs but present in kwargs." % "FmRef")
        elif not 'FmRef' in kwargs.keys():
            raise AssertionError("%s not in kwargs but present in expected_kwargs." % "FmRef")
    if 'Gpu' in expected_kwargs.keys() and 'Gpu' in kwargs.keys():
        assert kwargs['Gpu'] == expected_kwargs['Gpu']
    elif 'Gpu' in expected_kwargs.keys() or 'Gpu' in kwargs.keys():
        assert False
        
@parametrize_from_file
def test_constructMotionCorCmd(kwargs, executable, expected):
    calculated=constructMotionCorCmd(executable, kwargs)
    # Ensure that the command is correct.
    assert calculated.pop(0) == expected.pop(0)
    # Flag ordering is non-deterministic so we sort here.
    # TODO Group flags and arguments together when sorting.
    assert sorted(calculated) == sorted(expected)

@parametrize_from_file
def test_parseMotionCorLog(outbuffer, shift_start, expected):
    calculated=parseMotionCorLog(outbuffer, shift_start)
    calculated["shifts"]=[list(coords) for coords in calculated["shifts"]]
    assert calculated["shifts"] == expected["shifts"]