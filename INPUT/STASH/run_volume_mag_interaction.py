import os
import sys
import shutil
import numpy as np
from run_modules import *
import matplotlib.pyplot as plt
import pymatgen as mg
import pydass_vasp


def volume_fitting(run_spec, (incar, kpoints, poscars)):
    volume = np.zeros(len(poscars))
    energy = np.zeros((len(poscars), 4))
    for i, p in enumerate(poscars):
        structure = mg.Structure.from_dict(p)
        volume[i] = structure.volume
        chdir(str(np.round(structure.volume, 2)))
        magmoms = [ '8*3 4*3 16*0',
                    '8*3 4*-3 16*0',
                    '3 3 -3 -3 3 3 -3 -3 4*3 16*0',
                    '8*3 3 3 -3 -3 16*0']
        for j, m in enumerate(magmoms):
            incar['MAGMOM'] = m
            incar.write_file('INCAR')
            kpoints.write_file('KPOINTS')
            structure.to(filename='POSCAR')
            write_potcar(run_spec)
            run_vasp()
            oszicar = mg.io.vaspio.Oszicar('OSZICAR')
            energy[i, j] = oszicar.final_energy

        os.chdir('..')

    filedump({'volume': volume.tolist(), 'energy': energy.tolist()}, 'data.json')


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    rm_stdout()

    incar = read_incar(run_spec)
    kpoints = read_kpoints(run_spec)
    poscars = fileload('../' + run_spec['fitting_results'])[-1]['poscars']

    # first round
    volume_fitting(run_spec, (incar, kpoints, poscars))
