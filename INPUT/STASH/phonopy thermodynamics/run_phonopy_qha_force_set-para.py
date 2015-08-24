import os
import shutil
from subprocess import call
import glob
import numpy as np
from run_module import *
import pymatgen as mg


if __name__ == '__main__':
    """

    Run the phonopy qha force set calculation for a volume range obtained by a
    VASP routine run_volume.py in python level parallel submission mode. It'll
    get the volume, energy and structures at different volumes from
    ../run_volume/fitting_results.json.

    You should set a 'phonopy' tag in the specs file like

        phonopy:
          dim: [2, 2, 2]
          mp: [31, 31, 31]
          tmax: 1400
          tstep: 5

    """

    run_specs, filename = get_run_specs_and_filename()
    cwd = os.getcwd()
    chdir(get_run_dir(run_specs))
    filedump(run_specs, filename)

    phonopy_dim = ' '.join(map(str, run_specs['phonopy']['dim']))
    incar = read_incar(run_specs)
    if os.path.isfile('../properties.json'):
        properties = fileload('../properties.json')
        if 'ISPIN' not in incar:
            if detect_is_mag(properties['mag']):
                incar.update({'ISPIN': 2})
            else:
                incar.update({'ISPIN': 1})

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = read_kpoints(run_specs, structure)

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
            write_potcar(run_specs)
            job = str(V) + '-' + disp_d
            shutil.copy(cwd + '/INPUT/deploy.job', job)
            call('sed -i "/python/c time ' + VASP_EXEC + ' 2>&1 | tee -a stdout" ' + job, shell=True)
            call('M ' + job, shell=True)
            os.remove(job)
            os.chdir('..')
        os.chdir('..')
