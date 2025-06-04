#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 New York Structural Biology Center

from jinja2 import Environment, FileSystemLoader
import os
import subprocess
import sys
from argparse import ArgumentParser

def sbatch(batch_script_path : str):
    if os.path.exists(batch_script_path):
        proc=subprocess.run("sbatch {batch_script_path}", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, text=True, encoding="utf-8")
        return proc.stdout
    return None

def renderJobScript(rundir: str, template_dir : str, template_file : str, command : str):
    batch_script_path = os.path.join(rundir, "batch.sh")
    with open(batch_script_path, "w") as jobFile:
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_file)
        jobFile.write(template.render(command=command))
    return batch_script_path

def main():
    cmd=sys.argv[0]
    # If there's a wrapper we need to remove the wrapper from the command name before rendering the command in the template.
    # https://github.com/nysbc/leginon/blob/89218b54616e4f9e586b05c909708e199ea54106/myamiweb/processing/inc/processing.inc#L879-L883
    # The simplest way to avoid this nonsense is to set USE_APPION_WRAPPER to false in myamiweb's config.php.
    if "APPION_WRAPPER" in os.environ.keys():
        appion_wrapper=os.environ["APPION_WRAPPER"]
        cmd=appion_wrapper.split(cmd)
        cmd=cmd[-1]
        cmd=cmd.split()
    else:
        # Omit runJob.py
        cmd=cmd[1:]
    args=ArgumentParser(args=cmd)
    template_dir=os.environ.get("APPION_TEMPLATE_DIR","/etc/appion/templates")
    template_file="slurm_job.sh.j2"
    batch_script_path = renderJobScript(args.rundir, template_dir, template_file, " ".join(cmd))
    stdout = sbatch(batch_script_path)
    print(stdout)

if __name__ == '__main__':
    main()