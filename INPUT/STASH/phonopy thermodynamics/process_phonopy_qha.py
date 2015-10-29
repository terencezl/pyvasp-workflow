import os
from subprocess import call
import glob
import numpy as np
import run_module as rmd


if __name__ == '__main__':
    """

    Use phonopy to analyze each displacement run of each volume run.

    Not a VASP run script that requires a job submission. You can directly use
    it as

        INPUT/process_phonopy_qha.py INPUT/run_phonopy_qha.yaml

    to read a specs file at INPUT/run_phonopy_qha.yaml, which is the file you
    would use to actually run the routine script run_phonopy_qha-para.py before
    this.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))

    phonopy_dim = ' '.join(map(str, run_specs['phonopy']['dim']))
    phonopy_mp = ' '.join(map(str, run_specs['phonopy']['mp']))
    phonopy_tmax = str(run_specs['phonopy']['tmax'])
    phonopy_tstep = str(run_specs['phonopy']['tstep'])

    run_volume_dirname = run_specs['get_volumes_and_structures_from']\
        if 'get_volumes_and_structures_from' in run_specs else 'run_volume'

    if isinstance(run_volume_dirname, str):
        fitting_results = rmd.fileload(os.path.join('..',
            run_volume_dirname, 'fitting_results.json'))[-1]
        volume = fitting_results['volume']
        energy = fitting_results['energy']
    elif isinstance(run_volume_dirname, list):
        volume = []
        energy = []
        for dirname in run_volume_dirname:
            fitting_results = rmd.fileload(os.path.join('..',
                dirname, 'fitting_results.json'))[-1]
            volume.extend(fitting_results['volume'])
            energy.extend(fitting_results['energy'])

    volume, energy = np.array(sorted(zip(volume, energy))).T

    if not ('qha-only' in run_specs['phonopy'] and run_specs['phonopy']['qha-only']):
        for V in volume:
            rmd.chdir(str(np.round(V, 2)))
            if run_specs['phonopy']['mode'] == 'force_set':
                disp_dirs = sorted(glob.glob('disp-*'))
                disp_vasprun_xml = ' '.join([i + '/vasprun.xml' for i in disp_dirs])
                call('phonopy -f ' + disp_vasprun_xml + ' > /dev/null', shell=True)
                call('phonopy --mp="' + phonopy_mp + '" -tsp --dim="' + phonopy_dim +
                    '" --tmax=' + phonopy_tmax + ' --tstep=' + phonopy_tstep +
                    ' > /dev/null', shell=True)
            elif run_specs['phonopy']['mode'] == 'force_constant':
                call('phonopy --fc vasprun.xml > /dev/null 2>&1', shell=True)
                call('phonopy --readfc -c POSCAR_orig --mp="' + phonopy_mp +
                    '" -tsp --dim="' + phonopy_dim + '" --tmax=' + phonopy_tmax +
                    ' --tstep=' + phonopy_tstep + ' > /dev/null 2>&1', shell=True)
            os.chdir('..')

    # post processing
    e_v_dat = np.column_stack((volume, energy))
    np.savetxt('../e-v.dat', e_v_dat, '%15.6f', header='volume energy')
    thermal_properties = ' '.join([str(i) + '/thermal_properties.yaml' for i in np.round(volume, 2)])
    call('phonopy-qha ../e-v.dat ' + thermal_properties +
        ' -s --tmax=' + phonopy_tmax + ' > /dev/null', shell=True)
