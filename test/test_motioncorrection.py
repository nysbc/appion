import parametrize_from_file

from appion.motioncorrection.calc.internal import calcKV, calcPixelSize

def test_calcInputType():
    pass

def test_calcImageDefectMap():
    pass

def test_calcFmDose():
    pass

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

