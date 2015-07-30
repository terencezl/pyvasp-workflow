#!/bin/bash
task="$1"
if [[ -z $task ]]; then
    echo "You must provide task name at least!"
    exit 1
fi
shift 1

if [[ "$1" && "$1" != - ]]; then
    task_spec="$1"
    shift 1
else
    task_spec=${task}.yaml
fi

other_args="$@"

for st in NiAs WC; do
    for elem in Mn_pv Fe Co; do
        job=${st}-${elem}
        suffix=${job}_`date +%F-%T`
        task_spec_suffixed=${task_spec%.yaml}-${suffix}.yaml
        python -c "
import os
os.chdir('INPUT')
from run_module import fileload, filedump
run_spec = fileload('${task_spec}')
run_spec['structure'] = '$st'
run_spec['elem_types'] = ['$elem', 'N']
run_spec['poscar']['template'] = 'POSCAR-${st}'
filedump(run_spec, '../${task_spec_suffixed}')
        "
        cp INPUT/deploy.job $job
        sed -i "/python/c python INPUT/${task}.py $task_spec_suffixed $other_args" $job
        M $job
        rm $job
    done
done
