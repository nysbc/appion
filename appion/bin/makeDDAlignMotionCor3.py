#!/usr/bin/env python
import os
import shutil
from appionlib import apDDMotionCorrMaker
from appionlib import apDDFrameAligner
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apDisplay

if __name__ == '__main__':
	makeStack = apDDMotionCorrMaker.MotionCor3AlignStackLoop()
	makeStack.run()
