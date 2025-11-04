
import os
import logging
import numpy as np
import matplotlib.pyplot as plt
import bson
from ...motioncorrection.retrieve.params import readImageMetadata
from ..store import saveApCtfFind4ParamsData, saveApAceRunData, saveApCtfData

def readCryoSPARCMetadata():
    with open(r'exposures.bson', 'rb') as f:
        data = bson.decode_all(f.read())
    return data[0]

def process_task(imageid, args, cryosparc_metadata, cryosparc_dir):
    logger=logging.getLogger(__name__)

    imgmetadata=readImageMetadata(imageid)
    exposure=None
    exposure_filename=os.path.basename(exposure["abs_file_path"])
    for e in cryosparc_metadata["exposures"]:
        if imgmetadata['imgdata']['filename'] == exposure_filename:
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
    # TODO Make graphs and add them to db
    df_angle_rad = exposure["groups"]["exposure"]["ctf"]["df_angle_rad"][0]
    rel_fit_data_path = exposure["groups"]["exposure"]["ctf_stats"]["fit_data_path"][0]
    abs_fit_data_path = os.path.join(cryosparc_dir, rel_fit_data_path)
    if not os.path.exists(abs_fit_data_path):
        raise RuntimeError("Could not find ctfdiag file for exposure.")
    ctfdiag = np.load(abs_fit_data_path)
    opimages_dir = os.path.join(args["rundir"],"opimages")
    if not os.path.exists(opimages_dir):
        os.makedirs(opimages_dir)
    powAvRotFilename = os.path.basename(exposure["groups"]["exposure"]["micrograph_blob"]["path"][0]).replace(".mrc","-pow_avrot.png")
    powAvRotPath = os.path.join(opimages_dir, powAvRotFilename)
    savePowAvRot(powAvRotPath, ctfdiag, defocus1, defocus2, df_angle_rad)
    saveApCtfData(ref_apacerundata_acerun, imageid, cs, defocusinit, ampcontrast, 
                    defocus1, defocus2, None, None, None, None, None, None, None, None, None, None,
                    None, None, None, powAvRotFilename, None, None, None,
                    cross_correlation, None, None, None, None)

def savePowAvRot(figpath, ctfdiag, defocus1 ,defocus2, df_angle_rad):
    # Convert defocus to microns for plot
    defocus1 = defocus1*1e-06
    defocus2 = defocus1*1e-06
    # Preparing the raw data for plotting
    power_spectrum = ctfdiag['EPA_trim'] - ctfdiag['BGINT'] + 0.5
    ctf = ctfdiag['ENVINT'] * (2 * ctfdiag['CTF']**2 - 1) + 0.5
    cc = ctfdiag['CC']
    ctf_x = ctfdiag['freqs_trim']

    resIndex = np.where(cc < 0.143)[0][0]
    resLimit = ctf_x[resIndex-1]

    plt.figure(figsize = [12, 6])
    plt.title(f"DF1={defocus1:.2f}µm   DF2={defocus2:.2f}µm   ANGAST={df_angle_rad:.1f}   FIT={1/resLimit:.2f}Å")
    plt.plot(ctf_x, power_spectrum, c='black', linestyle='-', label='PS')
    plt.plot(ctf_x, ctf, c="red", linestyle="-", label="CTF")
    plt.plot(ctf_x, cc, c="mediumturquoise", marker="o", ms=3, label="Fit")
    plt.vlines(x=resLimit, ymin= -1, ymax= 1.2, color="green")
    plt.xlabel('Spatial Frequency (1/Å)')
    plt.ylim([-0.05, 1.1])
    plt.xlim(0, ctf_x.max())
    plt.legend()
    plt.minorticks_on()
    plt.grid(which='major')
    plt.grid(which='minor', linestyle=':', color='lightgray')
    plt.savefig(figpath, format="png")