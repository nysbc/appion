# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center

from ...base.calc import calcCryoSPARCDirectoryType
import json, bson
import numpy as np
import os

def readCryoSPARCMetadata(cs_path, imgmetadata):
    jobtype=calcCryoSPARCDirectoryType(cs_path)
    if jobtype == "session":
        csmetadata=readCryoSPARCSessionMetadata(cs_path, imgmetadata)
    elif jobtype == "job":
        csmetadata=readCryoSPARCJobMetadata(cs_path)
    else:
        csmetadata={}
    return csmetadata

def readCryoSPARCSessionMetadata(cs_path, imgmetadata):
    csmetadata = {}
    with open(os.path.join(cs_path,'exposures.bson'), 'rb') as f:
        data = bson.decode_all(f.read())
    exposure=None
    if data and type(data)==list:
        for e in data[0]["exposures"]:
            exposure_filename=os.path.basename(e["abs_file_path"])
            if imgmetadata['imgdata']['filename'] == exposure_filename:
                exposure=e
                break
        if not exposure:
            raise RuntimeError("Could not find exposure.")

    # Fields that need to be populated in ApCtfFind4ParamsData
    csmetadata["bestdb"] = False
    csmetadata["ampcontrast"] = exposure["groups"]["exposure"]["ctf"]["amp_contrast"]
    csmetadata["fieldsize"] = min(exposure["micrograph_shape"])
    csmetadata["cs"] = exposure["groups"]["exposure"]["ctf"]["cs_mm"]
    csmetadata["resmin"] = None
    csmetadata["defstep"] = None
    csmetadata["shift_phase"] = exposure["attributes"]["phase_shift"]

    if csmetadata["shift_phase"]:
        csmetadata["min_phase_shift"] = exposure["groups"]["exposure"]["ctf"]["phase_shift_rad"][0]
        csmetadata["max_phase_shift"] = exposure["groups"]["exposure"]["ctf"]["phase_shift_rad"][-1]
    csmetadata["phase_search_step"] = None

    csmetadata["defocus1"] = exposure["groups"]["exposure"]["ctf"]["df1_A"][0] / 1e10
    csmetadata["defocus2"] = exposure["groups"]["exposure"]["ctf"]["df2_A"][0] / 1e10
    csmetadata["defocusinit"] = min(csmetadata["defocus1"], csmetadata["defocus2"])
    csmetadata["cross_correlation"] = exposure["groups"]["exposure"]["ctf_stats"]['cross_corr'][0]
    csmetadata["angle_astigmatism"] = None
    csmetadata["ctffind4_resolution"] = None
    csmetadata["confidence"] = None
    csmetadata["confidence_d"] = None
    csmetadata["confidence_30_10"] = None
    csmetadata["confidence_5_peak"] = None
    csmetadata["overfocus_conf_30_10"] = None
    csmetadata["overfocus_conf_5_peak"] = None
    csmetadata["resolution_80_percent"] = None
    csmetadata["resolution_50_percent"] = None
    csmetadata["graph1"] = None
    csmetadata["graph2"] = None
    csmetadata["graph3"] = None
    csmetadata["graph4"] = None
    csmetadata["localplot"] = None
    csmetadata["localCTFstarfile"] = None
    csmetadata["ctfvalues_file"] = None
    csmetadata["tilt_angle"] = None
    csmetadata["tilt_axis_angle"] = None
    csmetadata["mat_file"] = None
    csmetadata["extra_phase_shift"] = None
    csmetadata["df_angle_rad"] = exposure["groups"]["exposure"]["ctf"]["df_angle_rad"][0]
    csmetadata["fit_data_path"] = exposure["groups"]["exposure"]["ctf_stats"]["fit_data_path"][0]
    csmetadata["micrograph_path"] = exposure["groups"]["exposure"]["micrograph_blob"]["path"][0]
    return csmetadata

