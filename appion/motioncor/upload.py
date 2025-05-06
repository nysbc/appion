import os
import numpy
import math
from sinedon.models.appion import ApDDAlignImagePairData
from sinedon.models.appion import ApDDFrameTrajectoryData
from sinedon.models.appion import ApDDAlignStatsData
from sinedon.models.leginon import AcquisitionImageData
from sinedon.models.leginon import ObjIceThicknessData
from sinedon.models.leginon import ZeroLossIceThicknessData

# ApDDAlignImagePairData
# We can only really add insert ref IDs here b/c the raw and aligned images are in a different database from the Appion results.
# If it weren't for this, we'd probably pass objects directly.
def uploadAlignedImage(raw_image_def_id, aligned_image_def_id, rundata_def_id, logData, kwargs):
    commitImagePairData(raw_image_def_id, aligned_image_def_id, rundata_def_id)
    aligned_image=AcquisitionImageData.objects.get(def_id=aligned_image_def_id)
    nframes=aligned_image.ref_cameraemdata_camera.nframes
    commitAlignStats(aligned_image_def_id, rundata_def_id, logData["shifts"], nframes, kwargs["PixSize"])
    transferALSThickness(raw_image_def_id,aligned_image_def_id)
    transferZLPThickness(raw_image_def_id,aligned_image_def_id)

def commitImagePairData(raw_image_def_id, aligned_image_def_id, rundata_def_id):
    pairdata = ApDDAlignImagePairData(ref_acquisitionimagedata_source=raw_image_def_id,
                                    ref_acquisitionimagedata_result=aligned_image_def_id,
                                    ref_apddstackrundata_ddstackrun=rundata_def_id)
    pairdata.save()

# Pass in shifts from dict returned by parseLog
def commitAlignStats(aligned_image_def_id, rundata_def_id, shifts, nframes, pixsize):
    # Issue #6155 need new query to get timestamp
	# JP: Where does a timestamp come in to play?
    #aligned_imgdata = AcquisitionImageData.objects.get(def_id=aligned_image_def_id)
    xy={}
    xy['x']=[shift[0] for shift in shifts]
    xy['y']=[shift[1] for shift in shifts]
    trajdata_def_id = saveFrameTrajectory(aligned_image_def_id, rundata_def_id, xy)
    saveAlignStats(aligned_image_def_id, rundata_def_id, shifts, nframes, pixsize, trajdata=trajdata_def_id)
			
def transferALSThickness(unaligned,aligned):
# transfers aperture limited scattering measurements and parameters from the unaligned image to the aligned image
# should it be here or in a different place???
    obthdata = ObjIceThicknessData.objects.get(ref_acquisitionimagedata_image=unaligned)
    if obthdata:
        results = obthdata[0]
        newobjth = ObjIceThicknessData(vacuum_intensity = results.vacuum_intensity,
                                       mfp = results.mfp,
                                       intensity = results.intensity,
                                       thickness = results.thickness,
                                       ref_acquisitionimagedata_image = aligned)
        newobjth.save()
		

def transferZLPThickness(unaligned,aligned):
    # transfers zero loss peak measurements and parameters from the unaligned image to the aligned image
    # should it be here or in a different place???
    zlpthdata = ZeroLossIceThicknessData.objects.get(ref_acquisitionimagedata_image=unaligned)
    if zlpthdata:
        results = zlpthdata[0]
        newzlossth = ZeroLossIceThicknessData(no_slit_mean = results.no_slit_mean,
											  no_slit_sd = results.no_slit_sd,
											  slit_mean = results.slit_mean,
											  slit_sd = results.slit_sd,
											  thickness = results.thickness,
											  ref_acquisitionimagedata_image = aligned
        )
        newzlossth.save()

# ApDDAlignStatsData	
def saveAlignStats(aligned_image_def_id, rundata_def_id, positions, nframes, pixsize, trajdata=None):
    '''
    save appiondata ApDDAlignStatsData
    '''
    max_drifts, median = getFrameStats(positions, nframes)
    drifts={}
    for i, drift_tuple in enumerate(max_drifts):
        key = 'top_shift%d' % (i+1,)
        drifts[key+'_index'] = drift_tuple[1]
        drifts[key+'_value'] = drift_tuple[0]
    alignstatsdata = ApDDAlignStatsData(image=aligned_image_def_id, 
										apix=pixsize,
                                        ddstackrun=rundata_def_id,
                                        median_shift_value=median,
                                        trajectory=trajdata,
                                        **drifts)
    alignstatsdata.save()

