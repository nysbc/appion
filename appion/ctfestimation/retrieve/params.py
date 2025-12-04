# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center

from ...base.calc import calcCryoSPARCDirectoryType
import json, bson
import numpy as np
from glob import glob
import os

def readCryoSPARCMetadata(cs_path, imgmetadata):
    jobtype=calcCryoSPARCDirectoryType(cs_path)
    csmetadata={}
    if jobtype == "session":
        exposure=readCryoSPARCSessionExposure(cs_path, imgmetadata)
    elif jobtype == "job":
        exposure=readCryoSPARCJobExposure(cs_path, imgmetadata)
    else:
        return csmetadata
    # Fields that need to be populated in ApCtfFind4ParamsData
    csmetadata["bestdb"] = False
    csmetadata["ampcontrast"] = exposure["groups"]["exposure"]["ctf"]["amp_contrast"]
    csmetadata["fieldsize"] = min(exposure["micrograph_shape"])
    csmetadata["cs"] = exposure["groups"]["exposure"]["ctf"]["cs_mm"]
    csmetadata["resmin"] = None
    csmetadata["defstep"] = None
    csmetadata["shift_phase"] = exposure["attributes"]["phase_shift"]

    csmetadata["min_phase_shift"] = None
    csmetadata["max_phase_shift"] = None
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
    csmetadata["fit_data_path"] = os.path.basename(exposure["groups"]["exposure"]["ctf_stats"]["fit_data_path"][0])
    csmetadata["micrograph_path"] = exposure["groups"]["exposure"]["micrograph_blob"]["path"][0]    
    return csmetadata

def readCryoSPARCSessionExposure(cs_path, imgmetadata):
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
    return exposure

def readCryoSPARCJobExposure(cs_path, imgmetadata):
    with open(os.path.join(cs_path,'job.json'), 'rb') as f:
        data = json.load(f)

    ctf=None
    ctf_stats=None
    micrograph_blob=None
    for result in data["output_results"]:
        if result["name"] == "ctf" and result["group_name"]=="exposures":
            if len(result["metafiles"]) == 1:
                ctf_path=os.path.join(cs_path,"..",result["metafiles"][0])
                if not os.path.isfile(ctf_path):
                    continue
                with open(ctf_path, "rb") as f:
                    ctf=np.load(f)
        if result["name"] == "ctf_stats" and result["group_name"]=="exposures":
            if len(result["metafiles"]) == 1:
                with open(os.path.join(cs_path,"..", result["metafiles"][0]), "rb") as f:
                    ctf_stats=np.load(f)
        if result["name"] == "micrograph_blob" and result["group_name"]=="exposures":
            if len(result["metafiles"]) == 1:
                with open(os.path.join(cs_path,"..",result["metafiles"][0]), "rb") as f:
                    micrograph_blob=np.load(f)
    if not list(ctf) or not list(ctf_stats) or not list(micrograph_blob):
        raise RuntimeError("Could not read metadata for exposure.")
    
    idx=0
    for micrograph in micrograph_blob:
        abs_file_path=os.readlink(os.path.join(cs_path,"..",str(micrograph["micrograph_blob/path"].decode())))
        exposure_filename=os.path.basename(abs_file_path)
        if imgmetadata['imgdata']['filename'] == exposure_filename:
            break
        idx+=1
    idx-=1

    exposure={}
    exposure["groups"]={}
    exposure["groups"]["exposure"]={}
    exposure["groups"]["exposure"]["ctf"]={}
    exposure["groups"]["exposure"]["ctf"]["amp_contrast"] = float(ctf[idx]["ctf/amp_contrast"])
    exposure["groups"]["exposure"]["ctf"]["cs_mm"] = float(ctf[idx]["ctf/cs_mm"])
    try:
        exposure["groups"]["exposure"]["ctf"]["phase_shift_rad"] = list(ctf[idx]["ctf/phase_shift_rad"])
    except TypeError:
        exposure["groups"]["exposure"]["ctf"]["phase_shift_rad"] = [float(ctf[idx]["ctf/phase_shift_rad"])]
    exposure["groups"]["exposure"]["ctf"]["df1_A"] = [float(ctf[idx]["ctf/df1_A"])]
    exposure["groups"]["exposure"]["ctf"]["df2_A"] = [float(ctf[idx]["ctf/df2_A"])]
    exposure["groups"]["exposure"]["ctf"]["df_angle_rad"] = [float(ctf[idx]["ctf/df_angle_rad"])]

    exposure["micrograph_shape"] = [int(dim) for dim in micrograph_blob[idx]["micrograph_blob/shape"]]

    exposure["attributes"]={}
    exposure["attributes"]["phase_shift"] = len(exposure["groups"]["exposure"]["ctf"]["phase_shift_rad"]) > 1

    exposure["groups"]["exposure"]["ctf_stats"]={}
    exposure["groups"]["exposure"]["ctf_stats"]['cross_corr'] = [float(ctf_stats[idx]["ctf_stats/cross_corr"])]
    exposure["groups"]["exposure"]["ctf_stats"]["fit_data_path"] = [str(ctf_stats[idx]["ctf_stats/fit_data_path"].decode())]
    exposure["groups"]["exposure"]["micrograph_blob"]={}
    exposure["groups"]["exposure"]["micrograph_blob"]["path"] = [str(micrograph_blob[idx]["micrograph_blob/path"].decode())]

    return exposure