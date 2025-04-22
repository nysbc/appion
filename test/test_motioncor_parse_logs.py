import re
import os
from random import randint
import json
import django
django.setup()
from sinedon.models.leginon import AcquisitionImageData
'''
This script parses Appion logs to create a dict that maps
image IDs to the Appion parameters that are associated with their run,
and the motioncor2 parameters that are passed as inputs to the motioncor2 command.

This will be used to identify regressions in the logic used to generate motioncor2 commands.
'''

# Pre-computed grep outputs.
MEMC_APPION_CMDS="/h2/jpellman/18169/motioncor_commands/memc_mar2025_appion_commands"
#NCCAT_APPION_CMDS="/h2/jpellman/18169/motioncor_commands/nccat_mar2025_appion_commands"
MEMC_MOTIONCOR_CMDS="/h2/jpellman/18169/motioncor_commands/memc_mar2025_motioncor2_commands"
#NCCAT_MOTIONCOR_CMDS="/h2/jpellman/18169/motioncor_commands/nccat_mar2025_motioncor2_commands"

appionflags=[]
links=[]
motioncorflags=[]

#appioncmds=[MEMC_APPION_CMDS,NCCAT_APPION_CMDS]
appioncmds=[MEMC_APPION_CMDS]
for c in appioncmds:
    with open(c,"r") as f:
        lines=f.readlines()
        for line in lines:
            # All Appion flags
            appionflags+=[re.findall("--([\w|-]+)=?([\w|/]*)",line)]

#motioncorcmds=[MEMC_MOTIONCOR_CMDS, NCCAT_MOTIONCOR_CMDS]
motioncorcmds=[MEMC_MOTIONCOR_CMDS]
for c in motioncorcmds:
    with open(c,"r") as f:
        lines=f.readlines()
        for line in lines:
            # Symlinks
            links+=re.findall("\.\.\. link (.+) to (.+)\.", line)
            # Motioncor2 Params
            motioncorflags+=[re.findall("(?:-)([A-Z]\w+) ([\S]+)", line)]

appionflags=[dict(flaglist) for flaglist in appionflags if flaglist]
links=dict([(dst, src) for src, dst in links])
motioncorflags=[dict(flaglist) for flaglist in motioncorflags if flaglist]

validationDataJoin1={}
for aflags in appionflags:
    if "rundir" in aflags:
        validationDataJoin1[aflags["rundir"]]={"motioncorflags": [], "appionflags" : aflags}
        for mflags in motioncorflags:
            for inputflag in ["InMrc", "InTiff", "InEer"]:
                if inputflag in mflags.keys():
                    if mflags[inputflag].startswith(aflags["rundir"]):
                        validationDataJoin1[aflags["rundir"]]["motioncorflags"].append(mflags)

validationDataJoin2={}
for rundir in validationDataJoin1.keys():
    for mflags in validationDataJoin1[rundir]["motioncorflags"]:
        for inputflag in ["InMrc", "InTiff", "InEer"]:
            if inputflag in mflags.keys():
                if mflags[inputflag] in links.keys():
                    mflags[inputflag]=links[mflags[inputflag]]
                    validationDataJoin2[mflags[inputflag]]={"motioncorflags": mflags, "appionflags" : validationDataJoin1[rundir]["appionflags"]}

samplesize=25
keys=list(validationDataJoin2.keys())
finalValidationData={}
while samplesize > 0:
    print("%d sample(s) left to acquire." % samplesize)
    idx=randint(0,len(keys)-1)
    imgdata=AcquisitionImageData.objects.get(filename=os.path.basename(keys[idx].split(".")[0]))
    finalValidationData[imgdata.def_id]=validationDataJoin2[keys[idx]]
    keys.pop(idx)
    samplesize-=1

with open(os.path.join(os.getcwd(),"motioncor2_validation.json"), "w") as f:
    json.dump(finalValidationData,f)