import subprocess

def readMotionCorVersion(cmd):
    cmd=[cmd]
    cmd.append("--version")
    proc=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, text=True, encoding="utf-8")
    output=proc.stdout
    output=output.split("\n")
    version=None
    for line in output:
        if line.strip().startswith("MotionCor"):
            version=line.strip()
    return version