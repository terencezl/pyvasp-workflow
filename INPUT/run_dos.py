import os
import sys
import shutil
import numpy as np
from run_modules import *
import pymatgen as mg
import pydass_vasp


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    rm_stdout()
    incar = read_incar(run_spec)
    kpoints = read_kpoints(run_spec)
    if os.path.isfile('../properties.json'):
        is_properties = True
        properties = fileload('../properties.json')
        if detect_is_mag(properties['mag']):
            incar.update({'ISPIN': 2})
        else:
            incar.update({'ISPIN': 1})
    else:
        is_properties = False

    if 'poscar' in run_spec:
        structure = generate_structure(run_spec)
        if 'volume' in run_spec['poscar']:
            structure.scale_lattice(run_spec['poscar']['volume'])
        elif is_properties:
            structure.scale_lattice(properties['V0'])
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
    elif os.path.isfile('CONTCAR'):
        structure = mg.Structure.from_file('CONTCAR')

    # first SC run
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()

    # second non-SC run
    incar.update(run_spec['dos']['incar'])
    kpoints.kpts = [run_spec['dos']['kpoints']['divisions']]
    structure = mg.Structure.from_file('CONTCAR')

    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()

    plotting_result = pydass_vasp.plotting.plot_tdos(display=False, save_figs=True)
