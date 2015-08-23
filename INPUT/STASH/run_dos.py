import os
import sys
import shutil
import numpy as np
from run_module import *
import pymatgen as mg


if __name__ == '__main__':
    run_specs, filename = get_run_specs_and_filename()
    chdir(get_run_dir(run_specs))
    filedump(run_specs, filename)
    init_stdout()
    incar = read_incar(run_specs)
    if os.path.isfile('../properties.json'):
        properties = fileload('../properties.json')
        if 'ISPIN' not in incar:
            if detect_is_mag(properties['mag']):
                incar.update({'ISPIN': 2})
            else:
                incar.update({'ISPIN': 1})

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = generate_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = read_kpoints(run_specs, structure)

    # first SC run
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_specs)
    run_vasp()

    # second non-SC run
    incar.update(run_specs['dos']['incar'])
    kpoints = read_kpoints(run_specs['dos'], structure)
    structure = mg.Structure.from_file('CONTCAR')

    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    run_vasp()

    vasprun = mg.io.vasp.Vasprun('vasprun.xml')
    dos = vasprun.tdos
    dosp = mg.electronic_structure.plotter.DosPlotter()
    dosp.add_dos(dos)
    dosp.save_plot('DOS.pdf', 'pdf')
