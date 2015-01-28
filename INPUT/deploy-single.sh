#!/bin/bash
task="$1"
if [[ -z $task ]]; then
    echo "You must provide task name at least!"
    exit 1
fi
shift 1

suffix=`date +%F-%T`
task_spec_suffixed=${task}-spec_$suffix.yaml
python -c "
import os
os.chdir('INPUT')
from run_module import fileload, filedump
run_spec = fileload('${task}-spec.yaml')
filedump(run_spec, '../${task_spec_suffixed}')
"
cp INPUT/deploy.job $task
sed -i "/python/c python INPUT/${task}.py $task_spec_suffixed $@" $task
qsub $task
rm $task