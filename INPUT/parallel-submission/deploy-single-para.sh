#!/bin/bash
task="$1"
if [[ -z $task ]]; then
    echo "You must provide task name at least!"
    exit 1
fi
shift 1

if [[ "$1" ]]; then
    task_spec="$1"
    shift 1
else
    task_spec=${task}-spec.yaml
fi

other_args="$@"

job=$task
suffix=`date +%F-%T`
task_spec_suffixed=${task_spec%-spec.yaml}-spec_${suffix}.yaml
python -c "
import os
os.chdir('INPUT')
from run_module import fileload, filedump
run_spec = fileload('${task_spec}')
filedump(run_spec, '../${task_spec_suffixed}')
"
python INPUT/${task}.py $task_spec_suffixed $other_args
