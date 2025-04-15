class ApAppionJobData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('cluster', str),
			('jobtype', str),
			('status', str),
			('user', str),
			('clusterjobid', int),
			('path', ApPathData),
			('session', leginon.leginondata.SessionData),
			('dmfpath', ApPathData),
			('clusterpath', ApPathData),

		)
	typemap = classmethod(typemap)