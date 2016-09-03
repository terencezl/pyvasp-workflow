from subprocess import call
import glob
import run_module as rmd


if __name__ == '__main__':
    """

    Use phonopy to analyze each displacement run of each volume run.

    Not a VASP run script that requires a job submission. You can directly use
    it as

        INPUT/process_phonopy.py INPUT/run_phonopy.yaml

    to read a specs file at INPUT/run_phonopy.yaml, which is the file you would
    use to actually run the routine script run_phonopy-para.py before this.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))

    phonopy_dim = ' '.join(map(str, run_specs['phonopy']['dim']))
    phonopy_mp = ' '.join(map(str, run_specs['phonopy']['mp']))
    phonopy_tmax = str(run_specs['phonopy']['tmax'])
    phonopy_tstep = str(run_specs['phonopy']['tstep'])

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
