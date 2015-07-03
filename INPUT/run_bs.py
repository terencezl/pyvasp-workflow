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
    structure = mg.Structure.from_file('CONTCAR')
    incar.update(run_spec['bs']['incar'])
    # obtain the automatically generated kpoints list
    hskp = mg.symmetry.bandstructure.HighSymmKpath(structure)
    kpoints = mg.io.vaspio.Kpoints.automatic_linemode(run_spec['bs']['kpoints_division'], hskp)
    kpoints.comment = ','.join(['-'.join(i) for i in hskp.kpath['path']])

    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()
