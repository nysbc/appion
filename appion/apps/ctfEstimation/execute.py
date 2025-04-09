from shutil import which
import os
import pexpect
from logParser import parseLog

def ctffind(input : str, is_movie : str, num_frame_avg : str, output : str, pixel_size : str, kv : str, cs : str, ampcontrast : str, 
            fieldsize : str, resmin : str, resmax : str, defmin : str, defmax : str, 
            defstep : str, known_astig : str, exhaustive_astig_search : str, astig : str, 
            astig_angle : str, restrain_astig : str, expect_astig : str, phase : str,
            min_phase_shift : str,  max_phase_shift : str, phase_search_step : str, expert_opts: str, 
            executable : str = "ctffind4") -> tuple:
    cmd=which(executable)
    if not cmd:
        raise RuntimeError("%s binary is not in path.  Cannot execute." % executable)
    prompts={
			'Input image file name': os.path.abspath(str(input)),
			'Input is a movie (stack of frames)' : str(is_movie),
			'Number of frames to average together' : str(num_frame_avg),
			'Output diagnostic image file name' : os.path.abspath(str(output)),
			'Pixel size' : str(pixel_size),
			'Acceleration voltage' : str(kv),
			'Spherical aberration' : str(cs),
			'Amplitude contrast' : str(ampcontrast),
			'Size of amplitude spectrum to compute' : str(fieldsize),
			'Minimum resolution' : str(resmin),
			'Maximum resolution' : str(resmax),
			'Minimum defocus' : str(defmin),
			'Maximum defocus' : str(defmax),
			'Defocus search step' : str(defstep),
			'Do you know what astigmatism is present?' : str(known_astig),
			'Slower, more exhaustive search?' : str(exhaustive_astig_search),
			'Known astigmatism' : str(astig),
			'Known astigmatism angle': str(astig_angle),
			'Use a restraint on astigmatism?' : str(restrain_astig),
			'Expected (tolerated) astigmatism': str(expect_astig),
			'Find additional phase shift?' : str(phase),
			'Minimum phase shift (rad)' : str(min_phase_shift),
			'Maximum phase shift (rad)' : str(max_phase_shift),
			'Phase shift search step' : str(phase_search_step),
			'Do you want to set expert options?' : str(expert_opts)
		}
    promptPatterns=list(prompts.keys())
    task=pexpect.spawn(cmd)
    while promptPatterns:
        idx=task.expect(promptPatterns)
        task.sendline(str(prompts[promptPatterns[idx]]))
        promptPatterns.pop(idx)
    rawoutput = task.read()
    output=rawoutput.split("\n")
    output=parseLog(output)
    return output, rawoutput
    
        