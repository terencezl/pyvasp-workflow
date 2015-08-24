#!/bin/bash

# the shell style iterative submission deploy trigger, looping on a parameter to
# change the copied specs file.

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

for i in 288.5 266 304; do
    suffix=`date +%F-%T`_${i}
    task_specs_suffixed=${task_specs##*/}
    task_specs_suffixed=${task_specs_suffixed%.yaml}_${suffix}.yaml
    job=`python -c "
from os import chdir
chdir('INPUT')
from run_module import fileload, filedump, get_run_dir
chdir('..')
run_specs = fileload('${task_specs}')
# suffix the run directory and changing parameter
run_specs['run_dir'] += '-$i'
run_specs['poscar']['volume'] = $i
filedump(run_specs, '${task_specs_suffixed}')
print(get_run_dir(run_specs).replace('/', '-'))
    "`
    cp INPUT/deploy.job "$job"
    sed -i "/python/c python INPUT/${task}.py $task_specs_suffixed --remove_file" "$job"
    M "$job"
    rm "$job"
done
