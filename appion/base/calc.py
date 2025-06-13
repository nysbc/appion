from math import degrees

# Currently ctffind4 is the only tool that has an obvious criteria for images that should be reprocessed.
# See: https://github.com/nysbc/appion-slurm/blob/f376758762771073c0450d2bc3badc0fed6f8e66/appion/bin/ctffind4.py#L130
# Rejected images 
def filterImages(all_images, done_images, reprocess_images : set = set(), rejected_images: set = set()):
    return ((all_images - done_images) | reprocess_images) - rejected_images

# 2026/09/10: Honestly not entirely sure how'd I'd go about testing this with real world data;
# no one has used the --tiltangle flag for any of the Appion sessions since 12/2024.  --jsp
# Maybe just chuck it?
def calcSkipTiltAngle(tilt_angle, tilt_angle_type, unit : str = "radians") -> bool:
    if unit == "radians":
        tilt_angle=degrees(tilt_angle)
    if (tilt_angle_type == 'notilt' and abs(tilt_angle) > 3.0 ):
        return True
    elif (tilt_angle_type == 'hightilt' and abs(tilt_angle) < 30.0 ):
        return True
    elif (tilt_angle_type == 'lowtilt' and abs(tilt_angle) >= 30.0 ):
        return True
    ### the reason why -2.0 and 2.0 are used is because the tilt angle is saved as 0 +/- a small amount
    elif (tilt_angle_type == 'minustilt' and tilt_angle > -2.0 ):
        return True
    elif (tilt_angle_type == 'plustilt' and tilt_angle < 2.0 ):
        return True
    return False

def calcSlicedImageSet(images, startimgid, endimgid):
    return set([image for image in images if image > startimgid or image < endimgid])