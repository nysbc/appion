#!/usr/bin/env python
import os
import shutil
from appionlib import apDDMotionCor2Maker

if __name__ == '__main__':
	makeStack = apDDMotionCor2Maker.MotionCor2UCSFAlignStackLoop()
	makeStack.run()
