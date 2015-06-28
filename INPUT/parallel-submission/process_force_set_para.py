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
    properties = fileload('../properties.json')
    volume = np.round(np.array(properties['volume']), 2)

    for V in volume:
        chdir(str(V))
        disp_dirs = sorted(glob.glob('disp-*'))
        disp_vasprun_xml = ' '.join([i + '/vasprun.xml' for i in disp_dirs])
        call('phonopy -f ' + disp_vasprun_xml + ' > /dev/null 2>&1', shell=True)
        call('phonopy --mp="' + phonopy_mp + '" -tsp --dim="' + phonopy_dim + '" --tmax=' + phonopy_tmax + ' --tstep=' + phonopy_tstep + ' > /dev/null 2>&1', shell=True)
        os.chdir('..')

    # post processing
    thermal_properties = ' '.join([str(i) + '/thermal_properties.yaml' for i in volume])
    call('phonopy-qha ../e-v.dat ' + thermal_properties + ' --tmax=' + phonopy_tmax + ' > /dev/null 2>&1', shell=True)
    # gibbs = np.loadtxt('gibbs-temperature.dat').T.tolist()
    # properties['gibbs'] = gibbs
    # filedump(properties, '../properties.json')
