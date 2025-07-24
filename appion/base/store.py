import sinedon.base as sb
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
from fcntl import flock, LOCK_EX, LOCK_UN

def saveScriptProgramName():
    progname = sb.set("ScriptProgramName", {"name": sys.argv[0]})
    return progname["def_id"]

def saveScriptUsername():
    getpwuid=pwd.getpwuid(os.getuid())
    username = sb.set("ScriptUserName", dict(name=getpwuid[0],
                            uid = getpwuid[2],
                            gid = getpwuid[3],
                            fullname = getpwuid[4]))
    return username["def_id"]

def saveScriptHostName():
    cpu_info = get_cpu_info()
    hostname = sb.set("ScriptHostName", dict(name = platform.node(),
							  ip = socket.gethostbyaddr(platform.node())[2][0], # Not really accurate/useful since a host can have multiple IPs and we don't know which one we care about here.
							  system = os.uname()[0].lower(),
							  distro = distro.name(pretty=True),
							  nproc = cpu_info["count"],
							  memory = int(psutil.virtual_memory().total/1024),
							  cpu_vendor = cpu_info["vendor_id_raw"],
							  gpu_vendor = None , # TODO But we don't really care about this as much.
							  arch = platform.machine()
							  ))
    return hostname["def_id"]

def saveScriptProgramRun(runname, ref_scriptprogramname_progname, ref_scriptusername_username, ref_scripthostname_hostname, ref_appathdata_rundir, ref_apappionjobdata_job, ref_appathdata_appion_path):
    getpwuid=pwd.getpwuid(os.getuid())
    progrun = sb.set("ScriptProgramRun", dict(runname=runname,
							   revision=importlib.metadata.version('appion'),
							   ref_scriptprogramname_progname=ref_scriptprogramname_progname,
							   ref_scriptusername_username=ref_scriptusername_username,
							   ref_scripthostname_hostname=ref_scripthostname_hostname,
							   ref_appathdata_rundir=ref_appathdata_rundir,
							   ref_apappionjobdata_job=ref_apappionjobdata_job,
							   ref_appathdata_appion_path=ref_appathdata_appion_path,
							   unixshell=getpwuid[6]
							   ))
    return progrun["def_id"]

# Run parse_args() to get a namespace object and then transfrom that into a dict with vars()
def saveScriptParams(args : dict, ref_scriptprogramname_progname, ref_scriptprogramrun_progrun):
    for paramname in args.keys():
        scriptparamname = sb.set("ScriptParamName", dict(name=paramname,
									ref_scriptprogramname_progname=ref_scriptprogramname_progname))
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
            paramvalue = sb.set("ScriptParamValue", dict(value=str(args[paramname]),
                                        usage = usage,
                                        ref_scriptparamname_paramname=scriptparamname["def_id"],
                                        ref_scriptprogramrun_progrun=ref_scriptprogramrun_progrun
            ))

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
        assessrun = sb.set("ApAssessmentRunData",dict(ref_sessiondata_session=ref_sessiondata_session,
                                        name = "run1"))
        return assessrun["def_id"]
    return None

# ApAppionJobData

def updateApAppionJobData(jobid, data):
    appionjob = sb.get("ApAppionJobData", {"def_id" : jobid})
    for k, v in data.items():
        if k in appionjob.keys() and data[k] is not None:
            appionjob[k] = v
    sb.update("ApAppionJobData",appionjob)
    return appionjob["def_id"]

def saveApAppionJobData(ref_appathdata_path, jobtype, runname, user, hostname, ref_sessiondata_session):
    #=====================
    appionjob = sb.get("ApAppionJobData",dict(ref_appathdata_path = ref_appathdata_path,
                                        jobtype = jobtype))
    if not appionjob:
        ### insert a cluster job
        appionjob = sb.set("ApAppionJobData", dict(name = runname+".appionsub.job",
                                ref_appathdata_clusterpath = ref_appathdata_path,
                                user = user,
                                cluster = hostname,
                                status = "R",
                                ref_sessiondata_session = ref_sessiondata_session,
                                jobtype=jobtype))
    return appionjob["def_id"]

# ApPathData
def savePathData(path):
    appath = sb.set("ApPathData", {"path" : path})
    return appath["def_id"]

# This isn't necessary for ctffind or motioncor2, since images that have been processed are 
# recorded in the Appion database, but it might be useful in the future for applications that don't
# have this info stored in the database.
def saveCheckpoint(image_id, checkpoint_path):
    if not os.path.exists(checkpoint_path):
        with open(checkpoint_path,"w") as f:
            flock(f, LOCK_EX)
            completed=[]
            json.dump(completed, f)
            flock(f, LOCK_UN)
    with open(checkpoint_path, "r+") as f:
        flock(f, LOCK_EX)
        completed=json.load(f)
        completed.append(image_id)
        f.seek(0)
        f.truncate()
        json.dump(completed, f)
        f.flush()
        flock(f, LOCK_EX)