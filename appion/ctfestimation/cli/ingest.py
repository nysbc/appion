# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center

import os
import logging
import numpy as np
from ...base.retrieve import readImageMetadata
from ..retrieve.params import readCryoSPARCMetadata
from ..store import saveApCtfFind4ParamsData, saveApAceRunData, saveApCtfData, savePowAvRot

def process_task(imageid, args, cryosparc_dir):
    logger=logging.getLogger(__name__)

    imgmetadata=readImageMetadata(imageid)
    csmetadata=readCryoSPARCMetadata(cryosparc_dir, imgmetadata)
    if not csmetadata:
        raise RuntimeError(f"Could not determine if {cryosparc_dir} was a job or a live session.")

    logger.info("Saving metadata to ApCtfFind4ParamsData.")
    ref_apctffind4paramsdata_ctffind4_params = saveApCtfFind4ParamsData(csmetadata["bestdb"], csmetadata["ampcontrast"], csmetadata["fieldsize"], csmetadata["cs"], csmetadata["resmin"],
                                                                            csmetadata["defstep"], csmetadata["shift_phase"], csmetadata["min_phase_shift"], csmetadata["max_phase_shift"],
                                                                            csmetadata["phase_search_step"])

    logger.info("Saving metadata to ApAceRunData.")
    ref_apacerundata_acerun=saveApAceRunData(args["runname"], args["rundir"],imgmetadata['sessiondata']['def_id'], ref_apctffind4paramsdata_ctffind4_params)

    fit_data_path = os.path.join(cryosparc_dir, csmetadata['fit_data_path'])
    if not os.path.exists(fit_data_path):
        raise RuntimeError("Could not find ctfdiag file for exposure.")
    ctfdiag = np.load(fit_data_path)
    opimages_dir = os.path.join(args["rundir"],"opimages")
    if not os.path.exists(opimages_dir):
        os.makedirs(opimages_dir)
    powAvRotFilename = os.path.basename(csmetadata["micrograph_path"]).replace(".mrc","-pow_avrot.png")
    logger.info("Saving CTF power spectrum plot.")
    powAvRotPath = os.path.join(opimages_dir, powAvRotFilename)
    savePowAvRot(powAvRotPath, ctfdiag, csmetadata["defocus1"], csmetadata["defocus2"], csmetadata["df_angle_rad"])
    logger.info("Saving metadata to ApCtfData.")
    saveApCtfData(ref_apacerundata_acerun, imageid, csmetadata["cs"], csmetadata["defocusinit"], csmetadata["ampcontrast"], 
              csmetadata["defocus1"], csmetadata["defocus2"], csmetadata["angle_astigmatism"], csmetadata["ctffind4_resolution"],
              csmetadata["confidence"], csmetadata["confidence_d"], csmetadata["confidence_30_10"], csmetadata["confidence_5_peak"], csmetadata["overfocus_conf_30_10"], 
              csmetadata["overfocus_conf_5_peak"], csmetadata["resolution_80_percent"], csmetadata["resolution_50_percent"],
              csmetadata["graph1"], csmetadata["graph2"], csmetadata["graph3"], powAvRotFilename, csmetadata["localplot"], csmetadata["localCTFstarfile"], csmetadata["ctfvalues_file"],
              csmetadata["cross_correlation"], csmetadata["tilt_angle"], csmetadata["tilt_axis_angle"], csmetadata["mat_file"], csmetadata["extra_phase_shift"])