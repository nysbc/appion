from sinedon.models.appion import ScriptProgramName
from sinedon.models.appion import ScriptUserName
from sinedon.models.appion import ScriptHostName
from sinedon.models.appion import ScriptProgramRun
from sinedon.models.appion import ScriptParamName
from sinedon.models.appion import ScriptParamValue
import platform
import importlib.metadata
import os, pwd
from cpuinfo import get_cpu_info
import socket
import distro
import psutil


def uploadScriptProgramName(name):
    progname = ScriptProgramName(name=name)
    progname.save()

def uploadScriptUsername(name):
    getpwnam=pwd.getpwnam(name)
    username = ScriptUserName(name=name,
                            uid = getpwnam[2],
                            gid = getpwnam[3],
                            fullname = getpwnam[4],
                            unixshell = getpwnam[6])
    username.save()

def uploadScriptHostName():
    cpu_info = get_cpu_info()
    hostname = ScriptHostName(name = platform.node(),
							  ip = socket.gethostbyaddr(platform.node())[2][0],
							  system = os.uname()[0].lower(),
							  distro = distro.name(pretty=True),
							  nproc = cpu_info["count"],
							  memory = psutil.virtual_memory().total,
							  cpu_vendor = cpu_info["vendor_id_raw"],
							  gpu_vendor = None , # TODO
							  arch = platform.machine()
							  )
    hostname.save()

def uploadScriptProgramRun():
    progrunq = appiondata.ScriptProgramRun()
    progrunq['runname'] = self.params['runname']
    progrunq['progname'] = prognameq
    progrunq['username'] = userq
    progrunq['hostname'] = hostq
    progrunq['unixshell'] = unixshell
    progrunq['rundir'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
    progrunq['job'] = self.getClusterJobData()
    appiondir = apParam.getAppionDirectory()
    ### get appion version/subversion revision
    progrunq['revision'] = importlib.metadata.version('appion')
    progrunq['appion_path'] = appiondata.ApPathData(path=os.path.abspath(appiondir))

def uploadScriptParamName():
    for paramname in self.params.keys():
        paramnameq = appiondata.ScriptParamName()
        paramnameq['name'] = paramname
        paramnameq['progname'] = prognameq

        paramvalueq = appiondata.ScriptParamValue()
        paramvalueq['value'] = str(self.params[paramname])
        usage = self.usageFromParamDest(paramname, self.params[paramname])
        #print "usage: ", usage
        paramvalueq['usage'] = usage
        paramvalueq['paramname'] = paramnameq
        paramvalueq['progrun'] = progrunq
        if usage is not None:
            paramvalueq.insert()
				
# ApAssessmentRunData

def insertImgAssessmentStatus(imgdata, runname="run1", assessment=None, msg=True):
	"""
	Insert the assessment status
		keep = True
		reject = False
		unassessed = None
	"""
	if assessment is True or assessment is False:
		assessrun = appiondata.ApAssessmentRunData()
		assessrun['session'] = imgdata['session']
		#override to ALWAYS be 'run1'
		#assessrun['name'] = runname
		assessrun['name'] = "run1"

		assessquery = appiondata.ApAssessmentData()
		assessquery['image'] = imgdata
		assessquery['assessmentrun'] = assessrun
		assessquery['selectionkeep'] = assessment
		assessquery.insert()
	else:
		apDisplay.printWarning("No image assessment made, invalid data: "+str(assessment))


	#check assessment
	if msg is True:
		finalassess = getImgAssessmentStatus(imgdata)
		imgname = apDisplay.short(imgdata['filename'])
		if finalassess is True:
			astr = apDisplay.colorString("keep", "green")
		elif finalassess is False:
			astr = apDisplay.colorString("reject", "red")
		elif finalassess is None:
			astr = apDisplay.colorString("none", "yellow")
		apDisplay.printMsg("Final image assessment: "+astr+" ("+imgname+")")

	return True

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