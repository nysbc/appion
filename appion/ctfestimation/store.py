# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center

import os
import sinedon.base as sb
import matplotlib.pyplot as plt
import numpy as np

def saveApCtfFind4ParamsData(bestdb, ampcontrast, fieldsize, cs, resmin, defstep, shift_phase, min_phase_shift, max_phase_shift, phase_search_step):
    apctffind4paramsdata = sb.set("ApCtfFind4ParamsData",{"bestdb" : bestdb, 
                                        "ampcontrast" : ampcontrast, 
                                        "fieldsize" : fieldsize, 
                                        "cs" : cs,
                                        "resmin" : resmin,
                                        "defstep" : defstep,
                                        "shift_phase" : shift_phase,
                                        "min_phase_shift" : min_phase_shift,
                                        "max_phase_shift" : max_phase_shift,
                                        "phase_search_step" : phase_search_step})
    return apctffind4paramsdata["def_id"]

def saveApAceRunData(runname, rundir, ref_sessiondata_session, ref_apctffind4paramsdata_ctffind4_params):
    path = sb.get("ApPathData", {"path" : os.path.abspath(rundir)})
    if not path:
        path["def_id"]=None
    apacerundata = sb.set("ApAceRunData",{"runname" : runname, 
                                         "ref_apctffind4paramsdata_ctffind4_params" : ref_apctffind4paramsdata_ctffind4_params, 
                                         "ref_sessiondata_session" : ref_sessiondata_session, 
                                         "ref_appathdata_path" : path["def_id"]})
    return apacerundata["def_id"]

def saveApCtfData(ref_apacerundata_acerun, ref_acquisitionimagedata_image, cs, defocusinit, amplitude_contrast, 
                  defocus1, defocus2, angle_astigmatism, ctffind4_resolution,
                  confidence, confidence_d, confidence_30_10, confidence_5_peak, overfocus_conf_30_10, 
                  overfocus_conf_5_peak, resolution_80_percent, resolution_50_percent,
                  graph1, graph2, graph3, graph4, localplot, localCTFstarfile, ctfvalues_file,
                  cross_correlation, tilt_angle, tilt_axis_angle, mat_file, extra_phase_shift):
    apctfdata = sb.set("ApCtfData",{"ref_apacerundata_acerun": ref_apacerundata_acerun,
                                    "ref_acquisitionimagedata_image": ref_acquisitionimagedata_image,
                                    "cs": cs,
                                    "defocusinit": defocusinit,
                                    "amplitude_contrast": amplitude_contrast,
                                    "defocus1": defocus1,
                                    "defocus2": defocus2,
                                    "angle_astigmatism": angle_astigmatism,
                                    "ctffind4_resolution": ctffind4_resolution,
                                    "confidence": confidence,
                                    "confidence_d": confidence_d,
                                    "confidence_30_10": confidence_30_10,
                                    "confidence_5_peak": confidence_5_peak,
                                    "overfocus_conf_30_10": overfocus_conf_30_10,
                                    "overfocus_conf_5_peak": overfocus_conf_5_peak,
                                    "resolution_80_percent": resolution_80_percent,
                                    "resolution_50_percent": resolution_50_percent,
                                    "graph1": graph1,
                                    "graph2": graph2,
                                    "graph3": graph3,
                                    "graph4": graph4,
                                    "localplot": localplot,
                                    "localCTFstarfile": localCTFstarfile,
                                    "ctfvalues_file": ctfvalues_file,
                                    "cross_correlation": cross_correlation,
                                    "tilt_angle": tilt_angle,
                                    "tilt_axis_angle": tilt_axis_angle,
                                    "mat_file": mat_file,
                                    "extra_phase_shift": extra_phase_shift})
    return apctfdata["def_id"]

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
    plt.close()