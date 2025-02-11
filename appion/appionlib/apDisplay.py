
import math
import os
import re
import sys
import types

####
# This is a low-level file with NO database connections
# Please keep it this way
####

debug = False
writeOut = False
try:
	outFile = os.path.basename(sys.argv[0]).split(".")[0]+".out"
except:
	outFile = "function.out"

def isDebugOn():
	return debug

def printColor(text, colorstr):
	"""
	standardized log message
	"""
	if writeOut is True:
		try:
			f = open(outFile, "a")
			f.write(" ... "+text+"\n")
			f.close()
		except:
			print "write error"
	sys.stderr.write(colorString(text, colorstr)+"\n")

def bytes(numbytes):
	numbytes = int(numbytes)
	mult = 1024.0
	if numbytes < mult:
		return "%d B"%(numbytes)
	elif numbytes < mult**2:
		return "%.1f kB"%(numbytes/mult)
	elif numbytes < mult**3:
		return "%.1f MB"%(numbytes/mult**2)
	elif numbytes < mult**4:
		return "%.1f GB"%(numbytes/mult**3)
	elif numbytes < mult**5:
		return "%.1f TB"%(numbytes/mult**4)
	else:
		return "%.1f PB"%(numbytes/mult**5)

def clusterBytes(numbytes):
	numbytes = int(numbytes)
	mult = 1024.0
	if numbytes < mult:
		return "%db"%(math.ceil(numbytes))
	elif numbytes < mult**2:
		return "%dkb"%(math.ceil(numbytes/mult))
	elif numbytes < mult**3:
		return "%dmb"%(math.ceil(numbytes/mult**2))
	elif numbytes < mult**4:
		return "%dgb"%(math.ceil(numbytes/mult**3))
	else:
		return "%dtb"%(math.ceil(numbytes/mult**4))

def orderOfMag(num):
	if num > 1:
		num = int(num)
		if num < 1e3:
			return str(num)
		elif num < 1e6:
			return str(int(num/1e3))+"k"
		elif num < 1e9:
			return str(int(num/1e6))+"M"
		elif num < 1e12:
			return str(int(num/1e9))+"G"
	else:
		return str(num)

def timeString(avg, stdev=0):
	""" 
	returns a string with the length of time scaled for clarity
	"""
	avg = float(avg)
	stdev = float(stdev)
	#less than 0.5 microseconds
	if avg < 0.5e-6:
		if stdev > 0.0:
			timestr = str(round(avg*1e9,2))+" +/- "+str(round(stdev*1e9,2))+" nsec"
		else:
			timestr = str(round(avg*1e9,2))+" nsec"
	#less than 0.5 milliseconds
	elif avg < 0.5e-3:
		if stdev > 0.0:
			timestr = str(round(avg*1e6,2))+" +/- "+str(round(stdev*1e6,2))+" usec"
		else:
			timestr = str(round(avg*1e6,2))+" usec"
	#less than 0.5 seconds
	elif avg < 0.5:
		if stdev > 0.0:
			timestr = str(round(avg*1e3,2))+" +/- "+str(round(stdev*1e3,2))+" msec"
		else:
			timestr = str(round(avg*1e3,2))+" msec"
	#less than 70 seconds
	elif avg < 70.0:
		if stdev > 0.0:
			timestr = str(round(avg,2))+" +/- "+str(round(stdev,2))+" sec"
		else:
			timestr = str(round(avg,2))+" sec"
	#less than 70 minutes
	elif avg < 4200.0:
		subbase = 1.0
		base = subbase * 60.0
		majorunit = "min"
		minorunit = "sec"
		if stdev > 0.0:
			timestr = str(round(avg/base, 2))+" +/- "+str(round(stdev/base, 2))+" "+majorunit
		else:
			timestr = ( str(int(math.floor(avg/base)))+" "+majorunit+" "
				+str(int(round( (avg % base)/subbase )))+" "+minorunit )
	#less than 28 hours
	elif avg < 100800.0:
		subbase = 60.0
		base = subbase * 60.0
		majorunit = "hr"
		minorunit = "min"
		if stdev > 0.0:
			timestr = str(round(avg/base, 2))+" +/- "+str(round(stdev/base, 2))+" "+majorunit
		else:
			timestr = ( str(int(math.floor(avg/base)))+" "+majorunit+" "
				+str(int(round( (avg % base)/subbase )))+" "+minorunit )
	#more than 28 hours (1.2 days)
	else:
		subbase = 3600.0
		base = subbase * 24.0
		majorunit = "days"
		minorunit = "hr"
		if stdev > 0.0:
			timestr = str(round(avg/base, 2))+" +/- "+str(round(stdev/base, 2))+" "+majorunit
		else:
			timestr = ( str(int(math.floor(avg/base)))+" "+majorunit+" "
				+str(int(round( (avg % base)/subbase )))+" "+minorunit )
	return str(timestr)

def color(text, fg, bg=None):
	return colorString(text, fg, bg)

def clearColor():
	opencol = "\033["
	closecol = "m"
	clear = opencol + "0" + closecol
	return clear	

def colorString(text, fg=None, bg=None):
	"""Return colored text.
	Uses terminal color codes; set avk_util.enable_color to 0 to
	return plain un-colored text. If fg is a tuple, it's assumed to
	be (fg, bg). Both colors may be 'None'.
	"""
	colors = {
		"black" :"0;30",
		"red"   :"0;31",
		"green" :"0;32",
		"brown" :"0;33",
		"orange":"0;33",
		"blue"  :"0;34",
		"violet":"0;35",
		"purple":"0;35",
		"magenta":"0;35",
		"maroon":"0;35",
		"cyan"  :"0;36",
		"lgray" :"0;37",
		"gray"  :"1;30",
		"lred"  :"1;31",
		"lgreen":"1;32",
		"yellow":"1;33",
		"lblue" :"1;34",
		"pink"  :"1;35",
		"lcyan" :"1;36",
		"white" :"1;37"
	}
	if fg is None:
		return text
	if type(fg) in (types.TupleType, types.ListType):
		fg, bg = fg
	if not fg:
		return text
	opencol = "\033["
	closecol = "m"
	clear = opencol + "0" + closecol
	xterm = 0
	if os.environ.get("TERM") is not None and os.environ.get("TERM") == "xterm": 
		xterm = True
	else:
		xterm = False
	b = ''
	# In xterm, brown comes out as yellow..
	if xterm and fg == "yellow": 
		fg = "brown"
	f = opencol + colors[fg] + closecol
	if bg:
		if bg == "yellow" and xterm: 
			bg = "brown"
		try: 
			b = colors[bg].replace('3', '4', 1)
			b = opencol + b + closecol
		except KeyError: 
			pass
	return "%s%s%s%s" % (b, f, text, clear)

####
# This is a low-level file with NO database connections
# Please keep it this way
####


