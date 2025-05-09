#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

class MotionCor2UCSFAlignStackLoop(apDDMotionCorrMaker.MotionCorrAlignStackLoop):
	#=======================
	def setupParserOptions(self):
		# Integer
		parser.add_option("--ddstartframe", dest="startframe", type="int", default=0,
			help="starting frame for summing the frames. The first frame is 0")
		parser.add_option("--alignlabel", dest="alignlabel", default='a',
			help="label to be appended to the presetname, e.g. --label=a gives ed-a as the aligned preset for preset ed", metavar="CHAR")
		parser.add_option("--bin",dest="bin",metavar="#",type=float,default="1.0",
			help="Binning factor relative to the dd stack. MotionCor2 takes float value (optional)")

		# Dosefgpu_driftcoor options
		parser.add_option("--alignoffset", dest="fod", type="int", default=2,
			help="number of frame offset in alignment in dosefgpu_driftcorr")
		parser.add_option("--alignccbox", dest="pbx", type="int", default=128,
			help="alignment CC search box size in dosefgpu_driftcorr")

		# Dose weighting, based on Grant & Grigorieff eLife 2015
		parser.add_option("--doseweight",dest="doseweight",metavar="bool", default=False,
			action="store_true", help="dose weight the frame stack, according to Tim / Niko's curves")
		parser.add_option("--totaldose",dest="totaldose",metavar="float",type=float,
                        help="total dose for the full movie stack in e/A^2. If not specified, will get value from database")

		#parser.add_option("--override_db", dest="override_db", default=False,
		#	action="store_true", help="Override database for bad rows, columns, and image flips")
		# String

		# Integer


		parser.add_option("--trim", dest="trim", type="int", default=0,
			help="Trim edge off after frame stack gain/dark correction", metavar="INT")
		parser.add_option("--align", dest="align", default=False,
			action="store_true", help="Make Aligned frame stack")

		parser.add_option("--gpuid", dest="gpuid", type="int", default=0,
			help="GPU device id used in gpu processing", metavar="INT")

		parser.add_option("--gpuids", dest="gpuids", default='0')
		parser.add_option("--nrw", dest="nrw", type="int", default=1,
			help="Number (1, 3, 5, ...) of frames in running average window. 0 = disabled", metavar="INT")

		parser.add_option("--FmRef", dest="FmRef",type="int",default=0,
			help="Specify which frame to be the reference to which all other frames are aligned. Default 0 is aligned to the first frame, other values aligns to the central frame.", metavar="#")

		parser.add_option("--Iter", dest="Iter",type="int",default=7,
			help="Maximum iterations for iterative alignment, default is 7.")

		parser.add_option("--Tol", dest="Tol",type="float",default=0.5,
                        help="Tolerance for iterative alignment, in pixels", metavar="#")

		parser.add_option("--Patchrows",dest="Patchrows",metavar="#",type=int,default="0",
			help="Number of patches divides the y-axis to be used for patch based alignment. Default 0 corresponds to full frame alignment in the direction.")

		parser.add_option("--Patchcols",dest="Patchcols",metavar="#",type=int,default="0",
			help="Number of patches divides the x-axis to be used for patch based alignment. Default 0 corresponds to full frame alignment in the direction.")

		parser.add_option("--MaskCentrow",dest="MaskCentrow",metavar="#",type=int,default="0",
			help="Y Coordinates for center of subarea that will be used for alignment. Default 0 corresponds to center coordinate.")

		parser.add_option("--MaskCentcol",dest="MaskCentcol",metavar="#",type=int,default="0",
			help="X Coordinate for center of subarea that will be used for alignment. Default 0 corresponds to center coordinate.")

		parser.add_option("--MaskSizecols",dest="MaskSizecols",metavar="#",type=float,default="1.0",
			help="The X size of subarea that will be used for alignment, default 1.0 1.0 corresponding full size.")
		parser.add_option("--MaskSizerows",dest="MaskSizerows",metavar="#",type=float,default="1.0",
			help="The Y size of subarea that will be used for alignment, default 1.0 corresponding full size.")

		# instead of single align bfactor, bft, this has two entries
		parser.add_option("--Bft_global",dest="Bft_global",metavar="#",type=float,default=500.0,
                        help=" Global B-Factor for alignment, default 500.0.")

		parser.add_option("--Bft_local",dest="Bft_local",metavar="#",type=float,default=150.0,
                        help=" Global B-Factor for alignment, default 150.0.")

		#parser.add_option("--force_cpu_flat", dest="force_cpu_flat", default=False,
		#	action="store_true", help="Use cpu to make frame flat field corrrection")

		parser.add_option("--rendered_frame_size", dest="rendered_frame_size", type="int", default=1,
			help="Sum this number of saved frames as a rendered frame in alignment", metavar="INT")
		parser.add_option("--eer_sampling", dest="eer_sampling", type="int", default=1,
			help="Upsampling eer frames. Fourier binning will be added to return the results back", metavar="INT")

		
	def setupGlobalParserOptions(self):
		"""
		set the input parameters
		"""

		self.tiltoptions = ("notilt", "hightilt", "lowtilt", "minustilt", "plustilt", "all")

		### Set usage
		parser.set_usage("Usage: %prog --projectid=## --runname=<runname> --session=<session> "
			+"--preset=<preset> --description='<text>' --commit [options]")
		### Input value options
		parser.add_option("-s", "--session", dest="sessionname",
			help="Session name associated with processing run, e.g. --session=06mar12a", metavar="SESSION")
		parser.add_option("--preset", dest="preset",
			help="Image preset associated with processing run, e.g. --preset=en", metavar="PRESET")

		#parser.add_option("--reprocess", dest="reprocess", type="float",
		#	help="Only process images that pass this reprocess criteria")
		parser.add_option("--tiltangle", dest="tiltangle", 
			default="all", type="choice", choices=self.tiltoptions,
			help="Only process images with specific tilt angles, options: "+str(self.tiltoptions))

		### True / False options
		parser.add_option("--continue", dest="continue", default=True,
			action="store_true", help="Continue processing run from last image")
		#parser.add_option("--no-continue", dest="continue", default=True,
		#	action="store_false", help="Do not continue processing run from last image")
		parser.add_option("--no-wait", dest="wait", default=True,
			action="store_false", help="Do not wait for more images after completing loop")
		parser.add_option("--no-rejects", dest="norejects", default=False,
			action="store_true", help="Do not process hidden or rejected images")
		parser.add_option("--reverse", dest="reverse", default=False,
			action="store_true", help="Process the images from newest to oldest")
		parser.add_option("--parallel", dest="parallel", default=False,
			action="store_true", help="parallel appionLoop on different cpu. Only work with the part not using gpu")

	def getAlignBin(self):
		alignbin = self.params['bin']
		if alignbin > 1:
			bintext = '_%4.1fx' % (alignbin)
		else:
			bintext = ''
		return bintext

	def organizeAlignedSum(self):
		'''
		Move local temp results to rundir in the official names
		'''
		temp_aligned_sumpath = self.temp_aligned_sumpath
		temp_aligned_dw_sumpath = self.temp_aligned_dw_sumpath
		gain_flip, gain_rotate = self.framealigner.getGainModification()
		need_flip = False
		if 'eer' in self.dd.__class__.__name__.lower():
			# output from -InEer is y-flipped even though gain in mrc
			# format is not relative to the eer file
			need_flip = True
		if gain_flip:
			need_flip = not need_flip
		if need_flip:
			apDisplay.printMsg('Flipping the aligned sum back')
			self.imageYFlip(temp_aligned_sumpath)
			self.imageYFlip(temp_aligned_dw_sumpath)
		if gain_rotate:
			apDisplay.printMsg('Rotating the aligned sum back')
			self.imageRotate(temp_aligned_sumpath, gain_rotate)
			self.imageRotate(temp_aligned_dw_sumpath, gain_rotate)
		# dose weighted result handled here
		if os.path.isfile(temp_aligned_sumpath):
			if self.params['doseweight'] is True and self.has_dose:
				shutil.move(temp_aligned_dw_sumpath,self.dd.aligned_dw_sumpath)
		return super(MotionCor2UCSFAlignStackLoop,self).organizeAlignedSum()

	def organizeAlignedStack(self):
		'''
		Things to do after alignment.
			1. Save the sum as imagedata
			2. Replace unaligned ddstack
		'''
		if os.path.isfile(self.dd.aligned_sumpath):
			if self.params['doseweight'] is True and self.has_dose:
				self.params['align_dw_label'] = self.params['alignlabel']+"-DW"
				self.aligned_dw_imagedata = self.dd.makeAlignedDWImageData(alignlabel=self.params['align_dw_label'])

		super(MotionCor2UCSFAlignStackLoop,self).organizeAlignedStack()

if __name__ == '__main__':
	makeStack = MotionCor2UCSFAlignStackLoop()
	makeStack.run()
