#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

import argparse
import yaml
import os
from fcntl import flock, LOCK_EX, LOCK_UN
from appion.base.cli import constructGlobalParser
from appion.motioncorrection.cli.parser import constructMotionCorParser
import sinedon.setup

def main():
    parser = argparse.ArgumentParser(parents=[constructGlobalParser(), constructMotionCorParser()])
    args = parser.parse_args()
    sinedon.setup(args.projectid)
    from appion.motioncorrection.cli.pipeline import pipeline
    from appion.motioncorrection.cli.constructors import constructMotionCor2JobMetadata
    from appion.motioncorrection.retrieve.images import retrieveDoneImages
    from appion.base.retrieve import readSessionData
    from appion.base.store import updateApAppionJobData
    from appion.base.loop import loop
    from appion.base.cluster import constructCluster
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
        # The cluster config can be set via environment variable instead of the CLI flag.
        # This is necessary for backwards compatibility since the myamiweb web UI will not add the clusterconfig flag at present.
        clusterconfig={}
        if "DASK_CLUSTER_CONFIG" in os.environ.keys():
            clusterconfig_path=os.environ["DASK_CLUSTER_CONFIG"]
            if os.path.exists(clusterconfig_path):
                with open(clusterconfig_path,"r") as f:
                    clusterconfig=yaml.load(f, Loader=yaml.Loader)
            else:
                raise RuntimeError("Dask cluster configuration at %s does not exist." % clusterconfig_path)
        else:
            clusterconfig_path=args.clusterconfig
            if os.path.exists(clusterconfig_path):
                with open(clusterconfig_path,"r") as f:
                    clusterconfig=yaml.load(f, Loader=yaml.Loader)
            else:
                raise RuntimeError("Dask cluster configuration at %s does not exist." % clusterconfig_path)
        session_metadata=readSessionData(args.sessionname)
        cluster=constructCluster(clusterconfig)
        loop(pipeline,
                vars(args),
                cluster,
                lambda : retrieveDoneImages(args.rundir, session_metadata['session_id']),
                lambda : constructMotionCor2JobMetadata(vars(args)),
                lambda jobmetadata : updateApAppionJobData(jobmetadata['ref_apappionjobdata_job'], "D"))
        flock(f, LOCK_UN)
 
if __name__ == '__main__':
    main()