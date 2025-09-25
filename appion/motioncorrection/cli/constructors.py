
def constructMotionCor2JobMetadata(args : dict):
    from ...base.retrieve import readSessionData
    from ...base.cli import constructJobMetadata
    from ..store import saveDDStackRunData
    progname="makeddalignmotioncor2_ucsf"
    jobmetadata=constructJobMetadata(args, progname)
    sessionmetadata=readSessionData(args["sessionname"])
    jobmetadata['ref_apddstackrundata_ddstackrun']=saveDDStackRunData(args['preset'], args['align'], args['bin'], args['runname'], args['rundir'], sessionmetadata["session_id"])
    return jobmetadata


