#!/usr/bin/env python

import os
import sys
import time
import subprocess

## this is a wrapper for all appion scripts
## use this function to launch from the web so that
## stdout & sterr will be saved to a file
if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage: webcaller.py '<command>' <outfile> (<mode>)"
		sys.exit(1)
	cmd = sys.argv[1]
	outf = sys.argv[2]
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.STDOUT, stderr=subprocess.STDERR)
	proc.wait()