def getFrameStats(positions, nframes):
    '''
    get alignment frame stats for faster graphing.
    '''
    pixel_shifts = calculateFrameShiftFromPositions(positions, nframes - len(positions)+1)
    if not pixel_shifts:
        raise ValueError('no pixel shift found for calculating stats')
    if len(pixel_shifts) < 3:
        raise ValueError('Not enough pixel shifts found for stats calculation')
    pixel_shifts_sort = list(pixel_shifts)
    pixel_shifts_sort.sort()
    median = numpy.median(numpy.array(pixel_shifts_sort))
    max1 = pixel_shifts_sort[-1]
    max2 = pixel_shifts_sort[-2]
    max3 = pixel_shifts_sort[-3]
    m1index = pixel_shifts.index(max1)
    m2index = pixel_shifts.index(max2)
    m3index = pixel_shifts.index(max3)
    return [(max1,m1index),(max2,m2index),(max3,m3index)], median

def calculateFrameShiftFromPositions(positions,running=1):
	# place holder for running first frame shift duplication
	offset = int((running-1)/2)
	shifts = offset*[None,]
	for p in range(len(positions)-1):
		shift = math.hypot(positions[p][0]-positions[p+1][0],positions[p][1]-positions[p+1][1])
		shifts.append(shift)
	# duplicate first and last shift for the end points if running
	for i in range(offset):
		shifts.append(shifts[-1])
		shifts[i] = shifts[offset]
	return shifts
	
# ApDDFrameTrajectoryData

def saveFrameTrajectory(image_def_id, rundata_def_id, xy, limit=20, reference_index=None, particle=None):
    '''
    Save appiondata ApDDFrameTrajectoryData
    '''
    n_positions = len(xy['x'])
    limit = min([n_positions,limit])
    if limit < 2:
        raise ValueError('Not enough frames to save trajectory')
    if reference_index == None:
        reference_index = n_positions // 2
    trajdata = ApDDFrameTrajectoryData(ref_acquisitionimagedata_image=image_def_id,
									ref_apstackparticledata_particle=particle,
									ref_apddstackrundata_ddstackrun=rundata_def_id,
                                    seq_pos_x=str(list(xy['x'][:limit])), #position relative to reference
                                    seq_pos_x=str(list(xy['y'][:limit])), #position relative to reference
                                    last_x=xy['x'][-1],
                                    last_y=xy['y'][-1],
                                    number_of_positions= n_positions,
                                    reference_index= reference_index)
    trajdata.save()
    return trajdata.def_id

#ApDDStackParamsData
def insertFunctionRun(stackid, preset, align, bin, runname, rundir):
    if stackid:
        stackdata = appiondata.ApStackData.direct_query(stackid)
    else:
        stackdata = None
    qparams = appiondata.ApDDStackParamsData(preset=preset,align=align,bin=bin,stack=stackdata)
    qpath = appiondata.ApPathData(path=os.path.abspath(rundir))
    sessiondata = getSessionData()
    q = appiondata.ApDDStackRunData(runname=runname,params=qparams,session=sessiondata,path=qpath)
    results = q.query()
    if not results:
        q.save()
		
def getSessionData(self):
    sessiondata = None
    if self.params.get('sessionname') is not None:
        sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
    if sessiondata is None and self.params.get('expid') is not None:
        sessiondata = apDatabase.getSessionDataFromSessionId(self.params['expid'])
    if sessiondata is None and self.params.get('stackid') is not None:
        from appionlib import apStack
        sessiondata = apStack.getSessionDataFromStackId(self.params['stackid'])
    if sessiondata is None and self.params.get('reconid') is not None:
        from appionlib import apStack
        self.params['stackid'] = apStack.getStackIdFromRecon(self.params['reconid'], msg=False)
        sessiondata = apStack.getSessionDataFromStackId(self.params['stackid'])
    if sessiondata is None:
        ### works with only canonical session names
        s = re.search('/([0-9][0-9][a-z][a-z][a-z][0-9][0-9][^/]*)/', self.params['rundir'])
        if s:
            self.params['sessionname'] = s.groups()[0]
            sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
    self.sessiondata=sessiondata
    return sessiondata
			
