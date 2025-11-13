import sinedon.base as sb
from .calc import calcSkipTiltAngle, calcSlicedImageSet
from datetime import datetime
import os

# The idea here is to have two sets of image IDs.  One set (queried from the database)
# contains all images for a session (optionally broken down by preset as well).
# The second set (also queried from the database using the run directory)
# contains all of the image IDs for images that have already been processed.
# To determine which images need to be processed, we get the set difference
# between all images and finished images.
def readImageSet(session, preset = None):
    if preset:
        if preset == "manual":
            preset = None
        session = sb.get("SessionData", {"name" : session})
        presets = sb.filter("PresetData", {"name" : preset,"ref_sessiondata_session" : session["def_id"]})
        images = []
        for p in presets:
            q_result = sb.filter("AcquisitionImageData", {"ref_sessiondata_session": session["def_id"], "ref_presetdata_preset" : p["def_id"]})
            images += [image["def_id"] for image in q_result]
        images = set(images)
    else:
        session = sb.get("SessionData", {"name" : session})
        images = sb.filter("AcquisitionImageData", {"ref_sessiondata_session" : session["def_id"]})
        images = set([image["def_id"] for image in images])
    return images

def retrieveRejectedImages(images, sessionname, start : None, stop : None, tilt_angle_type):
    skipped_tilt_angle_images = retrieveSkippedTiltAngleImages(sessionname, tilt_angle_type)
    if start and stop:
        sliced_images = calcSlicedImageSet(images, start, stop)
    else:
        sliced_images = set()
    viewer_rejects = retrieveViewerRejects(sessionname)
    assessment_rejects = retrieveAssessmentRejects()
    return skipped_tilt_angle_images | sliced_images | viewer_rejects | assessment_rejects

def retrieveAssessmentRejects():
    #TODO Might want to limit this to a range of image IDs for the current session only.
    assessment_rejects = sb.filter("ApAssessmentData", {"selectionkeep" : 0})
    if assessment_rejects:
        return set([reject["ref_acquisitionimagedata_image"] for reject in assessment_rejects])
    else:
        return set()

def retrieveViewerRejects(sessionname):
    '''
    Images that are hidden in the viewer or are trash are rejected.
    '''
    session = sb.get("SessionData", {"name":sessionname})
    hidden_images = sb.filter("ViewerImageStatus", {"ref_sessiondata_session":session["def_id"], "status" : "hidden"})
    trash_images = sb.filter("ViewerImageStatus", {"ref_sessiondata_session": session["def_id"], "status" : "trash"})
    return set([status["ref_acquisitionimagedata_image"] for status in hidden_images] + [status["ref_acquisitionimagedata_image"] for status in trash_images])


def retrieveSkippedTiltAngleImages(session, tilt_angle_type):
    session = sb.get("SessionData", {"name" : session})
    scopes = sb.filter("ScopeEMData", {"ref_sessiondata_session" : session["def_id"]})
    rejected_scopes=[]
    for scope in scopes:
        if calcSkipTiltAngle(scope["stage_position_a"], tilt_angle_type):
            rejected_scopes.append(scope)
    images = []
    for scope in rejected_scopes:
        q_result = sb.filter("AcquisitionImageData", {"ref_scopeemdata_scope" : scope})
        images += [image["def_id"] for image in q_result]
    images = set(images)
    return images

def readSessionData(sessionname : str):
    sessiondata=sb.get("SessionData", {"name" : sessionname})
    sessionmetadata={}
    sessionmetadata['session_id']=sessiondata["def_id"]
    sessionmetadata['session_image_path']=sessiondata["image_path"]
    sessionmetadata['session_frame_path']=sessiondata["frame_path"]
    return sessionmetadata

