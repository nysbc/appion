# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

import os
import sinedon.base as sb

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