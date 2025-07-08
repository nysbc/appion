# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center

from shutil import which
from ..retrieve.version import readMotionCorVersion
from ..retrieve.logs import retrieveLogParser
import subprocess
from subprocess import CalledProcessError

def compareSupportedVersion(version : str) -> bool:
    return version in ["MotionCor2 version 1.5.0","MotionCor2 version 1.6.4"]

def validateMotionCorArgs(version : str, passedParams : set) -> bool:
    baseParams=set(["InMrc","InTiff","InEer","OutMrc","ArcDir",
                    "FullSum","DefectFile","InAln","OutAln",
                    "DefectMap","Serial","Gain","Dark","TmpFile",
                    "Patch","Iter","Tol","Bft","PhaseOnly","StackZ",
                    "FtBin","InitDose","FmDose","PixSize","kV","Align",
                    "Throw","Trunc","SumRange","Group","Crop","FmRef",
                    "Tilt","RotGain","FlipGain","Mag","InFmMotion",
                    "Gpu","GpuMemUsage","UseGpus","SplitSum","OutStar", "EerSampling"])
    validParams=baseParams
    if len(validParams | passedParams) != len(validParams):
        return False, validParams
    if "InTiff" not in passedParams and "InMrc" not in passedParams and "InEer" not in passedParams:
        return False, validParams
    return True, validParams

#TODO Write unit test.
def constructMotionCorCmd(cmd, kwargs):
    cmd=[cmd]
    for k,v in kwargs.items():
        if type(v) in [tuple, list]:
            kwargs[k]=" ".join([str(e) for e in v])
    cmd+=["-%s" % item[idx] if idx == 0 else str(item[idx]) for item in kwargs.items() for idx in range(2)]
    return cmd

def motioncor(executable="motioncor2", **kwargs) -> tuple:
    cmd=which(executable)
    if not cmd:
        raise RuntimeError("%s binary is not in path.  Cannot execute." % executable)
    else:
        version=readMotionCorVersion(cmd)
        if not version:
            raise RuntimeError("Could not determine motioncor version.")
        supported=compareSupportedVersion(version)
        if not supported:
            raise RuntimeError("Unsupported version of motioncor: %s" % str(version))
        validArgs, validParams=validateMotionCorArgs(version, set(kwargs.keys()))
        if not validArgs:
            invalidArgs=", ".join(list(set(kwargs.keys()) - validParams))
            invalidArgs=invalidArgs.rstrip(", ")
            validParamsStr=", ".join(list(validParams))
            validParamsStr=validParamsStr.rstrip(", ")
            raise RuntimeError("Invalid argument(s) passed in: %s.\nValid parameters are as follows: %s" % (invalidArgs, validParamsStr))
        logparser=retrieveLogParser(version)
        if not logparser:
            raise RuntimeError("No supported log parser for motioncor version %s." % version)
    cmd=constructMotionCorCmd(cmd, kwargs)
    try:
        proc=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, text=True, encoding="utf-8")
    except CalledProcessError as e:
        raise RuntimeError("motioncor2 failed to run.  \n\nStdOut: %s\n\nStdErr: %s" % (e.stdout, e.stderr)) from e
    rawoutput=proc.stdout
    output=rawoutput.split("\n")
    output=logparser(output)
    return output, rawoutput