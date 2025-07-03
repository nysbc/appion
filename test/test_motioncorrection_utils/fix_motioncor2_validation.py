import os
import re
import json

with open(os.path.join(os.getcwd(),"motioncor2_validation.json"), "r") as f:
    validationData=json.load(f)

#Fix flags in validation data that weren't populated correctly due to botched regex
MEMC_MOTIONCOR_CMDS="/srv/appion/test/motioncor_commands/memc_mar2025_motioncor2_commands"

fixed_flags={}
with open(MEMC_MOTIONCOR_CMDS,"r") as f:
    lines=f.readlines()
    for line in lines:
        # Motioncor2 Params
        outmrc=re.findall("-OutMrc ([\S]+)", line)
        if outmrc:
            outmrc=outmrc[0]
        else:
            continue
        bft=re.findall("-Bft ([\S]+) ([\S]+)", line)
        if bft:
            bft=bft[0]
        else:
            bft=""
        patch=re.findall("-Patch ([\S]+) ([\S]+)", line)
        if patch:
            patch=patch[0]
        else:
            patch=""
        masksize=re.findall("-MaskSize ([\S]+) ([\S]+)", line)
        if masksize:
            masksize=masksize[0]
        else:
            masksize=""
        fixed_flags[outmrc]={}
        fixed_flags[outmrc]["bft"]=bft
        fixed_flags[outmrc]["patch"]=patch
        fixed_flags[outmrc]["masksize"]=masksize
    
    for imgid in validationData.keys():
        if validationData[imgid]["motioncorflags"]["OutMrc"] in fixed_flags.keys():
            validationData[imgid]["motioncorflags"]["Bft"]="%s %s" % fixed_flags[validationData[imgid]["motioncorflags"]["OutMrc"]]["bft"]
            validationData[imgid]["motioncorflags"]["Patch"]="%s %s" % fixed_flags[validationData[imgid]["motioncorflags"]["OutMrc"]]["patch"]
            validationData[imgid]["motioncorflags"]["MaskSize"]="%s %s" % fixed_flags[validationData[imgid]["motioncorflags"]["OutMrc"]]["masksize"]
    
with open(os.path.join(os.getcwd(),"motioncor2_validation.json"), "w") as f:
    validationData=json.dump(validationData, f)