#!/bin/bash

# another example of the shell style iterative submission deploy trigger,
# looping on the structure and element to change the copied specs file.

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

for st in NiAs WC; do
    for elem in Mn_pv Fe Co; do
        suffix=`date +%F-%T`_${st}-${elem}
        task_specs_suffixed=${task_specs##*/}
        task_specs_suffixed=${task_specs_suffixed%.yaml}_${suffix}.yaml
        job=`python -c "
import sys
sys.path = ['$PWD/INPUT'] + sys.path
from run_module import fileload, filedump, get_run_dir
run_specs = fileload('${task_specs}')
# suffix the run directory and changing parameter
run_specs['structure'] = '$st'
run_specs['elem_types'] = ['$elem', 'N']
run_specs['poscar']['template'] = 'POSCAR-${st}'
filedump(run_specs, '${task_specs_suffixed}')
print(get_run_dir(run_specs).replace('/', '-') + '.job')
        "`
        cp INPUT/deploy.job "$job"
        sed -i "/python/c python INPUT/${task}.py $task_specs_suffixed --remove_file" "$job"
        M $job
        rm $job
    done
done
