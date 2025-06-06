# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center
from sinedon.models.appion import ApDDAlignImagePairData
from sinedon.models.appion import ApDDStackRunData
from sinedon.models.appion import ApPathData

# preset is implicitly encoded in the path; each run should only be for one (and only one) preset.
def retrieveDoneImages(rundir, session_id):
    appathdata=ApPathData.objects.filter(path=rundir)
    runs=[]
    for path in appathdata:
        path_runs=ApDDStackRunData.objects.filter(ref_appathdata_path=path.def_id, ref_sessiondata_session=session_id)
        runs+=[run.def_id for run in path_runs]
    runs=set(runs)
    imageIds=set()
    for run in runs:
        runImageIds=ApDDAlignImagePairData.objects.filter(ref_apddstackrundata_ddstackrun=run)
        imageIds=imageIds | set([imageid.ref_acquisitionimagedata_source for imageid in runImageIds])
    return imageIds

