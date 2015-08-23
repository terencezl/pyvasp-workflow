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

for st in NiAs WC; do
    for elem in Mn_pv Fe Co; do
        suffix=`date +%F-%T`_${st}-${elem}
        task_spec_suffixed=${task_spec##*/}
        task_spec_suffixed=${task_spec_suffixed%.yaml}_${suffix}.yaml
        job=`python -c "
from os import chdir
chdir('INPUT')
from run_module import fileload, filedump, get_run_dir
chdir('..')
run_spec = fileload('${task_spec}')
# suffix the run directory and changing parameter
run_spec['structure'] = '$st'
run_spec['elem_types'] = ['$elem', 'N']
run_spec['poscar']['template'] = 'POSCAR-${st}'
filedump(run_spec, '${task_spec_suffixed}')
print(get_run_dir(run_spec).replace('/', '-'))
        "`
        cp INPUT/deploy.job "$job"
        sed -i "/python/c python INPUT/${task}.py $task_spec_suffixed --remove_file" "$job"
        M $job
        rm $job
    done
done
