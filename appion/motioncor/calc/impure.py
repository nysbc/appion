# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center

from shutil import which
import subprocess
from appion.motioncor.retrieve.logs import parseMotionCorLog

VALIDPARAMS=set(["InMrc","InTiff","InEer","OutMrc","ArcDir",
                    "FullSum","DefectFile","InAln","OutAln",
                    "DefectMap","Serial","Gain","Dark","TmpFile",
                    "Patch","Iter","Tol","Bft","PhaseOnly","StackZ",
                    "FtBin","InitDose","FmDose","PixSize","kV","Align",
                    "Throw","Trunc","SumRange","Group","Crop","FmRef",
                    "Tilt","RotGain","FlipGain","Mag","InFmMotion",
                    "Gpu","GpuMemUsage","UseGpus","SplitSum","OutStar"])

def motioncor(dryrun : bool = False, motionCorVersion: str = "2.1.5.0", executable="motioncor2", **kwargs) -> tuple:
    # Convert semantic version to int.  Use a dummy version if the version can't be cast into a float.
    try:
        motionCorVersion=motionCorVersion.split(".")
        majorVersion=int(motionCorVersion[0])
        motionCorVersion=float("".join(motionCorVersion))/(10**(len(motionCorVersion)-1))
    except:
        majorVersion=0
        motionCorVersion=0.0
    if majorVersion not in [2,3]:
        raise RuntimeError("Unsupported major version of motioncor: %d" % majorVersion)
    passedParams=set(kwargs.keys())
    if len(VALIDPARAMS | passedParams) != len(VALIDPARAMS):
        raise RuntimeError("Unsupported parameters: %s" % ", ".join(passedParams - VALIDPARAMS))
    if "InTiff" not in passedParams and "InMrc" not in passedParams and "InEer" not in passedParams:
        raise RuntimeError("Input file not specified for %s run." % executable)
    cmd=which(executable)
    if not cmd:
        raise RuntimeError("%s binary is not in path.  Cannot execute." % executable)
    else:
        cmd=[cmd]
    for k,v in kwargs.items():
        if type(v) in [tuple, list]:
            kwargs[k]=" ".join([str(e) for e in v])
    cmd+=["-%s" % item[idx] if idx == 0 else str(item[idx]) for item in kwargs.items() for idx in range(2)]
    if dryrun:
        print(" ".join(cmd))
        rawoutput=""
        output={}
    else:
        proc=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, text=True, encoding="utf-8")
        rawoutput=proc.stdout
        output=rawoutput.split("\n")
        output=parseMotionCorLog(output)
    return output, rawoutput