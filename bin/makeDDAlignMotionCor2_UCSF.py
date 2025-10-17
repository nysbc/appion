#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

import argparse
import os
from fcntl import flock, LOCK_EX, LOCK_UN
from appion.base.cli import constructGlobalParser
from appion.motioncorrection.cli.parser import constructMotionCorParser
from appion.motioncorrection.retrieve.images import retrieveDoneImages
import sinedon.setup

def main():
    parser = argparse.ArgumentParser(parents=[constructGlobalParser(), constructMotionCorParser()])
    args = parser.parse_args()
    sinedon.setup(args.projectid)
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
    with open(lockfile, 'r+') as f:
        flock(f, LOCK_EX)
        f.seek(0)
        f.truncate()
        f.write(str(os.getpid()))
        session_metadata=readSessionData(args.sessionname)
        arg_dict=vars(args)
        loop(lambda imageid : process_task(imageid, arg_dict, args.cryosparc_import_dir, args.cryosparc_motioncorrection_dir),
                arg_dict,
                lambda : retrieveDoneImages(args.rundir, session_metadata['session_id']),
                lambda : constructMotionCor2JobMetadata(arg_dict),
                lambda jobmetadata : updateApAppionJobData(jobmetadata['ref_apappionjobdata_job'], dict(status="D")))
        flock(f, LOCK_UN)
 
if __name__ == '__main__':
    main()
