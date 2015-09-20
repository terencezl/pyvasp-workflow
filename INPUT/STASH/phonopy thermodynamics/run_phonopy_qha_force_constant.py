import os
from subprocess import call
import glob
import numpy as np
import run_module as rmd
import pymatgen as mg


if __name__ == '__main__':
    """

    Run the phonopy qha force constant calculation for a volume range obtained
    by a VASP routine run_volume.py. It'll get the volume, energy and structures
    at different volumes from ../run_volume/fitting_results.json.

    You should set a 'phonopy' tag in the specs file like

        phonopy:
          dim: [2, 2, 2]
          mp: [31, 31, 31]
          tmax: 1400
          tstep: 5

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)

    phonopy_dim = ' '.join(map(str, run_specs['phonopy']['dim']))
    phonopy_mp = ' '.join(map(str, run_specs['phonopy']['mp']))
    phonopy_tmax = str(run_specs['phonopy']['tmax'])
    phonopy_tstep = str(run_specs['phonopy']['tstep'])
    incar = rmd.read_incar(run_specs)
    if os.path.isfile('../properties.json'):
        properties = rmd.fileload('../properties.json')
        if 'ISPIN' not in incar:
            if rmd.detect_is_mag(properties['mag']):
                incar.update({'ISPIN': 2})
            else:
                incar.update({'ISPIN': 1})

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = rmd.get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = rmd.read_kpoints(run_specs, structure)

    fitting_results = rmd.fileload('../run_volume/fitting_results.json')[-1]
    volume = np.round(np.array(fitting_results['volume']), 2)
    structures = fitting_results['structures']

    for V, st in zip(volume, structures):
        rmd.chdir(str(V))
        rmd.init_stdout()
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        structure = mg.Structure.from_dict(st)
        structure.to(filename='POSCAR')
        call('phonopy -d --dim="' + phonopy_dim + '" > /dev/null', shell=True)
        os.rename('POSCAR', 'POSCAR_orig')
        os.rename('SPOSCAR', 'POSCAR')
        os.remove('disp.yaml')
        for f in glob.glob('POSCAR-*'):
            os.remove(f)
        rmd.write_potcar(run_specs)
        rmd.run_vasp()
        call('phonopy --fc vasprun.xml > /dev/null 2>&1', shell=True)
        call('phonopy --readfc -c POSCAR_orig --mp="' + phonopy_mp + '" -tsp --dim="' + phonopy_dim + '" --tmax=' + phonopy_tmax + ' --tstep=' + phonopy_tstep + ' > /dev/null 2>&1', shell=True)
        os.chdir('..')

    # post processing
    fitting_results = rmd.fileload('../run_volume/fitting_results.json')[-1]
    e_v_dat = np.column_stack((fitting_results['volume'], fitting_results['energy']))
    np.savetxt('../e-v.dat', e_v_dat, '%15.6f', header='volume energy')
    thermal_properties = ' '.join([str(i) + '/thermal_properties.yaml' for i in volume])
    call('phonopy-qha ../e-v.dat ' + thermal_properties + ' --tmax=' + phonopy_tmax + ' > /dev/null 2>&1', shell=True)
