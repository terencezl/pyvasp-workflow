#!/bin/bash
task="$1"
subdirname="$2"
if [[ -z $task || -z $subdirname ]]; then
    echo "You must provide task name and task directory name at least!"
    exit 1
fi
shift 2

for st in NiAs; do
    # for i in `cat INPUT/element.txt`; do
    # for i in Sc_sv Ti_sv V_sv Cr_pv Mn_pv Fe Co Ni Cu Zn  Y_sv Zr_sv Nb_sv Mo_pv Tc_pv Ru_pv Rh_pv Pd Ag Cd   Hf_pv Ta_pv W_pv Re Os Ir Pt Au; do
    for i in Mn_pv; do
        task_spec_suffixed=${task}_spec-${st}-${i}.yaml
        cp INPUT/${task}_spec.yaml $task_spec_suffixed
        python -c "
import os
os.chdir('INPUT')
from run_module import fileload, filedump
os.chdir('..')
filename = '$task_spec_suffixed'
run_spec = fileload(filename)
run_spec['structure'] = '$st'
run_spec['elem_types'] = ['$i', 'N']
run_spec['poscar']['template'] = 'POSCAR-${st}'
filedump(run_spec, filename)
        "
        job_suffixed=${st}-${i}
        cp INPUT/${task}.job $job_suffixed
        sed -i "/python/c python INPUT/${task}.py $task_spec_suffixed $subdirname $@" $job_suffixed
        qsub $job_suffixed
        rm $job_suffixed
    done
done