def readCryoSPARCJobMetadata(cs_path, imgmetadata):
    csmetadata = {}
    with open(os.path.join(cs_path,'job.json'), 'rb') as f:
        data = json.load(f)

    # Retrieve the job ID for the import micrographs job
    input_job=""
    for slotgroup in data["input_slot_groups"]:
        if slotgroup["name"] == "exposures":
            if "connections" in slotgroup.keys():
                for connection in slotgroup["connections"]:
                    if "slots" in connection.keys():
                        for slot in connection["slots"]:
                            if slot["slot_name"] == "micrograph_blob":
                                input_job=slot["job_uid"]
    
    # Open the import job
    if input_job:
        with open(os.path.join(cs_path,"..", input_job, 'job.json'), 'rb') as f:
            input_data = json.load(f)
    else:
        raise RuntimeError

    # What about micrographs that are the output of a CS motion correction job?
    # Here we're just considering imported micrographs from Appion.
    input_files=set()
    imported_micrographs=False
    for r in input_data["output_results"]:
        if r["group_name"] == "imported_micrographs" or r["group_name"] == "micrographs":
            if r["group_name"] == "imported_micrographs":
                imported_micrographs=True
            input_files.add([mf for mf in r["metafiles"]])

    if input_files:
        for input_file in input_files:
            with open(os.path.join(cs_path,"..", input_file), 'rb') as f:
                input_data_cs = np.load(f)
    else:
        raise RuntimeError
    
    micrograph_paths=[path.decode() for path in input_data_cs["micrograph_blob/path"]]
    for micrograph_path in micrograph_paths:
        if os.path.basename(micrograph_path) == imgmetadata["filename"]:
            pass


    # Fields that need to be populated in ApCtfFind4ParamsData
    csmetadata["bestdb"] = False
    csmetadata["ampcontrast"] = float(data["outputs"]["spec"]["amp_contrast"])
    csmetadata["fieldsize"] = min(exposure["micrograph_shape"])
    csmetadata["cs"] = float(data["outputs"]["summary"]["ctf/cs_mm"])
    csmetadata["resmin"] = None
    csmetadata["defstep"] = None
    ps_max_default=3.141592653589793
    csmetadata["shift_phase"] = (int(data["outputs"]["spec"]["phase_shift_min"]) != 0) and (round(float(data["outputs"]["spec"]["phase_shift_max"]) == 3.142))

    if csmetadata["shift_phase"]:
        csmetadata["min_phase_shift"] = float(data["outputs"]["spec"]["phase_shift_min"])
        csmetadata["max_phase_shift"] = float(data["outputs"]["spec"]["phase_shift_max"])
    csmetadata["phase_search_step"] = None

    csmetadata["defocus1"] = exposure["groups"]["exposure"]["ctf"]["df1_A"][0] / 1e10
    csmetadata["defocus2"] = exposure["groups"]["exposure"]["ctf"]["df2_A"][0] / 1e10
    csmetadata["defocusinit"] = min(csmetadata["defocus1"], csmetadata["defocus2"])
    csmetadata["cross_correlation"] = exposure["groups"]["exposure"]["ctf_stats"]['cross_corr'][0]
    csmetadata["angle_astigmatism"] = None
    csmetadata["ctffind4_resolution"] = None
    csmetadata["confidence"] = None
    csmetadata["confidence_d"] = None
    csmetadata["confidence_30_10"] = None
    csmetadata["confidence_5_peak"] = None
    csmetadata["overfocus_conf_30_10"] = None
    csmetadata["overfocus_conf_5_peak"] = None
    csmetadata["resolution_80_percent"] = None
    csmetadata["resolution_50_percent"] = None
    csmetadata["graph1"] = None
    csmetadata["graph2"] = None
    csmetadata["graph3"] = None
    csmetadata["graph4"] = None
    csmetadata["localplot"] = None
    csmetadata["localCTFstarfile"] = None
    csmetadata["ctfvalues_file"] = None
    csmetadata["tilt_angle"] = None
    csmetadata["tilt_axis_angle"] = None
    csmetadata["mat_file"] = None
    csmetadata["extra_phase_shift"] = None
    csmetadata["df_angle_rad"] = exposure["groups"]["exposure"]["ctf"]["df_angle_rad"][0]
    csmetadata["fit_data_path"] = exposure["groups"]["exposure"]["ctf_stats"]["fit_data_path"][0]
    csmetadata["micrograph_path"] = exposure["groups"]["exposure"]["micrograph_blob"]["path"][0]
    return csmetadata