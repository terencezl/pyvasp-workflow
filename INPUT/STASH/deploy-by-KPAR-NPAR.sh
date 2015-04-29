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

# for i in 1,1 1,2 1,4 1,6 1,12 2,1 2,2 2,3 2,4 3,1 3,2 3,4 3,8 4,1 4,2 4,3 4,6 6,1 6,2 6,4; do
for i in 12,1 12,2; do
    OLDIFS=$IFS; IFS=',';
    set $i; KPAR=$1; NPAR=$2
    IFS=$OLDIFS
    job=${KPAR}-${NPAR}
    suffix=${job}_`date +%F-%T`
    task_spec_suffixed=${task_spec%-spec.yaml}-spec-${suffix}.yaml
    job=`python -c "
import os
os.chdir('INPUT')
from run_module import fileload, filedump
run_spec = fileload('${task_spec}')
run_spec['run_subdir'] += '-${job}'
run_spec['incar']['KPAR'] = $KPAR
run_spec['incar']['NPAR'] = $NPAR
filedump(run_spec, '../${task_spec_suffixed}')
print run_spec['run_subdir']
    "`
    cp INPUT/deploy.job "$job"
    sed -i "/python/c python INPUT/${task}.py $task_spec_suffixed $other_args" "$job"
    qsub "$job"
    rm "$job"
done


# for i in 1,1 1,2 1,4 1,6 1,12 2,1 2,2 2,3 2,4 3,1 3,2 3,4 3,8 4,1 4,2 4,3 4,6 6,1 6,2 6,4; do
#     OLDIFS=$IFS; IFS=',';
#     set $i; KPAR=$1; NPAR=$2
#     IFS=$OLDIFS
#     job=${KPAR}-${NPAR}
#     echo -e "$job \c"
#     grep walltime ${job}.* | cut -d= -f2
# done 2>&1 | grep -v grep > walltime.txt

# data = pd.read_table('walltime.txt', header=None, sep='\t')
# ind = pd.MultiIndex.from_tuples([map(int, i.split('-')) for i in data[0]], names=['KPAR','NPAR'])
# data.index =ind
# data.drop(0,axis=1, inplace=True)
# data.columns =['walltime']