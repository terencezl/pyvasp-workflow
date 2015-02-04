import os
import sys
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import pymatgen as mg
import pydass_vasp
from run_module import rm_stdout, detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    rm_stdout()
    (incar, kpoints) = read_incar_kpoints(run_spec)
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    if os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
    elif os.path.isfile('CONTCAR'):
        structure = mg.Structure.from_file('CONTCAR')
    else:
        structure = generate_structure(run_spec)
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()
    plotting_result = pydass_vasp.plotting.plot_dos(display=False, save_figs=True, save_data=True, return_states_at_Ef=True)
    properties = fileload('../properties.json')
    properties['TDOS_at_Ef'] = plotting_result['TDOS_at_Ef']
    filedump(properties, '../properties.json')
