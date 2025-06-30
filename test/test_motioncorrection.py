import parametrize_from_file

from appion.motioncorrection.calc.internal import calcInputType, calcFmDose, calcKV, calcPixelSize

@parametrize_from_file
def test_calcInputType(fpath, expected):
    assert calcInputType(fpath) == expected

def test_calcImageDefectMap():
    pass

@parametrize_from_file
def test_calcFmDose(total_raw_frames, exposure_time, frame_time, dose, rendered_frame_size, totaldose, is_eer, expected):
    assert "%.3f" % calcFmDose(total_raw_frames, exposure_time, frame_time, dose, rendered_frame_size, totaldose, is_eer) == expected

def test_calcTotalRenderedFrames():
    pass

@parametrize_from_file
def test_calcPixelSize(pixelsizedatas, binning, imgdata_timestamp, expected):
    assert "%.2f" % calcPixelSize(pixelsizedatas, binning, imgdata_timestamp) == "%.2f" % expected

def test_filterFrameList():
    pass

@parametrize_from_file
def test_calcKV(high_tension, expected):
    assert calcKV(high_tension) == expected

def test_calcTotalFrames():
    pass

def test_calcTrunc():
    pass

def test_calcRotFlipGain():
    pass

def test_calcFrameStats():
    pass

def test_calcFrameShiftFromPositions():
    pass

def test_calcAlignedCamera():
    pass

def test_calcMotionCorrLogPath():
    pass

