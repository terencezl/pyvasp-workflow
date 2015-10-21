#!/bin/bash

# the shell style iterative submission deploy trigger, looping on a parameter to
# change the copied specs file. This is designed for the run_xxx-para.py routine
# scripts, which has another python level of parallel submission. It can also be
# used for the process_xxx-para.py process scripts.

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

for i in 40 50 60; do
    suffix=`date +%F-%T`_${i}
    task_specs_suffixed=${task_specs##*/}
    task_specs_suffixed=${task_specs_suffixed%.yaml}_${suffix}.yaml
    python -c "
import sys
sys.path = ['$PWD/INPUT'] + sys.path
from run_module import fileload, filedump, get_run_dir
run_specs = fileload('${task_specs}')
# suffix the run directory and changing parameter
run_specs['run_dir'] += '-$i'
run_specs['poscar']['volume'] = $i
filedump(run_specs, '${task_specs_suffixed}')
"
    python INPUT/${task}.py $task_specs_suffixed --remove_file
done
