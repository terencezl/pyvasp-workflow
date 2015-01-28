import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import pymatgen as mg
from run_module import rm_stdout, detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    enter_main_dir(run_spec)
    shutil.move('../../' + filename, './')
    rm_stdout()
    (incar, kpoints) = read_incar_kpoints(run_spec)
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    if os.path.isfile('CONTCAR'):
        structure = mg.Structure.from_file('CONTCAR')
    elif os.path.isfile('POSCAR'):
        structure = mg.Structure.from_file('POSCAR')
    else:
        structure = generate_structure(run_spec)
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()