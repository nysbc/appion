from sinedon.models.leginon import SessionData, PresetData, AcquisitionImageData, ScopeEMData, ViewerImageStatus
from sinedon.models.appion import ApAssessmentData
import json
from .calc import calcSkipTiltAngle, calcSlicedImageSet
from fcntl import flock, LOCK_EX, LOCK_UN

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
        session = SessionData.objects.get(name=session)
        presets = PresetData.objects.filter(name=preset,ref_sessiondata_session=session.def_id)
        images = []
        for p in presets:
            q_result = AcquisitionImageData.objects.filter(ref_sessiondata_session=session.def_id, ref_presetdata_preset=p.def_id)
            images += [image.def_id for image in q_result]
        images = set(images)
    else:
        session = SessionData.objects.get(name=session)
        images = AcquisitionImageData.objects.filter(ref_sessiondata_session=session.def_id)
        images = set([image.def_id for image in images])
    return images

def retrieveRejectedImages(images, session, start : None, stop : None, tilt_angle_type):
    skipped_tilt_angle_images = retrieveSkippedTiltAngleImages(session, tilt_angle_type)
    if start and stop:
        sliced_images = calcSlicedImageSet(images, start, stop)
    else:
        sliced_images = set()
    viewer_rejects = retrieveViewerRejects(session)
    assessment_rejects = retrieveAssessmentRejects()
    return skipped_tilt_angle_images | sliced_images | viewer_rejects | assessment_rejects

def retrieveAssessmentRejects():
    #TODO Might want to limit this to a range of image IDs for the current session only.
    assessment_rejects = ApAssessmentData.objects.filter(selectionkeep=0)
    if assessment_rejects:
        return set([reject.ref_acquisitionimagedata_image for reject in assessment_rejects])
    else:
        return set()

def retrieveViewerRejects(session):
    '''
    Images that are hidden in the viewer or are trash are rejected.
    '''
    session = SessionData.objects.get(name=session)
    hidden_images = ViewerImageStatus.objects.filter(ref_sessiondata_session=session, status="hidden")
    trash_images = ViewerImageStatus.objects.filter(ref_sessiondata_session=session, status="trash")
    return set([status.ref_acquisitionimagedata_image.def_id for status in hidden_images] + [status.ref_acquisitionimagedata_image.def_id for status in trash_images])


def retrieveSkippedTiltAngleImages(session, tilt_angle_type):
    session = SessionData.objects.get(name=session)
    scopes = ScopeEMData.objects.filter(ref_sessiondata_session=session)
    rejected_scopes=[]
    for scope in scopes:
        if calcSkipTiltAngle(scope.stage_position_a, tilt_angle_type):
            rejected_scopes.append(scope)
    images = []
    for scope in rejected_scopes:
        q_result = AcquisitionImageData.objects.filter(ref_scopeemdata_scope=scope)
        images += [image.def_id for image in q_result]
    images = set(images)
    return images

# This isn't necessary for ctffind or motioncor2, since images that have been processed are 
# recorded in the Appion database, but it might be useful in the future for applications that don't
# have this info stored in the database.
def readCheckpoint(checkpoint_path):
    with open(checkpoint_path, "r") as f:
        flock(f, LOCK_EX)
        images=set(json.load(f))
        flock(f, LOCK_UN)
    return images

def readSessionData(sessionname : str):
    sessiondata=SessionData.objects.get(name=sessionname)
    sessionmetadata={}
    sessionmetadata['session_id']=sessiondata.def_id
    sessionmetadata['session_image_path']=sessiondata.image_path
    sessionmetadata['session_frame_path']=sessiondata.frame_path
    return sessionmetadata