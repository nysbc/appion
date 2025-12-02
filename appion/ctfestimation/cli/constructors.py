def constructCtfFind4JobMetadata(args : dict):
    from ...base.cli import constructJobMetadata
    progname="ctfestimate"
    jobmetadata=constructJobMetadata(args, progname)
    return jobmetadata