#!/bin/bash
task="$1"
if [[ -z $task ]]; then
    echo "You must provide task name at least!"
    exit 1
fi
shift 1

for i in 7 9 11 13 15 17 19 21 23; do
    # for j in 6 12; do
        job=$i
        suffix=$i_`date +%F-%T`
        task_spec_suffixed=${task}-spec_${suffix}.yaml
        python -c "
import os
os.chdir('INPUT')
from run_module import fileload, filedump
run_spec = fileload('${task}-spec.yaml')
run_spec['run_subdir'] = '${task}_${suffix}'
run_spec['kpoints']['divisions'] = [$i, $i, $i]
filedump(run_spec, '../${task_spec_suffixed}')
        "
        cp INPUT/deploy.job $job
        sed -i "/python/c python INPUT/${task}.py $task_spec_suffixed $@" $job
        qsub $job
        rm $job
    # done
done
