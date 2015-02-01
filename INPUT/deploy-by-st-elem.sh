#!/bin/bash
task="$1"
subdirname="$2"
if [[ -z $task ]]; then
    echo "You must provide task name at least!"
    exit 1
fi
shift 1

if [[ "$1" ]]; then
    task_spec="$1"-spec.yaml
    shift 1
else
    task_spec=${task}-spec.yaml
fi

other_args="$@"

for st in NiAs WC; do
    # for i in `cat INPUT/element.txt`; do
    # for i in Sc_sv Ti_sv V_sv Cr_pv Mn_pv Fe Co Ni Cu Zn  Y_sv Zr_sv Nb_sv Mo_pv Tc_pv Ru_pv Rh_pv Pd Ag Cd   Hf_pv Ta_pv W_pv Re Os Ir Pt Au; do
    # for i in Ti_sv V_sv Cr_pv Fe Co Ni Cu   Y_sv Zr_sv Nb_sv Mo_pv Tc_pv Ru_pv Rh_pv Pd Ag Cd   Hf_pv Ta_pv W_pv Re Os Ir Pt Au; do
    # for i in Ni Tc_pv Rh_pv Pd Ag Ir Pt Au; do
    # for i in Rh_pv Pd Ag Os Ir Pt Au; do
    for elem in Mn_pv Fe Co; do
        job=${st}-${elem}
        suffix=${job}_`date +%F-%T`
        task_spec_suffixed=${task_spec%-spec.yaml}-spec-${suffix}.yaml
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
        qsub $job
        rm $job
    done
done
