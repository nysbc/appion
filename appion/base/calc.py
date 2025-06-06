from math import degrees

# Currently ctffind4 is the only tool that has an obvious criteria for images that should be reprocessed.
# See: https://github.com/nysbc/appion-slurm/blob/f376758762771073c0450d2bc3badc0fed6f8e66/appion/bin/ctffind4.py#L130
# Rejected images 
def filterImages(all_images, done_images, reprocess_images : set = set(), rejected_images: set = set()):
    return all_images - done_images + reprocess_images - rejected_images

def getTiltAngleDeg(imgdata):
    from math import degrees
    return degrees(imgdata['scope']['stage position']['a'])

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

#TODO refactor this to return a set?  What are we doing with this?
#=====================
# def skipTestOnImage(self,imgdata):
#     imgname = imgdata['filename']
#     skip = False
#     reason = None
#     # Check if in donedict first. This means rejected images that
#     # was last tested will not be called rejected, but done
#     # This speeds up this function when rerun but means past image
#     # status can not be reverted.
#     try:
#         self.donedict[imgname]
#         return True, 'done'
#     except KeyError:
#         pass
#     if self.reprocessImage(imgdata) is False:
#         self._writeDoneDict(imgname)
#         reason = 'reproc'
#         skip = True

#     if skip is True:
#         return skip, reason
#     else:
#     # image not done or reprocessing allowed

#         if self.params['norejects'] is True and status is False:
#             reason = 'reject'
#             skip = True

#         elif ( self.params['tiltangle'] is not None or self.params['tiltangle'] != 'all' ):
#             tiltangle = apDatabase.getTiltAngleDeg(imgdata)

#             tiltangle = apDatabase.getTiltAngleDeg(imgdata)

#             if skip == True:
#                 reason = 'tilt'

#     return skip, reason