from sinedon.models.appion import ScriptProgramName
from sinedon.models.appion import ScriptUserName
from sinedon.models.appion import ScriptHostName
from sinedon.models.appion import ScriptProgramRun
from sinedon.models.appion import ScriptParamName
from sinedon.models.appion import ScriptParamValue
from sinedon.models.appion import ApAssessmentRunData
import platform
import importlib.metadata
import os, pwd
from cpuinfo import get_cpu_info
import socket
import distro
import psutil
from argparse import ArgumentParser


def uploadScriptProgramName(name):
    progname = ScriptProgramName(name=name)
    progname.save()

def uploadScriptUsername():
    getpwuid=pwd.getpwuid(os.getuid())
    username = ScriptUserName(name=getpwuid[0],
                            uid = getpwuid[2],
                            gid = getpwuid[3],
                            fullname = getpwuid[4],
                            unixshell = getpwuid[6])
    username.save()

def uploadScriptHostName():
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

def uploadScriptProgramRun(runname, ref_scriptprogramname_progname, ref_scriptusername_username, ref_scripthostname_hostname, ref_appathdata_rundir, ref_apappionjobdata_job, ref_appathdata_appion_path):
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
def uploadScriptParams(args : dict, ref_scriptprogramname_progname, ref_scriptprogramrun_progrun, parser : ArgumentParser):
    for paramname in args.keys():
        paramname = ScriptParamName(name=paramname,
									ref_scriptprogramname_progname=ref_scriptprogramname_progname)
        paramname.save()
        usage=usageFromParamDest(args, parser, paramname, args[paramname])
        if usage:
            paramvalue = ScriptParamValue(value=str(args[paramname]),
                                        usage = usage,
                                        paramname=paramname.def_id,
                                        ref_scriptprogramrun_progrun=ref_scriptprogramrun_progrun
            )
            paramvalue.save()
			
def usageFromParamDest(args, parser, dest, value):
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

def uploadApAssessmentRunData(ref_sessiondata_session, assessment="unassessed"):
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

if __name__ == "__main__":
	# parse options
	projectid = None
	if len(sys.argv) < 3:
		print "Usage: %s jobid status [projectid]" % (sys.argv[0],)
		sys.exit()

	jobid = sys.argv[1]
	status = sys.argv[2]

	if len(sys.argv) > 3:
		projectid = sys.argv[3]

	# set new db
	if projectid is not None:
		pjc = sinedon.getConfig('projectdata')
		q = "SELECT appiondb FROM processingdb WHERE `REF|projects|project`='%s'" % (projectid,)
		dbc = sinedon.sqldb.connect(**pjc)
		cursor = dbc.cursor()
		result = cursor.execute(q)
		if result:
			newdbname, = cursor.fetchone()
			sinedon.setConfig('appiondata', db=newdbname)
		cursor.close()
		dbc.close()

	# connect to database
	c = sinedon.getConfig('appiondata')

	dbc = sinedon.sqldb.connect(**c)
	cursor = dbc.cursor()

	# execute update
	q = "UPDATE ApAppionJobData SET `status` = '%s' WHERE `DEF_id` = '%s'" %(status,jobid)
	cursor.execute(q)

	# close
	cursor.close()
	dbc.close()

	#=====================
	def getClusterJobData(self):
		if self.clusterjobdata is not None:
			return self.clusterjobdata
		if not 'commit' in self.params or self.params['commit'] is False:
			return None
		pathq = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		clustq = appiondata.ApAppionJobData()
		clustq['path'] = pathq
		clustq['jobtype'] = self.functionname.lower()
		clustdatas = clustq.query()
		if not clustdatas:
			### insert a cluster job
			clustq['name'] = self.params['runname']+".appionsub.job"
			clustq['clusterpath'] = pathq
			clustq['user'] = apParam.getUsername()
			clustq['cluster'] = apParam.getHostname()
			clustq['status'] = "R"
			clustq['session'] = self.getSessionData()
			### need a proper way to create a jobtype
			clustq['jobtype']=self.params['jobtype']
			if not clustq['jobtype']:
				clustq['jobtype'] = self.functionname.lower()
			clustq.insert()
			self.clusterjobdata = clustq
			return clustq
		elif len(clustdatas) == 1:
			### we have an entry
			### we need to say that we are running
			apWebScript.setJobToRun(clustdatas[0].dbid)
			self.clusterjobdata = clustdatas[0]
			return clustdatas[0]
		else:
			### special case: more than one job with given path
			apDisplay.printWarning("More than one cluster job has this path")
			self.clusterjobdata = clustdatas[0]
			return clustdatas[0]