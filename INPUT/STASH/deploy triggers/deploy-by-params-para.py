#!/bin/env python
import os
import shutil
import subprocess
import argparse
import datetime
from run_module import fileload, filedump, get_run_dir

parser = argparse.ArgumentParser(description='Copy the specs file from INPUT/ and directly run several copies of the routine script.')
parser.add_argument('routine', help='path of the Python routine file')
parser.add_argument('specs', help='path of the yaml specs file')
args = parser.parse_args()

for i in ['1.0', '0.5']:
    suffix = datetime.datetime.now().isoformat(sep='-')
    specs_suffixed = os.path.basename(args.specs).split('.yaml')[0] + '-' + str(i) + '_' + suffix + '.yaml'

    run_specs = fileload(args.specs)
    # suffix the run directory and changing parameter
    run_specs['run_dir'] += i
    run_specs['poscar']['template'] += i
    filedump(run_specs, specs_suffixed)
    job = get_run_dir(run_specs).replace('/', '-') + '.job'
    shutil.copy('INPUT/deploy.job', job)
    subprocess.call(' '.join(['python', args.routine, specs_suffixed, '--remove_file']), shell=True)
