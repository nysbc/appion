class ApAceRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('aceparams', ApAceParamsData),
			('ctftilt_params', ApCtfTiltParamsData),
			('xmipp_ctf_params', ApXmippCtfParamsData),
			('ace2_params', ApAce2ParamsData),
			('ctffind4_params', ApCtfFind4ParamsData),
			('transferred', bool),
			('transfer_params', ApAceTransferParamsData),
			('session', leginon.leginondata.SessionData),
			('path', ApPathData),
			('name', str),
			('hidden', bool),
		)
	typemap = classmethod(typemap)