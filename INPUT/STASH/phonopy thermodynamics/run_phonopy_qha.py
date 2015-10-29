import os

import shutil
from subprocess import call
import glob
import numpy as np
import run_module as rmd
import pymatgen as mg


if __name__ == '__main__':
    """

    ============================================================================
    THIS EXISTS JUST AS A REFERENCE. Because calculations at different volumes
    can be simply parallelized, you'll almost always want to take advantage of
    that, by choosing run_phonopy_qha_para.py and process_phonopy_qha.py.
    ============================================================================

    Run the phonopy qha force set calculation for a volume range obtained by a
    VASP routine run_volume.py. It'll get the volume, energy and structures at
    different volumes from the last iteraton of
    ../run_volume/fitting_results.json.

    Optionally, if you set a 'get_volumes_and_structures_from' tag in the specs
    file like

        get_volumes_and_structures_from: run_volume-special

    and the last iteration in the fitting_results.json from that directory will
    be used. If that is set to a list of directory names, the volumes and
    structures will be concatenated.

    You should set a 'phonopy' tag in the specs file like

        phonopy:
          mode: force_set (or force_constant)
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

    run_volume_dirname = run_specs['get_volumes_and_structures_from']\
        if 'get_volumes_and_structures_from' in run_specs else 'run_volume'

    if isinstance(run_volume_dirname, str):
        fitting_results = rmd.fileload(os.path.join('..',
            run_volume_dirname, 'fitting_results.json'))[-1]
        volume = fitting_results['volume']
        energy = fitting_results['energy']
        structures = fitting_results['structures']
    elif isinstance(run_volume_dirname, list):
        volume = []
        energy = []
        structures = []
        for dirname in run_volume_dirname:
            fitting_results = rmd.fileload(os.path.join('..',
                dirname, 'fitting_results.json'))[-1]
            volume.extend(fitting_results['volume'])
            energy.extend(fitting_results['energy'])
            structures.extend(fitting_results['structures'])

    volume, energy = np.array(sorted(zip(volume, energy))).T

    for V, st in zip(volume, structures):
        rmd.chdir(str(np.round(V, 2)))
        if run_specs['phonopy']['mode'] == 'force_set':
            structure = mg.Structure.from_dict(st)
            structure.to(filename='POSCAR')
            call('phonopy -d --dim="' + phonopy_dim + '" > /dev/null', shell=True)
            os.remove('SPOSCAR')
            disp_structures = sorted(glob.glob('POSCAR-*'))
            disp_dirs = ['disp-' + i.split('POSCAR-')[1] for i in disp_structures]
            for disp_d, disp_p in zip(disp_dirs, disp_structures):
                rmd.chdir(disp_d)
                rmd.init_stdout()
                shutil.move('../' + disp_p, 'POSCAR')
                incar.write_file('INCAR')
                kpoints.write_file('KPOINTS')
                rmd.write_potcar(run_specs)
                rmd.run_vasp()
                os.chdir('..')
            disp_vasprun_xml = ' '.join([i + '/vasprun.xml' for i in disp_dirs])
            call('phonopy -f ' + disp_vasprun_xml + ' > /dev/null', shell=True)
            call('phonopy --mp="' + phonopy_mp + '" -tsp --dim="' + phonopy_dim +
                '" --tmax=' + phonopy_tmax + ' --tstep=' + phonopy_tstep +
                ' > /dev/null', shell=True)
        elif run_specs['phonopy']['mode'] == 'force_constant':
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
            call('phonopy --fc vasprun.xml > /dev/null', shell=True)
            call('phonopy --readfc -c POSCAR_orig --mp="' + phonopy_mp +
                '" -tsp --dim="' + phonopy_dim + '" --tmax=' + phonopy_tmax +
                ' --tstep=' + phonopy_tstep + ' > /dev/null', shell=True)
        os.chdir('..')

    # post processing
    e_v_dat = np.column_stack((volume, energy))
    np.savetxt('../e-v.dat', e_v_dat, '%15.6f', header='volume energy')
    thermal_properties = ' '.join([str(i) + '/thermal_properties.yaml' for i in np.round(volume, 2)])
    call('phonopy-qha ../e-v.dat ' + thermal_properties +
        ' -s --tmax=' + phonopy_tmax + ' > /dev/null', shell=True)
