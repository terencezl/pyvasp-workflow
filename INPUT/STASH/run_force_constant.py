import os
import sys
import shutil
from subprocess import call
import glob
import numpy as np
from run_modules import *
import pymatgen as mg


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    phonopy_dim = ' '.join(map(str, run_spec['phonopy']['dim']))
    phonopy_mp = ' '.join(map(str, run_spec['phonopy']['mp']))
    phonopy_tmax = str(run_spec['phonopy']['tmax'])
    phonopy_tstep = str(run_spec['phonopy']['tstep'])

    enter_main_dir(run_spec)
    filedump(run_spec, filename)

    # for solution runs
    if run_spec.has_key('solution') and run_spec['solution'].has_key('ratio'):
        ratio = str(run_spec['solution']['ratio'])
        ratio_list = [float(i) for i in ratio.split('-')]
        if ratio_list[0] == 0 and ratio_list[1] == 1:
            run_spec['elem_types'] = [run_spec['elem_types'][1], run_spec['elem_types'][2]]
        elif ratio_list[0] == 1 and ratio_list[1] == 0:
            run_spec['elem_types'] = [run_spec['elem_types'][0], run_spec['elem_types'][2]]

    incar = read_incar(run_spec)
    kpoints = read_kpoints(run_spec)
    properties = fileload('../properties.json')
    if detect_is_mag(properties['mag']):
        incar.update({'ISPIN': 2})
    else:
        incar.update({'ISPIN': 1})
    volume = np.round(np.array(properties['volume']), 2)
    poscars = properties['poscars']

    for V, poscar in zip(volume, poscars):
        chdir(str(V))
        rm_stdout()
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        structure = mg.Structure.from_dict(poscar)
        structure.to(filename='POSCAR')
        call('phonopy -d --dim="' + phonopy_dim + '" > /dev/null', shell=True)
        os.rename('POSCAR', 'POSCAR_orig')
        os.rename('SPOSCAR', 'POSCAR')
        os.remove('disp.yaml')
        for f in glob.glob('POSCAR-*'):
            os.remove(f)
        write_potcar(run_spec)
        run_vasp()
        call('phonopy --fc vasprun.xml > /dev/null 2>&1', shell=True)
        call('phonopy --readfc -c POSCAR_orig --mp="' + phonopy_mp + '" -tsp --dim="' + phonopy_dim + '" --tmax=' + phonopy_tmax + ' --tstep=' + phonopy_tstep + ' > /dev/null 2>&1', shell=True)
        os.chdir('..')

    # post processing
    thermal_properties = ' '.join([str(i) + '/thermal_properties.yaml' for i in volume])
    call('phonopy-qha ../e-v.dat ' + thermal_properties + ' --tmax=' + phonopy_tmax + ' > /dev/null 2>&1', shell=True)
    # gibbs = np.loadtxt('gibbs-temperature.dat').T.tolist()
    # properties['gibbs'] = gibbs
    # filedump(properties, '../properties.json')