# ApDDStackRunData
# TODO
		
# ApPathData

def commitSubStack(params, newname=False, centered=False, oldstackparts=None, sorted=False, radial_averaged=False, included=None):
	"""
	commit a substack to database

	required params:
		stackid
		description
		commit
		rundir
		keepfile
	'included' param is a list of included particles, starting at 0
	"""

	t0 = time.time()
	oldstackdata = getOnlyStackData(params['stackid'], msg=False)
	apDisplay.printColor("got old stackdata in "+apDisplay.timeString(time.time()-t0),"cyan")

	t0 = time.time()
	#create new stack data
	stackq = appiondata.ApStackData()
	stackq['path'] = appiondata.ApPathData(path=os.path.abspath(params['rundir']))
	stackq['name'] = oldstackdata['name']

	# use new stack name if provided
	if newname:
		stackq['name'] = newname

	stackdata=stackq.query(results=1)

	if stackdata:
		apDisplay.printWarning("A stack with these parameters already exists")
		return
	stackq['oldstack'] = oldstackdata
	stackq['hidden'] = False
	stackq['substackname'] = params['runname']
	stackq['description'] = params['description']
	stackq['pixelsize'] = oldstackdata['pixelsize']
	stackq['boxsize'] = oldstackdata['boxsize']
	if 'correctbeamtilt' in params.keys():
		stackq['beamtilt_corrected'] = params['correctbeamtilt']
	if sorted is True:
		stackq['junksorted'] = True
	if radial_averaged is True:
		stackq['radial_averaged'] = True
	if centered is True:
		stackq['centered'] = True
		if 'mask' in params:
			stackq['mask'] = params['mask']
		if 'maxshift' in params:
			stackq['maxshift'] = params['maxshift']

	## insert now before datamanager cleans up referenced data
	stackq.insert()
	apDisplay.printMsg("created new stackdata in %s\n"%(apDisplay.timeString(time.time()-t0)))

	newstackid = stackq.dbid

	t0 = time.time()
	# get list of included particles
	apDisplay.printMsg("Getting list of particles to include")

	if included:
		listfilelines = [p+1 for p in included]
	else:
		### read list
		listfilelines = []
		listfile = params['keepfile']

		f=open(listfile,'r')
		for line in f:
			sline = line.strip()
			if re.match("[0-9]+", sline):
				listfilelines.append(int(sline.split()[0])+1)
			else:
				apDisplay.printWarning("Line in listfile is not int: "+str(line))
		f.close()
		listfilelines.sort()

	apDisplay.printMsg("Completed in "+apDisplay.timeString(time.time()-t0)+"\n")

	## index old stack particles by number
	apDisplay.printMsg("Retrieving original stack information")
	t0 = time.time()
	part_by_number = {}
	
	# get stack data from original particles
	if not oldstackparts:
		sqlcmd = "SELECT * FROM ApStackParticleData " + \
			"WHERE `REF|ApStackData|stack` = %i"%(params['stackid'])
		# This result gives dictionary, not data object
		oldstackparts = sinedon.directq.complexMysqlQuery('appiondata',sqlcmd)

	for part in oldstackparts:
		part_by_number[part['particleNumber']] = part

	apDisplay.printMsg("Completed in "+apDisplay.timeString(time.time()-t0)+"\n")
	
	apDisplay.printMsg("Assembling database insertion command")
	t0 = time.time()
	count = 0
	newpartnum = 1

	partlistvals = []	 
	for origpartnum in listfilelines:
		count += 1
		oldstackpartdata = part_by_number[origpartnum]
		sqlParams = ['particleNumber','REF|ApStackData|stack']
		vals = [newpartnum,newstackid]
		for k,v in oldstackpartdata.iteritems():
			# First need to convert the keys to column names
			k = sinedon.directq.datakeyToSqlColumnName(oldstackpartdata,k)
			if k in ['DEF_id', 
				'DEF_timestamp', 
				'particleNumber', 
				'REF|ApStackData|stack']:
				continue
			sqlParams.append(k)
			# oldstackpartdata can either be sinedon data object
			# as passed through the function call
			# or a pure dictionary from directq.complexMysqlQuery
			# In the latter case v is just a long integer, not
			# data reference.
			if 'REF|' in k and hasattr(v,'dbid'):
				# if it is a sinedon data object
				v = v.dbid
			vals.append(v)
		valstr = "('"+"','".join(str(x) for x in vals)+"')"
		# sql understand Null without string quote, not 'None'
		valstr = valstr.replace("'None'","Null")
		partlistvals.append(valstr)

		newpartnum += 1

	apDisplay.printMsg("Inserting particle information into database")

	sqlstart = "INSERT INTO `ApStackParticleData` (`" + \
		"`,`".join(sqlParams)+ "`) VALUES "
	# break up command into groups of 100K inserts
	# this is a workaround for the max_allowed_packet at 16MB
	n = 100000
	sqlinserts = [partlistvals[i:i+n] \
		for i in range(0, len(partlistvals), n)]

	if params['commit'] is True:
		for sqlinsert in sqlinserts:
			sqlcmd=sqlstart+",".join(sqlinsert)
			sinedon.directq.complexMysqlQuery('appiondata',sqlcmd)

	sys.stderr.write("\n")
	if newpartnum == 0:
		apDisplay.printError("No particles were inserted for the stack")

	apDisplay.printColor("Inserted "+str(newpartnum-1)+ \
		" stack particles into the database in "+ \
		apDisplay.timeString(time.time()-t0),"cyan")

	apDisplay.printMsg("\nInserting Runs in Stack")
	runsinstack = getRunsInStack(params['stackid'])
	for run in runsinstack:
		newrunsq = appiondata.ApRunsInStackData()
		newrunsq['stack'] = stackq
		newrunsq['stackRun'] = run['stackRun']
		if params['commit'] is True:
			newrunsq.insert()
		else:
			apDisplay.printWarning("Not committing to the database")

	apDisplay.printMsg("finished")
	return

