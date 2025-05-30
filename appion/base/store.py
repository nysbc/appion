from sinedon.models.appion import ScriptProgramName
from sinedon.models.appion import ScriptUserName
from sinedon.models.appion import ScriptHostName
from sinedon.models.appion import ScriptProgramRun
from sinedon.models.appion import ScriptParamName
from sinedon.models.appion import ScriptParamValue
from sinedon.models.appion import ApAssessmentRunData
from sinedon.models.appion import ApAppionJobData
from sinedon.models.appion import ApPathData
import sys
import platform
import importlib.metadata
import os, pwd
from cpuinfo import get_cpu_info
import socket
import distro
import psutil
import argunparse
import json
from dask.distributed import Lock

def saveScriptProgramName():
    progname = ScriptProgramName(name=sys.argv[0])
    progname.save()
    return progname.def_id

def saveScriptUsername():
    getpwuid=pwd.getpwuid(os.getuid())
    username = ScriptUserName(name=getpwuid[0],
                            uid = getpwuid[2],
                            gid = getpwuid[3],
                            fullname = getpwuid[4],
                            unixshell = getpwuid[6])
    username.save()
    return username.def_id

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
    return hostname.def_id

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
    return progrun.def_id

# Run parse_args() to get a namespace object and then transfrom that into a dict with vars()
def saveScriptParams(args : dict, ref_scriptprogramname_progname, ref_scriptprogramrun_progrun):
    for paramname in args.keys():
        paramname = ScriptParamName(name=paramname,
									ref_scriptprogramname_progname=ref_scriptprogramname_progname)
        paramname.save()
        usage=None
        if isinstance(args[paramname], bool):
            if args[paramname] is True:
                usage="--%s" % paramname
            else:
                usage="--no-%s" % paramname
        else:
            tmp={paramname : args[paramname]}
            unparser = argunparse.ArgumentUnparser()
            usage=unparser.unparse(**tmp)
            del tmp
        if usage:
            paramvalue = ScriptParamValue(value=str(args[paramname]),
                                        usage = usage,
                                        paramname=paramname.def_id,
                                        ref_scriptprogramrun_progrun=ref_scriptprogramrun_progrun
            )
            paramvalue.save()

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
        return assessrun.def_id
    return None

# ApAppionJobData

def updateApAppionJobData(jobid, status):
    appionjob = ApAppionJobData.objects.get(def_id=jobid)
    appionjob.status = status
    appionjob.save()
    return appionjob.def_id

def saveApAppionJobData(ref_appathdata_path, jobtype, runname, user, hostname, ref_sessiondata_session):
    #=====================
    appionjob = ApAppionJobData.objects.get(ref_appathdata_path = ref_appathdata_path,
                                        jobtype = jobtype)
    if not appionjob:
        ### insert a cluster job
        appionjob = ApAppionJobData(name = runname+".appionsub.job",
                                ref_appathdata_clusterpath = ref_appathdata_path,
                                user = user,
                                cluster = hostname,
                                status = "R",
                                ref_sessiondata_session = ref_sessiondata_session,
                                jobtype=jobtype)
        appionjob.save()
    return appionjob.def_id

# ApPathData
def savePathData(path):
	appath = ApPathData.objects.get(path=path)
	if not appath:
		appath = ApPathData(path=path)
		appath.save()
	return appath.def_id

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