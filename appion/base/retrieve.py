from sinedon.models.leginon import SessionData, PresetData, AcquisitionImageData
import json

# The idea here is to have two sets of image IDs.  One set (queried from the database)
# contains all images for a session (optionally broken down by preset as well).
# The second set (loaded from a JSON checkpoint file in the run directory)
# contains all of the image IDs for images that have already been processed.
# To determine which images need to be processed, we get the set difference
# between all images and checkpointed images.
def readImageSet(session, preset = None):
    if preset:
        if preset == "manual":
            preset = None
        session = SessionData.objects.get(name=session)
        preset = PresetData.objects.get(name=preset,ref_sessiondata_session=session.def_id)
        images = AcquisitionImageData.objects.filter(ref_sessiondata_session=session.def_id, ref_presetdata_preset=preset.def_id)
    else:
        session = SessionData.objects.get(name=session)
        images = AcquisitionImageData.objects.filter(ref_sessiondata_session=session.def_id)
    return set([image.def_id for image in images])

def readImageSetCheckpoint(checkpoint_path):
    with open(checkpoint_path, "r") as f:
        images=set(json.load(f))
    return images

