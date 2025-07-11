from glob import glob
import re
import os
import json
import random

#Classic Appion logs use ANSI escape sequences to add colors.
#https://stackoverflow.com/a/38662876
def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)

log_glob=glob(os.path.join("./slurm_logs","h1","*","appion","*","ctf","ctffind4run*","slurm*.out"))
random.shuffle(log_glob)
logs=[]
for _ in range(8):
    logs.append(log_glob.pop())
validation={}
for log in logs:
    with open(log,"r") as f:
        txt=f.readlines()
    rundir=os.path.dirname(log)
    validation[rundir]=[]
    idx=0
    total_lines=len(txt)
    try:
        while txt:
            line=txt.pop(0)
            if line.startswith(" ... running ctf estimation "):
                inputs={}
                while not line.startswith(" ... ctf estimation completed in"):
                    splitline=line.split("=")
                    if len(splitline) > 1:
                        k=str(line.split("=")[0].strip())
                        v=str(line.split("=")[1].strip())
                        inputs[k]=v
                        if k == "newline":
                            break
                    line=txt.pop(0)
                    line=escape_ansi(line)
                validation[rundir].append(inputs)
            idx+=1
            if idx % 100 == 0:
                print("%d / %d : %s" % (idx, total_lines, log))
                print(validation.keys())
                if total_lines > 40000 and idx >= 40000:
                    break
    except Exception as e:
        print("Whoopsie: %s" % str(e))
        continue

with open("./ctffind4_validation_data.json", "w") as f:
    json.dump(validation, f)

                