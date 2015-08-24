#!/bin/bash

# This is designed for the run_xxx-para.py routine scripts, which has a python
# level of parallel submission. But for a single call, this file is optional,
# because you can always do
#
#   INPUT/run_xxx-para.py INPUT/run_xxx.yaml

task="$1"
if [[ -z $task ]]; then
    echo "You must provide task name at least!"
    exit 1
fi
shift 1

if [[ "$1" && "$1" != - ]]; then
    task_specs="$1"
    shift 1
else
    task_specs=INPUT/${task}.yaml
fi

suffix=`date +%F-%T`
task_specs_suffixed=${task_specs##*/}
task_specs_suffixed=${task_specs_suffixed%.yaml}_${suffix}.yaml
job=`python -c "
from os import chdir
chdir('INPUT')
from run_module import fileload, filedump, get_run_dir
chdir('..')
run_specs = fileload('${task_specs}')
filedump(run_specs, '${task_specs_suffixed}')
print(get_run_dir(run_specs).replace('/', '-'))
"`
python INPUT/${task}.py $task_specs_suffixed --remove_file
