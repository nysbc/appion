from sinedon.models.leginon import SessionData, PresetData, AcquisitionImageData
import json
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