import os
import sys
import shutil
import numpy as np
from run_module import *
import pymatgen as mg


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    init_stdout()
    incar = read_incar(run_spec)
    if os.path.isfile('../properties.json'):
        properties = fileload('../properties.json')
        if 'ISPIN' not in incar:
            if detect_is_mag(properties['mag']):
                incar.update({'ISPIN': 2})
            else:
                incar.update({'ISPIN': 1})

    # higher priority for run_spec
    if 'poscar' in run_spec:
        structure = generate_structure(run_spec)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = read_kpoints(run_spec, structure)

    # first SC run
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()

    # second non-SC run
    incar.update(run_spec['dos']['incar'])
    kpoints = read_kpoints(run_spec['dos'], structure)
    structure = mg.Structure.from_file('CONTCAR')

    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    run_vasp()
