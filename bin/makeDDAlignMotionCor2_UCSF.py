#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2002-2015 Scripps Research Institute, 2015-2025 New York Structural Biology Center

import argparse
from appion.base.cli import constructGlobalParser
from appion.motioncorrection.cli import constructMotionCorParser
from appion.motioncorrection.cli import preTask, task, postTask
from appion.base import loop
from appion.base.calc import filterImages
from appion.base.store import saveCheckpoint
from dask_jobqueue import SLURMCluster
import sinedon.setup

def main():
    parser = argparse.ArgumentParser(parents=[constructGlobalParser(), constructMotionCorParser()])
    args = parser.parse_args()
    sinedon.setup(args.projectid)
    cluster = SLURMCluster(queue="long", cores=2, memory="16G", job_extra_directives=["-J motioncor2-worker"], processes=8,local_directory="/h2/jpellman/appion_django/dask/spillover", death_timeout=120, log_directory="/h2/jpellman/appion-django/dask/logs", walltime="2:00:00", shared_temp_directory="/h2/jpellman/appion_django/dask/shared_inc",scheduler_options={'port':8889})
    cluster.adapt(minimum_jobs=2,maximum_jobs=10)
    loop(filterImages, 
         lambda imageid : preTask(imageid, vars(args)), 
         lambda p_args : task(*p_args), 
         lambda p_args : postTask(*p_args), 
         saveCheckpoint, 
         cluster)
 
if __name__ == '__main__':
    main()

# class MotionCor2UCSFAlignStackLoop(apDDMotionCorrMaker.MotionCorrAlignStackLoop):
# 	#=======================

# 	def getAlignBin(self):
# 		alignbin = self.params['bin']
# 		if alignbin > 1:
# 			bintext = '_%4.1fx' % (alignbin)
# 		else:
# 			bintext = ''
# 		return bintext

# 	def organizeAlignedSum(self):
# 		'''
# 		Move local temp results to rundir in the official names
# 		'''
# 		temp_aligned_sumpath = self.temp_aligned_sumpath
# 		temp_aligned_dw_sumpath = self.temp_aligned_dw_sumpath
# 		gain_flip, gain_rotate = self.framealigner.getGainModification()
# 		need_flip = False
# 		if 'eer' in self.dd.__class__.__name__.lower():
# 			# output from -InEer is y-flipped even though gain in mrc
# 			# format is not relative to the eer file
# 			need_flip = True
# 		if gain_flip:
# 			need_flip = not need_flip
# 		if need_flip:
# 			apDisplay.printMsg('Flipping the aligned sum back')
# 			self.imageYFlip(temp_aligned_sumpath)
# 			self.imageYFlip(temp_aligned_dw_sumpath)
# 		if gain_rotate:
# 			apDisplay.printMsg('Rotating the aligned sum back')
# 			self.imageRotate(temp_aligned_sumpath, gain_rotate)
# 			self.imageRotate(temp_aligned_dw_sumpath, gain_rotate)
# 		# dose weighted result handled here
# 		if os.path.isfile(temp_aligned_sumpath):
# 			if self.params['doseweight'] is True and self.has_dose:
# 				shutil.move(temp_aligned_dw_sumpath,self.dd.aligned_dw_sumpath)
# 		return super(MotionCor2UCSFAlignStackLoop,self).organizeAlignedSum()

# 	def organizeAlignedStack(self):
# 		'''
# 		Things to do after alignment.
# 			1. Save the sum as imagedata
# 			2. Replace unaligned ddstack
# 		'''
# 		if os.path.isfile(self.dd.aligned_sumpath):
# 			if self.params['doseweight'] is True and self.has_dose:
# 				self.params['align_dw_label'] = self.params['alignlabel']+"-DW"
# 				self.aligned_dw_imagedata = self.dd.makeAlignedDWImageData(alignlabel=self.params['align_dw_label'])

# 		super(MotionCor2UCSFAlignStackLoop,self).organizeAlignedStack()

# if __name__ == '__main__':
# 	makeStack = MotionCor2UCSFAlignStackLoop()
# 	makeStack.run()
