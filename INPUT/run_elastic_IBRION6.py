import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import pymatgen as mg
from run_module import detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure


if __name__ == '__main__':
    filename = sys.argv[1]
    subdirname = sys.argv[2]
    run_spec = fileload(filename)
    enter_main_dir(run_spec)
    properties = fileload('properties.json')

    (incar, kpoints) = read_incar_kpoints(run_spec)
    if not detect_is_mag(properties['mag']):
        incar.update({'ISPIN': 1})

    if os.path.isfile('POSCAR'):
        structure = mg.Structure.from_file('POSCAR')
    else:
        structure = generate_structure(run_spec)
        structure.scale_lattice(properties['V0'])

    chdir(subdirname)
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()
    os.chdir('..')
