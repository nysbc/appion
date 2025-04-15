class ApCtfTiltParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('medium', str),
			('ampcarbon', float),
			('ampice', float),
			('fieldsize', int),
			('cs', float),
			('bin', int),
			('resmin', float),
			('resmax', float),
			('defstep', float),
			('dast', float),
		)
	typemap = classmethod(typemap)