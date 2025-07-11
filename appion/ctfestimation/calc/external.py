# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center

from shutil import which
import os
import pexpect
from log import parseLog
from io import BytesIO

def ctffind(input : str, output : str, is_movie : str = "", num_frame_avg : str = "", 
            pixel_size : str = "", kv : str = "", cs : str = "", ampcontrast : str = "", 
            fieldsize : str = "", resmin : str = "", resmax : str = "", defmin : str = "", defmax : str = "", 
            defstep : str = "", known_astig : str = "", exhaustive_astig_search : str = "", astig : str = "", 
            astig_angle : str = "", restrain_astig : str = "", expect_astig : str = "", phase : str = "no",
            min_phase_shift : str = "",  max_phase_shift : str = "", phase_search_step : str = "", expert_opts: str = "no", 
            executable : str = "ctffind4") -> tuple:
    cmd=which(executable)
    if not cmd:
        raise RuntimeError("%s binary is not in path.  Cannot execute." % executable)
    prompts={
			r'Input image file name': os.path.abspath(str(input)),
			r'Input is a movie \(stack of frames\)' : str(is_movie),
			r'Number of frames to average together' : str(num_frame_avg),
			r'Output diagnostic image file name' : os.path.abspath(str(output)),
			r'Pixel size' : str(pixel_size),
			r'Acceleration voltage' : str(kv),
			r'Spherical aberration' : str(cs),
			r'Amplitude contrast' : str(ampcontrast),
			r'Size of amplitude spectrum to compute' : str(fieldsize),
			r'Minimum resolution' : str(resmin),
			r'Maximum resolution' : str(resmax),
			r'Minimum defocus' : str(defmin),
			r'Maximum defocus' : str(defmax),
			r'Defocus search step' : str(defstep),
			r'Do you know what astigmatism is present\?' : str(known_astig),
			r'Slower, more exhaustive search\?' : str(exhaustive_astig_search),
			r'Known astigmatism' : str(astig),
			r'Known astigmatism angle': str(astig_angle),
			r'Use a restraint on astigmatism\?' : str(restrain_astig),
			r'Expected \(tolerated\) astigmatism': str(expect_astig),
			r'Find additional phase shift\?' : str(phase),
			r'Minimum phase shift \(rad\)' : str(min_phase_shift),
			r'Maximum phase shift \(rad\)' : str(max_phase_shift),
			r'Phase shift search step' : str(phase_search_step),
			r'Do you want to set expert options\?' : str(expert_opts)
		}
    promptPatterns=list(prompts.keys())
    promptPatterns.append(pexpect.EOF)
    task=pexpect.spawn(cmd)
    stdout=BytesIO()
    task.logfile=stdout
    while len(promptPatterns) >= 1:
        idx=task.expect(promptPatterns)
        # EOF matched
        if idx == len(promptPatterns)-1:
            break
        task.sendline(str(prompts[promptPatterns[idx]]))
        promptPatterns.pop(idx)
    stdout=stdout.getvalue().decode("utf-8").split("\n")
    resultspath=""
    for line in stdout:
         if line.startswith("Summary of results"):
              resultspath=line.split(":")[1].strip()
    with open(resultspath, "r") as f:
         rawoutput=f.readlines()
    output=parseLog(rawoutput)
    return output, rawoutput


    
        