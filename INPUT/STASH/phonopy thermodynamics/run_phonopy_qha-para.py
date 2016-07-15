import os
import shutil
from subprocess import call
import glob
import numpy as np
import run_module as rmd
import pymatgen as mg


if __name__ == '__main__':
    """

    Run the phonopy qha force set calculation for a volume range obtained by a
    VASP routine run_volume.py in python level parallel submission mode. It'll
    get the volume, energy and structures at different volumes from the last
    iteraton of  ../run_volume/fitting_results.json.

    You should set a 'phonopy' tag in the specs file like

        phonopy:
          mode: force_set (or force_constant)
          dim: [2, 2, 2]
          mp: [31, 31, 31]
          tmax: 1400
          tstep: 5

    Optionally, if you set a 'volumes_and_structures' tag under the tag
    'phonopy', and a 'from' tag under it, like

        phonopy:
          volumes_and_structures:
            from: run_volume

    the last iteration in the fitting_results.json from that directory will be
    used. If that is set to a list of directory names, the volumes and
    structures will be concatenated and sorted according to the volume value.

    If you set a 'slice' tag in the under the tag 'phonopy', like

        phonopy:
          volumes_and_structures:
            slice: [null, -4]

    The slice is applied to the volume and structure list.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    cwd = os.getcwd()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)

    phonopy_specs = run_specs['phonopy']
    phonopy_specs['dim'] = ' '.join(map(str, phonopy_specs['dim']))

    rmd.infer_from_json(run_specs)
    structure = rmd.get_structure(run_specs)
    incar = rmd.read_incar(run_specs)
    kpoints = rmd.read_kpoints(run_specs, structure)

    run_volume_dirname = phonopy_specs['volumes_and_structures']['from']\
        if 'volumes_and_structures' in phonopy_specs and \
           'from' in phonopy_specs['volumes_and_structures'] and \
           phonopy_specs['volumes_and_structures']['from'] else 'run_volume'

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

    idx_slice = phonopy_specs['volumes_and_structures']['slice'] if \
        'volumes_and_structures' in phonopy_specs and \
        'slice' in phonopy_specs['volumes_and_structures'] and \
        phonopy_specs['volumes_and_structures']['slice'] else [None] * 2

    volume, energy, structures = np.array(sorted(zip(volume, energy, structures)))[idx_slice[0]:idx_slice[1]].T

    for V, st in zip(volume, structures):
        rmd.chdir(str(np.round(V, 2)))
        if run_specs['phonopy']['mode'] == 'force_set':
            structure = mg.Structure.from_dict(st)
            structure.to(filename='POSCAR')
            call('phonopy -d --dim="' + phonopy_specs['dim'] + '" > /dev/null', shell=True)
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
                job = str(V) + '-' + disp_d
                shutil.copy(cwd + '/INPUT/deploy.job', job)
                call('sed -i "/python/c time ' + rmd.VASP_EXEC + ' 2>&1 | tee -a stdout" ' + job, shell=True)
                call('M ' + job, shell=True)
                os.remove(job)
                os.chdir('..')
        elif run_specs['phonopy']['mode'] == 'force_constant':
            rmd.init_stdout()
            incar.write_file('INCAR')
            kpoints.write_file('KPOINTS')
            structure = mg.Structure.from_dict(st)
            structure.to(filename='POSCAR')
            call('phonopy -d --dim="' + phonopy_specs['dim'] + '" > /dev/null', shell=True)
            os.rename('POSCAR', 'POSCAR_orig')
            os.rename('SPOSCAR', 'POSCAR')
            os.remove('disp.yaml')
            for f in glob.glob('POSCAR-*'):
                os.remove(f)
            rmd.write_potcar(run_specs)
            job = str(V)
            shutil.copy(cwd + '/INPUT/deploy.job', job)
            call('sed -i "/python/c time ' + rmd.VASP_EXEC + ' 2>&1 | tee -a stdout" ' + job, shell=True)
            call('M ' + job, shell=True)
            os.remove(job)
        os.chdir('..')
