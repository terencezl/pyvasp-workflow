#!/bin/bash
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
import sys
sys.path = ['$PWD/INPUT'] + sys.path
from run_module import fileload, filedump, get_run_dir
run_specs = fileload('${task_specs}')
filedump(run_specs, '${task_specs_suffixed}')
print(get_run_dir(run_specs).replace('/', '-') + '.job')
"`
cp INPUT/deploy.job "$job"
sed -i "/python/c python INPUT/${task}.py $task_specs_suffixed --remove_file" "$job"
M "$job"
rm "$job"
