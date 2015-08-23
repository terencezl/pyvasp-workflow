import os
import sys
import shutil
from subprocess import call
import glob
import numpy as np
from run_module import *
import pymatgen as mg


if __name__ == '__main__':
    """

    Needs run_volume first. Specifically, needs
    ../run_volume/fitting_results.json.

    """

    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    phonopy_dim = ' '.join(map(str, run_spec['phonopy']['dim']))
    cwd = os.getcwd()
    enter_main_dir(run_spec)
    filedump(run_spec, filename)

    incar = read_incar(run_spec)
    if os.path.isfile('../properties.json'):
        properties = fileload('../properties.json')
        if 'ISPIN' not in incar:
            if detect_is_mag(properties['mag']):
                incar.update({'ISPIN': 2})
            else:
                incar.update({'ISPIN': 1})

    # higher priority for run_spec
    if 'poscar' in run_spec:
        structure = generate_structure(run_spec)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = read_kpoints(run_spec, structure)

    fitting_results = fileload('../run_volume/fitting_results.json')[-1]
    volume = np.round(np.array(fitting_results['volume']), 2)
    structures = fitting_results['structures']

    for V, st in zip(volume, structures):
        chdir(str(V))
        structure = mg.Structure.from_dict(st)
        structure.to(filename='POSCAR')
        call('phonopy -d --dim="' + phonopy_dim + '" > /dev/null', shell=True)
        os.remove('SPOSCAR')
        disp_structures = sorted(glob.glob('POSCAR-*'))
        disp_dirs = ['disp-' + i.split('POSCAR-')[1] for i in disp_structures]

        for disp_d, disp_p in zip(disp_dirs, disp_structures):
            chdir(disp_d)
            init_stdout()
            shutil.move('../' + disp_p, 'POSCAR')
            incar.write_file('INCAR')
            kpoints.write_file('KPOINTS')
            write_potcar(run_spec)
            job = str(V) + '-' + disp_d
            shutil.copy(cwd + '/INPUT/deploy.job', job)
            call('sed -i "/python/c time ' + VASP_EXEC + ' 2>&1 | tee -a stdout" ' + job, shell=True)
            call('M ' + job, shell=True)
            os.remove(job)
            os.chdir('..')
        os.chdir('..')
