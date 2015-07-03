import os
import sys
import shutil
import numpy as np
from run_module import *
import matplotlib.pyplot as plt
import pymatgen as mg
import pydass_vasp


def volume_fitting(run_spec, (incar, kpoints, poscars), is_mag, fitting_results):
    volume = np.zeros(len(poscars))
    energy = np.zeros(len(poscars))
    mag = np.zeros(len(poscars))
    for i, p in enumerate(poscars):
        structure = mg.Structure.from_dict(p)
        chdir(str(np.round(structure.volume, 2)))
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        structure.to(filename='POSCAR')
        write_potcar(run_spec)
        run_vasp()
        oszicar = mg.io.vaspio.Oszicar('OSZICAR')
        volume[i] = structure.volume
        energy[i] = oszicar.final_energy
        if is_mag:
            mag[i] = oszicar.ionic_steps[-1]['mag']
        os.chdir('..')

    # dump in case error in fitting
    fitting_results.append({'volume': volume.tolist(), 'energy': energy.tolist(), 'mag': mag.tolist(), 'poscars': poscars})
    filedump(fitting_results, 'fitting_results.json')
    # plot in case error in fitting
    plt.plot(volume, energy, 'o')
    plt.tight_layout()
    plt.savefig('eos_fit.pdf')
    plt.close()
    # fitting
    fitting_result_raw = pydass_vasp.fitting.eos_fit(volume, energy, save_figs=True)
    fitting_results[-1]['params'] = fitting_result_raw['params']
    fitting_results[-1]['r_squared'] = fitting_result_raw['r_squared']
    filedump(fitting_results, 'fitting_results.json')
    is_mag = detect_is_mag(mag)
    # if not is_mag:
        # incar.update({'ISPIN': 1})


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    init_stdout()

    incar = read_incar(run_spec)
    kpoints = read_kpoints(run_spec)
    is_mag = incar['ISPIN'] == 2
    if incar['LWAVE'] == False:
        LWAVE = False
        incar['LWAVE'] = True
    else:
        LWAVE = True

    fitting_results = []
    poscars = fileload('../' + run_spec['fitting_results'])[-1]['poscars']

    # first round
    volume_fitting(run_spec, (incar, kpoints, poscars), is_mag, fitting_results)
