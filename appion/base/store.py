from sinedon.models.appion import ScriptProgramName
from sinedon.models.appion import ScriptUserName
from sinedon.models.appion import ScriptHostName
from sinedon.models.appion import ScriptProgramRun
from sinedon.models.appion import ScriptParamName
from sinedon.models.appion import ScriptParamValue
from sinedon.models.appion import ApAssessmentRunData
from sinedon.models.appion import ApAppionJobData
from sinedon.models.projects import processingdb
import platform
import importlib.metadata
import os, pwd
from cpuinfo import get_cpu_info
import socket
import distro
import psutil
from argparse import ArgumentParser
import json
from dask.distributed import Lock


def saveScriptProgramName(name):
    progname = ScriptProgramName(name=name)
    progname.save()

def saveScriptUsername():
    getpwuid=pwd.getpwuid(os.getuid())
    username = ScriptUserName(name=getpwuid[0],
                            uid = getpwuid[2],
                            gid = getpwuid[3],
                            fullname = getpwuid[4],
                            unixshell = getpwuid[6])
    username.save()

def saveScriptHostName():
    cpu_info = get_cpu_info()
    hostname = ScriptHostName(name = platform.node(),
							  ip = socket.gethostbyaddr(platform.node())[2][0], # Not really accurate/useful since a host can have multiple IPs and we don't know which one we care about here.
							  system = os.uname()[0].lower(),
							  distro = distro.name(pretty=True),
							  nproc = cpu_info["count"],
							  memory = psutil.virtual_memory().total,
							  cpu_vendor = cpu_info["vendor_id_raw"],
							  gpu_vendor = None , # TODO
							  arch = platform.machine()
							  )
    hostname.save()

def saveScriptProgramRun(runname, ref_scriptprogramname_progname, ref_scriptusername_username, ref_scripthostname_hostname, ref_appathdata_rundir, ref_apappionjobdata_job, ref_appathdata_appion_path):
    getpwuid=pwd.getpwuid(os.getuid())
    progrun = ScriptProgramRun(runname=runname,
							   revision=importlib.metadata.version('appion'),
							   ref_scriptprogramname_progname=ref_scriptprogramname_progname,
							   ref_scriptusername_username=ref_scriptusername_username,
							   ref_scripthostname_hostname=ref_scripthostname_hostname,
							   ref_appathdata_rundir=ref_appathdata_rundir,
							   ref_apappionjobdata_job=ref_apappionjobdata_job,
							   ref_appathdata_appion_path=ref_appathdata_appion_path,
							   unixshell=getpwuid[6]
							   )
    progrun.save()

# Run parse_args() to get a namespace object and then transfrom that into a dict with vars()
def saveScriptParams(args : dict, ref_scriptprogramname_progname, ref_scriptprogramrun_progrun, parser : ArgumentParser):
    for paramname in args.keys():
        paramname = ScriptParamName(name=paramname,
									ref_scriptprogramname_progname=ref_scriptprogramname_progname)
        paramname.save()
        usage=calcUsageFromParamDest(args, parser, paramname, args[paramname])
        if usage:
            paramvalue = ScriptParamValue(value=str(args[paramname]),
                                        usage = usage,
                                        paramname=paramname.def_id,
                                        ref_scriptprogramrun_progrun=ref_scriptprogramrun_progrun
            )
            paramvalue.save()
			
def calcUsageFromParamDest(args, parser, dest, value):
    """
    For a given optparse destination (dest, e.g., 'commit')
        and value (e.g., 'False') this will generate the command line
        usage (e.g., '--no-commit')
    """
    usage = None
    if value is None:
        return None
    if len(args) == 0:
        for opt in parser.option_list:
            arg = str(opt.get_opt_string.im_self)
            if '/' in arg:
                args = arg.split('/')
                arg = args[-1:][0]
                args[opt.dest] = arg
                args[opt.dest] = opt
        if dest in args:
            argument=args[dest]
        else:
            return usage
    if not dest in args:
        return usage
    optaction = args[dest].action
    if optaction == 'store':
        value = str(value)
        if not ' ' in value:
            usage = argument+"="+value
        else:
            usage = argument+"='"+value+"'"
    elif optaction == 'store_true' or optaction == 'store_false':
        storage = 'store_'+str(value).lower()
        for opt in parser.option_list:
            if opt.dest == dest and opt.action == storage:
                arg = str(opt.get_opt_string.im_self)
                if '/' in arg:
                    arglist = arg.split('/')
                    arg = arglist[-1:][0]
                    usage = arg
    return usage

# ApAssessmentRunData

def saveApAssessmentRunData(ref_sessiondata_session, assessment="unassessed"):
    """
    Insert the assessment status
        keep = True
        reject = False
        unassessed = None
    """
    if assessment != "unassessed":
        # Run name is always run1.  Not sure what the rationale for this is.
        assessrun = ApAssessmentRunData(ref_sessiondata_session=ref_sessiondata_session,
                                        name = "run1")
        assessrun.save()

# ApAppionJobData

# Appion database is initialized by myamiweb / web viewer.
def readAppionDatabaseName(projectid):
    project = processingdb.objects.get(ref_projects_project=projectid)
    return project.appiondb

def updateApAppionJobData(jobid, status):
    appionjob = ApAppionJobData.objects.get(def_id=jobid)
    appionjob.status = status
    appionjob.save()

def saveApAppionJobData(ref_appathdata_path, jobtype, runname, user, hostname, ref_sessiondata_session):
    #=====================
    clust = ApAppionJobData.objects.get(ref_appathdata_path = ref_appathdata_path,
                                        jobtype = jobtype)
    if not clust:
        ### insert a cluster job
        clust = ApAppionJobData(name = runname+".appionsub.job",
                                ref_appathdata_clusterpath = ref_appathdata_path,
                                user = user,
                                cluster = hostname,
                                status = "R",
                                ref_sessiondata_session = ref_sessiondata_session,
                                jobtype=jobtype)
        clust.save()

# Handle locking using Dask distributed lock
def saveCheckpoint(image_id, checkpoint_path):
    lock = Lock("checkpoint")
    lock.acquire(timeout=10)
    if not os.path.exists(checkpoint_path):
        with open(checkpoint_path,"w") as f:
            completed=[]
            json.dump(completed, f)
    with open(checkpoint_path, "r+") as f:
        completed=json.load(f)
        completed.append(image_id)
        f.seek(0)
        f.truncate()
        json.dump(completed, f)
        f.flush()
    lock.release()