import os
import sys
import numpy as np
import shutil
from run_module import *
import pymatgen as mg


if __name__ == '__main__':
    # pre-config
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    init_stdout()

    # read settings
    incar = read_incar(run_spec)
    kpoints = read_kpoints(run_spec)
    structure = generate_structure(run_spec)

    # write input files and run vasp
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()
