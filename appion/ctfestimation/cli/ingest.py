
import os
import logging
import numpy as np
import bson
from ...motioncorrection.retrieve.params import readImageMetadata
from ..store import saveApCtfFind4ParamsData, saveApAceRunData, saveApCtfData

def readCryoSPARCMetadata():
    with open(r'exposures.bson', 'rb') as f:
        data = bson.decode_all(f.read())
    return data[0]

def process_task(imageid, args, cryosparc_metadata):
    logger=logging.getLogger(__name__)

    imgmetadata=readImageMetadata(imageid)
    exposure=None
    for e in cryosparc_metadata["exposures"]:
        if imgmetadata['imgdata']['filename'] == os.path.basename(exposure["abs_file_path"]):
            exposure=e
            break
    if not exposure:
        raise RuntimeError("Could not find exposure.")

    # Fields that need to be populated in ApCtfFind4ParamsData
    ampcontrast=exposure["groups"]["exposure"]["ctf"]["amp_contrast"]
    #fieldsize=args.fieldsize
    fieldsize=min(exposure["micrograph_shape"])
    cs=exposure["groups"]["exposure"]["ctf"]["cs_mm"]
    shift_phase=exposure["attributes"]["phase_shift"]
    if shift_phase:
        min_phase_shift=exposure["groups"]["exposure"]["ctf"]["phase_shift_rad"][0]
        max_phase_shift=exposure["groups"]["exposure"]["ctf"]["phase_shift_rad"][-1]
    ref_apctffind4paramsdata_ctffind4_params=saveApCtfFind4ParamsData(False, ampcontrast, fieldsize, cs, None, 
                                                                      None, shift_phase, min_phase_shift, max_phase_shift, 
                                                                      None)

    ref_apacerundata_acerun=saveApAceRunData(args["runname"], args["rundir"],imgmetadata['sessiondata']['def_id'], ref_apctffind4paramsdata_ctffind4_params)

    defocus1=exposure["groups"]["exposure"]["ctf"]["df1_A"][0]/1e10
    defocus2=exposure["groups"]["exposure"]["ctf"]["df2_A"][0]/1e10
    defocusinit=min(defocus1, defocus2)
    cross_correlation=exposure["groups"]["exposure"]["ctf_stats"]['cross_corr'][0]
    saveApCtfData(ref_apacerundata_acerun, imageid, cs, defocusinit, ampcontrast, 
                    defocus1, defocus2, None, None, None, None, None, None, None, None, None, None,
                    None, None, None, None, None, None, None,
                    cross_correlation, None, None, None, None)

