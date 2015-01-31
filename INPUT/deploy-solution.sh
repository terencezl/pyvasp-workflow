#!/bin/bash
task="$1"
if [[ -z $task ]]; then
    echo "You must provide task name at least!"
    exit 1
fi
shift 1

# for ratio in 1.0-0.0 0.5-0.5 0.0-1.0; do
for ratio in 0.0-1.0; do
    job=$ratio
    suffix=${job}_`date +%F-%T`
    task_spec_suffixed=${task}-spec_${suffix}.yaml
    python -c "
import os
os.chdir('INPUT')
from run_module import fileload, filedump
run_spec = fileload('${task}-spec.yaml')
run_spec['run_subdir'] = '${job}/${task}'
run_spec['solution']['ratio'] = '$ratio'
run_spec['poscar']['template'] += '_$ratio'
filedump(run_spec, '../${task_spec_suffixed}')
    "
    cp INPUT/deploy.job $job
    sed -i "/python/c python INPUT/${task}.py $task_spec_suffixed $@" $job
    qsub $job
    rm $job
done
