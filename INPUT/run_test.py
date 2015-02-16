import os
import sys
import shutil
import numpy as np
from run_module import rm_stdout, detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure
import pymatgen as mg
import pydass_vasp


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    rm_stdout()
    (incar, kpoints) = read_incar_kpoints(run_spec)
    if os.path.isfile('../properties.json'):
        is_properties = True
        properties = fileload('../properties.json')
        if detect_is_mag(properties['mag']):
            incar.update({'ISPIN': 2})
        else:
            incar.update({'ISPIN': 1})
    else:
        is_properties = False

    if os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
    elif os.path.isfile('CONTCAR'):
        structure = mg.Structure.from_file('CONTCAR')
    else:
        structure = generate_structure(run_spec)
        if is_properties:
            structure.scale_lattice(properties['V0'])

    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()
    plotting_result = pydass_vasp.plotting.plot_tdos(display=False, save_figs=True, return_states_at_Ef=True)
    if is_properties:
        properties['TDOS_at_Ef'] = plotting_result['TDOS_at_Ef']/properties['V0']
        filedump(properties, '../properties.json')
