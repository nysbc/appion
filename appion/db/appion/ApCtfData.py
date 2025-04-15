class ApCtfData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('acerun', ApAceRunData),
			('image', leginon.leginondata.AcquisitionImageData),
			('cs', float),  # in millimeters
			('defocusinit', float),  # initial defocus
			('amplitude_contrast', float),  # sqrt(1-A^2)sin + A*cos format
			('defocus1', float),  # in negative meters for underfocus |def1| < |def2|
			('defocus2', float),  # in negative meters for underfocus
			('angle_astigmatism', float),  # in counter-clockwise degrees from x-axis (degrees)
			('ctffind4_resolution', float),  # ctffind4 good fit resolution
			('confidence', float),  # classic confidence
			('confidence_d', float),  # classic confidence
			('confidence_30_10', float),  # defined as confidence between 1/30 and 1/10 Angstroms
			('confidence_5_peak', float),  # defined as conidence of the first 5 peaks of the CTF
			('overfocus_conf_30_10', float),  # defined as confidence between 1/30 and 1/10 Angstroms
			('overfocus_conf_5_peak', float),  # defined as conidence of the first 5 peaks of the CTF
			('resolution_80_percent', float),  # resolution at 80% confidence
			('resolution_50_percent', float),  # resolution at 50% confidence
			('graph1', str),  # 2d powerspectra
			('graph2', str),  # 1d plot showing fit
			('graph3', str),  # raw native powerspectra from software 
			('graph4', str),  # raw native 1d plot from software 
			('localplot', str), # 2D plot for local CTF estimation
			('localCTFstarfile', str), # local CTF output file
			('ctfvalues_file', str),  # used for ace2correct
			('cross_correlation', float),  # direct from ctffind/ctftilt
			('tilt_angle', float),  # from ctftilt
			('tilt_axis_angle', float),  # from ctftilt
			('mat_file', str),  # from ACE1
			('extra_phase_shift', float), #phase plate phase shift addition (radians)
		)
	typemap = classmethod(typemap)