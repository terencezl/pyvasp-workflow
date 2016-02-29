#!/bin/env python
import os
import shutil
import subprocess
import argparse
import datetime
from run_module import fileload, filedump, get_run_dir

parser = argparse.ArgumentParser(description='Copy the specs file from INPUT/ and submit the job to the queue.')
parser.add_argument('routine', help='path of the Python routine file')
parser.add_argument('specs', help='path of the yaml specs file')
args = parser.parse_args()

suffix = datetime.datetime.now().isoformat(sep='-')
specs_suffixed = os.path.basename(args.specs).split('.yaml')[0] + '_' + suffix + '.yaml'

run_specs = fileload(args.specs)
filedump(run_specs, specs_suffixed)
job = get_run_dir(run_specs).replace('/', '-') + '.job'
shutil.copy('INPUT/deploy.job', job)
subprocess.call(' '.join(['sed -i "/python/c python', args.routine, specs_suffixed, '--remove_file"', job]), shell=True)
subprocess.call('M ' + job, shell=True)
os.remove(job)
