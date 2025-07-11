import argparse
import os, sys, pwd, platform

def constructGlobalParser():
    """
    Function that adds universal Appion options to an ArgumentParser object.
    """
    parser = argparse.ArgumentParser(add_help=False)

    ### Input value options
    parser.add_argument("-R", "--rundir", "--outdir", dest="rundir",
        help="Run path for storing output, e.g. --rundir=/data/appion/runs/run1", default=os.getcwd())
    parser.add_argument("-s", "--session", dest="sessionname",
        help="Session name associated with processing run, e.g. --session=06mar12a")
    parser.add_argument("--preset", dest="preset",
        help="Image preset associated with processing run, e.g. --preset=en")
    parser.add_argument("--clusterconfig", dest="clusterconfig",
        help="Path to a YAML file that contains Dask cluster configuration info.", type=str, default="/etc/dask/cluster.yml")

    #parser.add_argument("--reprocess", dest="reprocess", type=float,
    #	help="Only process images that pass this reprocess criteria")

    tiltoptions = ("notilt", "hightilt", "lowtilt", "minustilt", "plustilt", "all")
    parser.add_argument("--tiltangle", dest="tiltangle", 
        default="all", choices=tiltoptions,
        help="Only process images with specific tilt angles, options: "+str(tiltoptions))

    ### True / False options
    parser.add_argument("--continue", dest="continue", default=True,
        action="store_true", help="Continue processing run from last image")
    #parser.add_argument("--no-continue", dest="continue", default=True,
    #	action="store_false", help="Do not continue processing run from last image")
    parser.add_argument("--no-wait", dest="wait", default=True,
        action="store_false", help="Do not wait for more images after completing loop")
    parser.add_argument("--no-rejects", dest="rejects", default=False,
        action="store_false", help="Do not process hidden or rejected images")
    parser.add_argument("--reverse", dest="reverse", default=False,
        action="store_true", help="Process the images from newest to oldest")
    parser.add_argument("--parallel", dest="parallel", default=False,
        action="store_true", help="parallel appionLoop on different cpu. Only work with the part not using gpu")
    
    parser.add_argument("-n", "--runname", dest="runname",
        help="Name for processing run, e.g. --runname=run1")
    parser.add_argument("-d", "--description", dest="description",
        help="Description of the processing run (must be in quotes)")
    parser.add_argument("-p", "--projectid", dest="projectid", type=int,
        help="Project id associated with processing run, e.g. --projectid=159")
    parser.add_argument("-C", "--commit", dest="commit", default=True,
        action="store_true", help="Commit processing run to database")
    parser.add_argument("--no-commit", dest="commit", default=True,
        action="store_false", help="Do not commit processing run to database")

    parser.add_argument("--expid", "--expId", dest="expid", type=int,
        help="Session id associated with processing run, e.g. --expid=7159")
    parser.add_argument("--nproc", dest="nproc", type=int,
        help="Number of processor to use")
    # jobtype is a dummy option for now so that it is possible to use the same command line that
    # is fed to runJob.py to direct command line running.  Do not use the resulting param.
    parser.add_argument("--jobtype", dest="jobtype",
        help="Job Type of processing run, e.g., partalign", type=str)
    parser.add_argument("--clean", dest="clean",
        help="Clean up intermediate results during the course of processing.", default=True, 
        action="store_true")
    parser.add_argument("--no-clean", dest="clean",
        help="Don't clean up intermediate results during the course of processing.", default=True, 
        action="store_false")
    return parser

def constructJobMetadata(args : dict, progname: str):
    from .store import saveScriptProgramName, saveScriptUsername, saveScriptHostName, savePathData, saveApAppionJobData, saveScriptProgramRun, saveScriptParams
    from .retrieve import readSessionData
    sessionmetadata=readSessionData(args['sessionname'])
    jobmetadata={}
    jobmetadata['ref_scriptprogramname_progname']=saveScriptProgramName()
    jobmetadata['ref_scriptusername_username']=saveScriptUsername()
    jobmetadata['ref_scripthostname_hostname']=saveScriptHostName()
    jobmetadata['ref_appathdata_appion_path']=savePathData(os.path.abspath(sys.argv[0]))
    jobmetadata['ref_appathdata_rundir']=savePathData(args['rundir'])
    jobmetadata['ref_apappionjobdata_job']=saveApAppionJobData(jobmetadata['ref_appathdata_rundir'], progname, args['runname'], pwd.getpwuid(os.getuid())[0], platform.node(), sessionmetadata['session_id'])
    jobmetadata['ref_scriptprogramrun_progrun']=saveScriptProgramRun(args['runname'], jobmetadata['ref_scriptprogramname_progname'], jobmetadata['ref_scriptusername_username'], jobmetadata['ref_scripthostname_hostname'], jobmetadata['ref_appathdata_appion_path'], jobmetadata['ref_appathdata_rundir'], jobmetadata['ref_apappionjobdata_job'])
    saveScriptParams(args, jobmetadata['ref_scriptprogramname_progname'], jobmetadata['ref_scriptprogramrun_progrun'])
    return jobmetadata