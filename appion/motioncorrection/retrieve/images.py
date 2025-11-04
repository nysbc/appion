# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center
import sinedon.base as sb

# preset is implicitly encoded in the path; each run should only be for one (and only one) preset.
def retrieveDoneImages(rundir, session_id):
    appathdata=sb.filter("ApPathData",{"path" : rundir})
    runs=[]
    for path in appathdata:
        path_runs=sb.filter("ApDDStackRunData", {"ref_appathdata_path":path["def_id"], "ref_sessiondata_session":session_id})
        runs+=[run["def_id"] for run in path_runs]
    runs=set(runs)
    imageIds=set()
    for run in runs:
        try:
            runImageIds=sb.filter("ApDDAlignImagePairData", {"ref_apddstackrundata_ddstackrun" :run})
            imageIds=imageIds | set([imageid["ref_acquisitionimagedata_source"] for imageid in runImageIds])
        except:
            continue
    #TODO double-check to make sure that both aligned and dose-weighted aligned are in ApDDAlignImagePairData
    return imageIds


