#!/usr/bin/env python
import os
import socket
import shutil
import numpy
import glob

#pyami
from pyami import fileutil
from pyami import mrc
#appion
from appionlib import apDDStackMaker
from appionlib import apDDFrameAligner
from appionlib import apDDResult
from appionlib import apFile

class AlignStackLoop(apDDStackMaker.FrameStackLoop):
	def setupParserOptions(self):
		super(AlignStackLoop,self).setupParserOptions()
		self.parser.add_option("--align", dest="align", default=False,
			action="store_true", help="Make Aligned frame stack")
		self.parser.add_option("--defergpu", dest="defergpu", default=False,
			action="store_true", help="Make unaligned frame stack first on computer without gpu alignment program")

	#=======================
	def checkConflicts(self):
		if self.params['align'] and not self.params['defergpu']:
			self.checkFrameAlignerExecutable()

			# Local directory creating and permission checking
			if self.params['tempdir']:
				try:
					fileutil.mkdirs(self.params['tempdir'])
					os.access(self.params['tempdir'],os.W_OK|os.X_OK)
				except:
					self.logger.error('Local temp directory not writable')
		else:
			# makes no sense to save gain corrected ddstack in tempdir if no alignment
			# will be done on the same machine
			if self.params['tempdir']:
				self.logger.warning('tempdir is not neccessary without aligning on the same host. Reset to None')
				self.params['tempdir'] = None
			# Stack cleaning should not be done in some cases
			if not self.params['keepstack']:
				if self.params['defergpu']:
					self.logger.warning('The gain/dark-corrected stack must be saved if alignment is deferred')
					self.params['keepstack'] = True
				else:
					self.logger.error('Why making only gain/dark-corrected ddstacks but not keeping them')

	def setFrameAligner(self):
		self.framealigner = apDDFrameAligner.DDFrameAligner()

	def checkFrameAlignerExecutable(self):
		self.setFrameAligner()

	#=======================
	def preLoopFunctions(self):
		self.is_ok = True
		self.setFrameAligner()
		self.framealigner.setFrameAlignOptions(self.params)
		self.hostname = socket.gethostname()
		super(AlignStackLoop,self).preLoopFunctions()

	def setTempPaths(self):
		# The alignment is done in tempdir (a local directory to reduce network traffic)
		bintext = self.getAlignBin()
		self.temp_logpath = self.dd.tempframestackpath[:-4]+bintext+'_Log.txt'

	def setOtherProcessImageResultParams(self):
		'''
		result path needed for alignment. This is run before alignment
		'''
		# The alignment is done in tempdir (a local directory to reduce network traffic)
		self.setTempPaths()

		self.log = self.dd.framestackpath[:-4]+'_Log.txt'
		self.framealigner.setInputFrameStackPath(self.dd.tempframestackpath)
		self.framealigner.setAlignedSumPath(self.dd.aligned_sumpath)
		self.framealigner.setAlignedStackPath(self.dd.aligned_stackpath)
		# Log is stream to self.temp_logpath but will be convert or copied to self.log later
		self.framealigner.setLogPath(self.temp_logpath)

		if self.isAlign():
			self.framealigner.setStackBinning(self.dd.stack_binning)
			# set framelist
			framelist = self.dd.getFrameListFromParams(self.params)
			self.dd.setAlignedSumFrameList(framelist)
			# AlignedCameraEMData needs framelist
			self.dd.setAlignedCameraEMData()
			self.framealigner.setInputNumberOfFrames(self.nframes)
			self.framealigner.setAlignedSumFrameList(framelist)
			# whether the sum can be don in framealigner depends on the framelist
			self.framealigner.setIsUseFrameAlignerSum(self.isUseFrameAlignerSum())
			self.framealigner.setSaveAlignedStack(self.dd.getKeepAlignedStack())
			if self.isUseFrameAlignerFlat():
				self.dd.makeDarkNormMrcs()
				gain_ref = self.dd.getNormRefMrcPath()
				per_frame_dark_ref = self.dd.getDarkRefMrcPath()
				self.framealigner.setGainDarkCmd(gain_ref, per_frame_dark_ref)

	def isAlign(self):
		return self.params['align']

	def isUseFrameAlignerFlat(self):
		if self.dd.hasBadPixels() or not self.isAlign():
			self.dd.setUseFrameAlignerFlat(False)
			return False
		else:
			self.dd.setUseFrameAlignerFlat(True)
			return True

	def isUseFrameAlignerSum(self):
		return self.dd.isSumSubStackWithFrameAligner()

	def imageYFlip(self, filepath):
		if os.path.isfile(filepath):
			a = mrc.read(filepath)
			self.logger.info('flipping %s' % filepath)
			a = numpy.flipud(a)
			mrc.write(a, filepath)

	def imageRotate(self, filepath, number):
		if os.path.isfile(filepath):
			a = mrc.read(filepath)
			self.logger.warning('Rotation direction not checked yet, report if wrong')
			# This operation has not being checked, yet.
			a = numpy.rot90(a, number)
			mrc.write(a, filepath)

	def getAlignBin(self):
		alignbin = self.params['bin']
		if alignbin > 1:
			bintext = '_%dx' % (alignbin)
		else:
			bintext = ''
		return bintext

	#=======================
	def otherProcessImage(self, imgdata):
		# Align
		if self.params['align']:
			# make a fake log so that catchUpDDAlign will know that frame stack is done
			fakelog = self.log
			f = open(fakelog,'w')
			f.write('Fake log to mark the unaligned frame stack as done\n')
			f.close()
			if self.params['defergpu']:
				return
			
			os.chdir(self.dd.tempdir)
			# actual alignment
			self.alignFrameStack()
			# organize the results
			self.is_ok = self.organizeAlignedSum()
			if not self.is_ok:
				os.chdir(self.dd.rundir)
				return
			self.organizeAlignedStack()
			os.chdir(self.dd.rundir)
	
	def organizeAlignedSum(self):
		if not os.path.isfile(self.dd.aligned_sumpath):
			self.logger.warning('Frame alignment FAILED: \n%s not created.' % os.path.basename(self.dd.aligned_sumpath))
			return False
		else:
			# successful alignment
			self.convertLogFile()
			if self.dd.getKeepAlignedStack():
				# bug in MotionCorr requires this
				self.dd.updateFrameStackHeaderImageStats(self.dd.aligned_stackpath)
			if not self.isUseFrameAlignerSum():
				# replace the sum with one corresponds with framelist
				self.sumSubStackWithNumpy(self.dd.aligned_stackpath,self.dd.aligned_sumpath)

			# self.dd.aligned_sumpath should have the right number of frames at this point
			shutil.move(self.dd.aligned_sumpath,self.dd.aligned_sumpath)
			return self.dd.aligned_sumpath

	def organizeAlignedStack(self):
		'''
		Things to do after alignment.
			1. Save the sum as imagedata
			2. Replace unaligned ddstack
		'''
		if os.path.isfile(self.dd.aligned_sumpath):
			# Save the alignment result
			self.aligned_imagedata = self.dd.makeAlignedImageData(alignlabel=self.params['alignlabel'])
			self.logger.debug('self.dd.aligned_stackpath= %s' % self.dd.aligned_stackpath)
			self.logger.debug('self.dd.framestackpath= %s' % self.dd.framestackpath)

			if self.params['keepstack']:
				if not os.path.isfile(self.dd.aligned_stackpath):
					self.logger.warning('No aligned stack generated as %s' % self.dd.aligned_stackpath)
			else:
				if os.path.isfile(self.dd.aligned_stackpath):
					apFile.removeFile(self.dd.aligned_stackpath)
			
			# replace the unaligned stack with aligned_stack
			if os.path.isfile(self.dd.aligned_stackpath):
				# aligned_stackpath exists either because keepstack is true
				self.logger.info(' Replacing unaligned stack with the aligned one....')
				apFile.removeFile(self.dd.framestackpath)
				self.logger.info('Moving %s to %s' % (self.dd.aligned_stackpath,self.dd.framestackpath))
				shutil.move(self.dd.aligned_stackpath,self.dd.framestackpath)

	def otherCleanUp(self, imgdata):
		if not self.is_ok:
			self.logger.warning('Nothing to clean up')
			return
		# Clean up tempdir in case of failed alignment
		if self.dd.framestackpath != self.dd.tempframestackpath:
			apFile.removeFile(self.dd.tempframestackpath)

	def convertLogFile(self):
		'''
		Standard LogFile is in XX form.
		'''
		if self.temp_logpath != self.log:
			# Move the Log to permanent location for display and inspection
			if os.path.isfile(self.temp_logpath):
				shutil.move(self.temp_logpath,self.log)
				self.logger.info('Moving result for %s from %s to %s' % (self.dd.image['filename'],self.dd.tempdir,self.dd.rundir))

	def alignFrameStack(self):
		# Align
		if self.params['align']:
			# Doing the alignment
			self.framealigner.alignFrameStack()

	def commitAlignStats(self, aligned_imgdata):
		try:
			ddr = apDDResult.DDResults(aligned_imgdata)
			xydict = ddr.getFrameTrajectoryFromLog()
		except Exception as e:
			self.logger.error('Can not commit alignmnet stats: %s' % e) 
		trajdata = ddr.saveFrameTrajectory(ddr.ddstackrun, xydict)
		ddr.saveAlignStats(ddr.ddstackrun, trajdata)

	def loopCleanUp(self, imgdata):
		'''
		Clean up within AppionLoop.  This is executed after commitToDatabase,
		and is used to remove align corrected mrc files.
		'''
		super(AlignStackLoop, self).loopCleanUp(imgdata)
		if self.aligned_imagedata != None and self.params['commit']:
			pattern = imgdata['filename']+'_c*.mrc'
			mrcs_to_delete = glob.glob(pattern)
			if mrcs_to_delete:
				self.logger.warning('Deleting temporary results after upload')
			for filename in mrcs_to_delete:
				apFile.removeFile(filename, False)

if __name__ == '__main__':
	makeStack = AlignStackLoop()
	makeStack.run()
