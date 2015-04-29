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

for i in 288.5 266 304; do
    suffix=${i}_`date +%F-%T`
    task_spec_suffixed=${task_spec%-spec.yaml}-spec-${suffix}.yaml
    job=`python -c "
import os
os.chdir('INPUT')
from run_module import fileload, filedump
run_spec = fileload('${task_spec}')
run_spec['run_subdir'] += '-$i'
run_spec['poscar']['volume'] = $i
filedump(run_spec, '../${task_spec_suffixed}')
print run_spec['run_subdir']
    "`
    cp INPUT/deploy.job "$job"
    sed -i "/python/c python INPUT/${task}.py $task_spec_suffixed $other_args" "$job"
    qsub "$job"
    rm "$job"
done