# Retrieves metadata from the database that is used to calculate inputs to motioncor2/motioncor3
def readImageMetadata(imageid: int, has_bad_pixels : bool = False, is_align : bool = False, has_non_zero_dark : bool = False):
    imgmetadata={}
    imgmetadata['imgdata']=sb.get("AcquisitionImageData",{"def_id":imageid})
    if "ref_correctorplandata_corrector_plan" in imgmetadata['imgdata'].keys():
        imgmetadata['correctorplandata']=sb.get("CorrectorPlanData",{"def_id":imgmetadata['imgdata']["ref_correctorplandata_corrector_plan"]})
    else:
        imgmetadata['correctorplandata']={}
        imgmetadata['correctorplandata']["def_id"]=None
        imgmetadata['correctorplandata']["bad_pixels"]=None
        imgmetadata['correctorplandata']["bad_rows"]=None
        imgmetadata['correctorplandata']["bad_cols"]=None

    imgmetadata['sessiondata']=sb.get("SessionData",{"def_id":imgmetadata['imgdata']["ref_sessiondata_session"]})
    imgmetadata['cameraemdata']=sb.get("CameraEMData",{"def_id":imgmetadata['imgdata']["ref_cameraemdata_camera"]})
    imgmetadata['ccdcamera']=sb.get("InstrumentData",{"def_id" : imgmetadata['cameraemdata']["ref_instrumentdata_ccdcamera"]})
    imgmetadata['presetdata']=sb.get("PresetData",{"def_id":imgmetadata['imgdata']["ref_presetdata_preset"]})
    imgmetadata['scope']=sb.get("ScopeEMData", {"def_id":imgmetadata['imgdata']["ref_scopeemdata_scope"]})
    if "frame_time" not in imgmetadata['cameraemdata'].keys():
        imgmetadata['cameraemdata']["frame_time"]=None   
    if "dose" not in imgmetadata['presetdata'].keys():
        imgmetadata['presetdata']['dose'] = None
    imgmetadata['imgdata']["def_timestamp"]=datetime.fromisoformat(imgmetadata['imgdata']["def_timestamp"])
    imgmetadata['frame_aligner_flat']=not (has_bad_pixels or not is_align or has_non_zero_dark)
    imgmetadata['pixelsizecalibrationdata'] = sb.filter("PixelSizeCalibrationData", dict(magnification=imgmetadata["scope"]['magnification'], 
                                                             ref_instrumentdata_tem=imgmetadata["scope"]['ref_instrumentdata_tem'], 
                                                             ref_instrumentdata_ccdcamera=imgmetadata["ccdcamera"]['def_id']))
    if not imgmetadata['pixelsizecalibrationdata']:
        raise RuntimeError("No pixelsize information was found for image %s with mag %d, tem id %d, ccdcamera id %d."
                        % (imgmetadata['imgdata']["filename"], 
                           imgmetadata["scope"]['magnification'], 
                           imgmetadata["scope"]['tem'], 
                           imgmetadata["ccdcamera"]['def_id']))
    imgmetadata['pixelsizedata']=[{"timestamp": datetime.fromisoformat(p["def_timestamp"]), "pixelsize" : p["pixelsize"] } for p in imgmetadata['pixelsizecalibrationdata']]
    # Gain inputs
    if "ref_normimagedata_norm" in imgmetadata['imgdata'].keys():
        imgmetadata['gainmetadata']={}
        imgmetadata['gainmetadata']['normimagedata']=sb.get("NormImageData", {"def_id" : imgmetadata['imgdata']["ref_normimagedata_norm"]})
        imgmetadata['gainmetadata']['sessiondata']=sb.get("SessionData", {"def_id" : imgmetadata['gainmetadata']['normimagedata']["ref_sessiondata_session"]})
        imgmetadata['gain_input']=os.path.join(imgmetadata['gainmetadata']['sessiondata']["image_path"],imgmetadata['gainmetadata']['normimagedata']["mrc_image"])
    else:
        imgmetadata['gainmetadata']={}
        imgmetadata['gainmetadata']['normimagedata']=None
        imgmetadata['gainmetadata']['sessiondata']=None
        imgmetadata['gain_input']=None
    if "ref_darkimagedata_dark" in imgmetadata['imgdata'].keys():
        imgmetadata['darkmetadata']={}
        imgmetadata['darkmetadata']['darkimagedata'] = sb.get("DarkImageData", {"def_id" : imgmetadata['imgdata']['ref_darkimagedata_dark']})
        imgmetadata['darkmetadata']['sessiondata']=sb.get("SessionData", {"def_id" : imgmetadata['darkmetadata']['darkimagedata']["ref_sessiondata_session"]})
        imgmetadata['dark_input']=os.path.join(imgmetadata['darkmetadata']["image_path"],imgmetadata['darkmetadata']['darkimagedata']["mrc_image"])
        imgmetadata['darkmetadata']['cameraemdata']=sb.get("CameraEMData", {"camera":imgmetadata['darkmetadata']['darkimagedata']["ref_cameraemdata_camera"]})
    else:
        imgmetadata['darkmetadata']={}
        imgmetadata['darkmetadata']['darkimagedata']=None
        imgmetadata['darkmetadata']['sessiondata']=None
        imgmetadata['dark_input']=None
        imgmetadata['darkmetadata']['cameraemdata']=None
    return imgmetadata