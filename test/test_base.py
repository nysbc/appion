import parametrize_from_file
from appion.base.calc import filterImages, calcSkipTiltAngle, calcSlicedImageSet

@parametrize_from_file
def test_filterImages(all_images, done_images, reprocess_images, rejected_images, expected):
    calculated=filterImages(set(all_images), set(done_images), set(reprocess_images), set(rejected_images))
    assert type(calculated) == set
    assert list(calculated) == expected

@parametrize_from_file
def test_calcSkipTiltAngle(tilt_angle, tilt_angle_type, unit, expected):
    try:
        calculated=calcSkipTiltAngle(tilt_angle, tilt_angle_type, unit)
        assert calculated == expected
    except RuntimeError:
        if unit not in ["degrees", "radians"]:
            assert True
    

@parametrize_from_file
def test_calcSlicedImageSet(images, startimgid, endimgid, expected):
    calculated=calcSlicedImageSet(set(images), startimgid, endimgid)
    assert type(calculated) == set
    assert list(calculated) == expected