#===============
def commitMaskedStack(params, oldstackparts, newname=False):
	"""
	commit a substack to database

	required params:
		stackid
		description
		commit
		rundir
		mask
	"""
	oldstackdata = getOnlyStackData(params['stackid'], msg=False)

	#create new stack data
	stackq = appiondata.ApStackData()
	stackq['path'] = appiondata.ApPathData(path=os.path.abspath(params['rundir']))
	stackq['name'] = oldstackdata['name']

	# use new stack name if provided
	if newname:
		stackq['name'] = newname

	stackdata=stackq.query(results=1)

	if stackdata:
		apDisplay.printWarning("A stack with these parameters already exists")
		return
	stackq['oldstack'] = oldstackdata
	stackq['hidden'] = False
	stackq['substackname'] = params['runname']
	stackq['description'] = params['description']
	stackq['pixelsize'] = oldstackdata['pixelsize']
	stackq['boxsize'] = oldstackdata['boxsize']
	stackq['mask'] = params['mask']
	if 'correctbeamtilt' in params.keys():
		stackq['beamtilt_corrected'] = params['correctbeamtilt']

	## insert now before datamanager cleans up referenced data
	stackq.insert()

	#Insert particles
	apDisplay.printMsg("Inserting stack particles")
	count = 0
	newpartnum = 1
	total = len(oldstackparts)
	for part in oldstackparts:
		count += 1
		if count % 100 == 0:
			sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
			sys.stderr.write(str(count)+" of "+(str(total))+" complete")

		# Insert particle
		newstackq = appiondata.ApStackParticleData()
		newstackq.update(part)
		newstackq['particleNumber'] = newpartnum
		newstackq['stack'] = stackq
		if params['commit'] is True:
			newstackq.insert()
		newpartnum += 1
	sys.stderr.write("\n")
	if newpartnum == 0:
		apDisplay.printError("No particles were inserted for the stack")

	apDisplay.printMsg("Inserted "+str(newpartnum-1)+" stack particles into the database")

	apDisplay.printMsg("Inserting Runs in Stack")
	runsinstack = getRunsInStack(params['stackid'])
	for run in runsinstack:
		newrunsq = appiondata.ApRunsInStackData()
		newrunsq['stack'] = stackq
		newrunsq['stackRun'] = run['stackRun']
		if params['commit'] is True:
			newrunsq.insert()
		else:
			apDisplay.printWarning("Not commiting to the database")

	apDisplay.printMsg("finished")
	return