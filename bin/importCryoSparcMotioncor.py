#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2026 New York Structural Biology Center

import argparse
import os
from glob import glob
import json
from fcntl import flock, LOCK_EX, LOCK_UN
from appion.base.cli import constructGlobalParser
from appion.motioncorrection.cli.parser import constructCSMotionCorParser
import sinedon.setup

def find_cslive_session_dir(cs_project, cs_session):
    csd=""
    p_jsons=glob("/h[123]/*/cryosparc/*/project.json")
    for p_json in p_jsons:
        try:
            with open(p_json,"r") as f:
                j=json.load(f)
            if "uid_num" in j.keys():
                uid_num=int(j["uid_num"])
            elif "uid" in j.keys():
                uid_num=int(j["uid"].strip("P"))
            else:
                continue
            if uid_num == cs_project:
                csd=os.path.join(os.path.dirname(p_json),f"S{cs_session}")
                if os.path.exists(csd):
                    break
        except:
            continue
    return csd


def main():
    parser = argparse.ArgumentParser(parents=[constructGlobalParser(), constructCSMotionCorParser()])
    args = parser.parse_args()
    sinedon.setup(args.projectid)
    from appion.motioncorrection.retrieve.images import retrieveDoneImages
    from appion.motioncorrection.cli.constructors import constructMotionCor2JobMetadata
    from appion.base.retrieve import readSessionData
    from appion.base.store import updateApAppionJobData
    from appion.base.loop import loop
    from appion.motioncorrection.cli.ingest import process_task
    if not os.path.exists(args.rundir):
        os.makedirs(args.rundir)
    # Create a lock in the run directory so that only one loop can run at a time.
    lockfile=os.path.join(args.rundir, ".lock")
    if not os.path.exists(lockfile):
        f=open(lockfile, "w")
        f.close()
    cslive_session_dir=find_cslive_session_dir(args.cs_project, args.cs_session)
    if not cslive_session_dir:
        raise RuntimeError(f"No session directory found for P{args.cs_project}, S{args.cs_session}")
    cryosparc_import_dir=os.path.join(cslive_session_dir, "import_movies")
    cryosparc_motioncorrection_dir(cslive_session_dir, "motioncorrected")
    with open(lockfile, 'r+') as f:
        flock(f, LOCK_EX)
        f.seek(0)
        f.truncate()
        f.write(str(os.getpid()))
        session_metadata=readSessionData(args.sessionname)
        arg_dict=vars(args)
        if "FLOAT16_IMAGE" in os.environ.keys():
            float16_image_path=os.environ["FLOAT16_IMAGE"]
            p=lambda imageid : process_task(imageid, arg_dict, cryosparc_import_dir, cryosparc_motioncorrection_dir, float16_image_path)
        else:
            p=lambda imageid : process_task(imageid, arg_dict, cryosparc_import_dir, cryosparc_motioncorrection_dir)
        loop(p,
                arg_dict,
                lambda : retrieveDoneImages(args.rundir, session_metadata['session_id']),
                lambda : constructMotionCor2JobMetadata(arg_dict),
                lambda jobmetadata : updateApAppionJobData(jobmetadata['ref_apappionjobdata_job'], dict(status="D")))
        flock(f, LOCK_UN)
 
if __name__ == '__main__':
    main()
