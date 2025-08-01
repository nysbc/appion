#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center

from jinja2 import Environment, FileSystemLoader
import os
import subprocess
import sys
from shutil import which
import copy

def sbatch(batch_script_path : str):
    if os.path.exists(batch_script_path):
        cmd=which("sbatch")
        if not cmd:
            return None
        proc=subprocess.run([cmd, batch_script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, text=True, encoding="utf-8")
        return proc.stdout
    return None

def renderJobScript(rundir: str, template_dir : str, template_file : str, command : str):
    if not os.path.exists(rundir):
        os.makedirs(rundir)
    batch_script_path = os.path.join(rundir, "batch.sh")
    with open(batch_script_path, "w") as jobFile:
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_file)
        jobFile.write(template.render(command=command))
    return batch_script_path

def main():
    template_dir=os.environ.get("APPION_TEMPLATE_DIR","/etc/appion/templates")
    template_file=os.environ.get("APPION_JOB_TEMPLATE","slurm_job.sh.j2")
    appion_wrapper_path=os.environ.get("APPION_WRAPPER_PATH",None)
    remove_flags=["--ppn", "--nodes", "--walltime", "--queue"] 
    cmd=copy.deepcopy(sys.argv)
    cmd_record=copy.deepcopy(sys.argv)
    rundir=""
    cmd_str=""
    cmd.pop(0)
    while cmd:
        cmd_token=cmd.pop(0)
        if "=" in cmd_token:
            cmd_token_split=cmd_token.split("=")
            if len(cmd_token_split) > 1:
                if cmd_token_split[0] in ["--rundir", "--outdir", "-R"]:
                    rundir=cmd_token_split[1]
                if cmd_token_split[0] in remove_flags:
                    continue
        if appion_wrapper_path:
            if cmd_token.strip() != appion_wrapper_path.strip():
                cmd_str+=" %s" % cmd_token.strip()
        else:
            cmd_str+=" %s" % cmd_token.strip()
    if not rundir:
        raise RuntimeError("Could not find rundir argument")
    batch_script_path = renderJobScript(rundir, template_dir, template_file, cmd_str)
    if not os.path.exists(rundir):
        os.makedirs(rundir)
    os.chdir(rundir)
    with open(os.path.join(rundir,"run_command.txt"), "a") as f:
        f.write(" ".join(cmd_record) + "\n")
    stdout = sbatch(batch_script_path)
    sys.stdout.write((stdout.replace("Submitted batch job ","")))
    sys.stdout.flush()

if __name__ == '__main__':
    main()
