
import os
import logging
from ..calc.internal import calcTotalRenderedFrames, calcPixelSize
from .constructors import constructMotionCor2JobMetadata
from ..store import saveFrameTrajectory, constructAlignedCamera, constructAlignedPresets, constructAlignedImage, uploadAlignedImage, saveDDStackParamsData, saveMotionCorrLog
from ...base.retrieve import readImageMetadata
from ..retrieve.params import readInputPath
import numpy as np

def process_task(imageid, args, cryosparc_import_dir, cryosparc_motioncorrection_dir):
    logger=logging.getLogger(__name__)

    jobmetadata=constructMotionCor2JobMetadata(args)

    imgmetadata=readImageMetadata(imageid)
    input_path = readInputPath(imgmetadata['sessiondata']['frame_path'],imgmetadata['imgdata']['filename'])
    import_paths = matchInputImport(input_path, cryosparc_import_dir)
    for import_path in import_paths:
        output_prefix = calcOutputPrefix(import_path)
        framestackpath=os.path.join(args["rundir"],os.path.basename(input_path))

        cs_traj_file=os.path.join(cryosparc_motioncorrection_dir, output_prefix+"_rigid_traj.npy")
        aligned_output_file=os.path.join(cryosparc_motioncorrection_dir, output_prefix+"_patch_aligned.mrc")
        aligned_dw_output_file=os.path.join(cryosparc_motioncorrection_dir, output_prefix+"_patch_aligned_doseweighted.mrc")
        cryosparc_outputs_exist=True
        for cryosparc_output in [cs_traj_file, aligned_output_file, aligned_dw_output_file]:
            if not os.path.exists(cryosparc_output):
                cryosparc_outputs_exist=False
        if not cryosparc_outputs_exist:
            continue

        shifts=readShifts(cs_traj_file)
        motioncorr_log_path=os.path.splitext(framestackpath)[0]+"_Log.txt"
        logger.info("Saving out motioncorr-formatted log for %d to %s." % (imageid, motioncorr_log_path))
        saveMotionCorrLog(shifts, motioncorr_log_path, args['startframe'], calcTotalRenderedFrames(imgmetadata['cameraemdata']['nframes'], args['rendered_frame_size']), args['bin'])

        framelist=[]
        nframes=0
        trim=0
        aligned_camera_id = constructAlignedCamera(imgmetadata['cameraemdata']['def_id'], args['square'], args['bin'], trim, framelist, nframes)

        aligned_image_filename = imgmetadata['imgdata']['filename']+"-%s" % args['alignlabel']
        aligned_image_mrc_image = aligned_image_filename + ".mrc"
        if not os.path.exists(imgmetadata["sessiondata"]["image_path"]):
            raise RuntimeError("Session path does not exist at %s." % imgmetadata["sessiondata"]["image_path"])
        abs_path_aligned_image_mrc_image=os.path.join(imgmetadata["sessiondata"]["image_path"],aligned_image_mrc_image)
        if os.path.lexists(abs_path_aligned_image_mrc_image):
            os.unlink(abs_path_aligned_image_mrc_image)
        if os.path.exists(aligned_output_file):
            # In the future, we may want to catch any exceptions involving a cross-device link and run shutil.copy.
            os.link(aligned_output_file, abs_path_aligned_image_mrc_image)
            logger.info("%s linked to %s." % (abs_path_aligned_image_mrc_image, aligned_output_file))
            logger.info("Constructing aligned image record for %d." % imageid)
            aligned_preset_id = constructAlignedPresets(imgmetadata['presetdata']['def_id'], aligned_camera_id, alignlabel=args['alignlabel'])
            aligned_image_id = constructAlignedImage(imageid, aligned_preset_id, aligned_camera_id, aligned_image_mrc_image, aligned_image_filename)
            
        aligned_image_dw_filename = imgmetadata['imgdata']['filename']+"-%s-DW" % args['alignlabel']
        aligned_image_dw_mrc_image = aligned_image_dw_filename + ".mrc"
        abs_path_aligned_image_dw_mrc_image = os.path.join(imgmetadata["sessiondata"]["image_path"],aligned_image_dw_mrc_image)
        if os.path.lexists(abs_path_aligned_image_dw_mrc_image):
            os.unlink(abs_path_aligned_image_dw_mrc_image)
        if os.path.exists(aligned_dw_output_file):
            # In the future, we may want to catch any exceptions involving a cross-device link and run shutil.copy.
            os.link(aligned_dw_output_file, abs_path_aligned_image_dw_mrc_image)
            logger.info("%s linked to %s." % (abs_path_aligned_image_dw_mrc_image, aligned_output_file.replace(".mrc","_DW.mrc")))
            logger.info("Constructing aligned, dose-weighted image record for %d." % imageid)
            aligned_preset_dw_id = constructAlignedPresets(imgmetadata['presetdata']['def_id'], aligned_camera_id, alignlabel=args['alignlabel']+"-DW")
            aligned_image_dw_id = constructAlignedImage(imageid, aligned_preset_dw_id, aligned_camera_id, aligned_image_dw_mrc_image, aligned_image_dw_filename)
        # Frame trajectory only saved for aligned_image_id: https://github.com/nysbc/appion-slurm/blob/814544a7fee69ba7121e7eb1dd3c8b63bc4bb75a/appion/appionlib/apDDLoop.py#L89-L107
        trajdata_id=saveFrameTrajectory(aligned_image_id, jobmetadata['ref_apddstackrundata_ddstackrun'], shifts)
        # This is only used by manualpicker.py so it can go away.  Just making a note of it in a commit for future me / someone.
        #saveApAssessmentRunData(imgmetadata['session_id'], assessment)
        # Seems mostly unused?  Might have been used with a prior implementation of motion correction?  Fields seem to mostly be filled with nulls in the MEMC database.
        # Not entirely sure that we want to pass args["preset"] in here.  Maybe we're supposed to pass in the aligned preset in addition to or instead?
        # Difficult to know for sure, since it's not obvious what this table even exists for (at least to the author of this comment).
        saveDDStackParamsData(args['preset'], args['align'], args['bin'], None, None, None, None)
        #saveDDStackParamsData(args['preset'], args['align'], args['bin'], ref_apddstackrundata_unaligned_ddstackrun, method, ref_apstackdata_stack, ref_apdealignerparamsdata_de_aligner)

        # These need to happen last because they create records that are used to determine if an image is done or not in retrieveDoneImages.
        # Every other step in this function should be idempotent/capable of being run multiple times, but these two function invocations
        # finalize the image for the specified preset/settings/alignment label.
        pixsize = calcPixelSize(imgmetadata['pixelsizedata'], imgmetadata['cameraemdata']['subd_binning_x'], imgmetadata['imgdata']['def_timestamp'])
        logger.info("Uploading aligned image record for %d." % imageid)
        uploadAlignedImage(imageid, aligned_image_id, jobmetadata['ref_apddstackrundata_ddstackrun'], shifts, pixsize, False)
        logger.info("Uploading aligned, dose-weighted image record for %d." % imageid)
        uploadAlignedImage(imageid, aligned_image_dw_id, jobmetadata['ref_apddstackrundata_ddstackrun'], shifts, pixsize, True, trajdata_id)

def readShifts(cs_traj_file):
    traj=np.load(cs_traj_file)
    points = traj[0]
    x = list(points[:,0]-points[0,0])
    y = list(points[:,1]-points[0,1])
    shifts=[coordinate for coordinate in zip(x,y)]
    return shifts

def matchInputImport(input_path, cryosparc_import_dir):
    matches=[]
    input_path=os.path.abspath(input_path.strip())
    for dirpath, _, filenames in os.walk(cryosparc_import_dir):
        for filename in filenames:
            fullpath=os.path.join(dirpath, filename)
            target=os.readlink(fullpath)
            target=os.path.abspath(target.strip())
            if target == input_path:
                matches.append(fullpath)
    return set(matches)

def calcOutputPrefix(import_path):
    try:
        return os.path.splitext(os.path.basename(import_path))[0]
    except:
        return None