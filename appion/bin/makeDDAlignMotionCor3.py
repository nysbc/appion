#!/usr/bin/env python
from appionlib import apDDMotionCor2Maker

class MotionCor3AlignStackLoop(apDDMotionCor2Maker.MotionCor2UCSFAlignStackLoop):
	#=======================
	def setupParserOptions(self):
		super(MotionCor3AlignStackLoop,self).setupParserOptions()

		self.parser.add_option("--InSkips", dest="inskips", type="str", default="")
		self.parser.add_option("--Cs", dest="cs", type="float", default=2.70)
		self.parser.add_option("--AmpCont", dest="ampcont",type="float",default=0.00)
		self.parser.add_option("--ExtPhase", dest="extphase",type="int",default=0)


if __name__ == '__main__':
	makeStack = MotionCor3AlignStackLoop()
	makeStack.run()
