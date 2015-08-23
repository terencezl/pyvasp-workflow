import os
import sys
import shutil
import numpy as np
from run_module import *
import pymatgen as mg
import pymatgen.electronic_structure.plotter

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

    # first DFT run
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()

    # second hybrid run
    structure = mg.Structure.from_file('CONTCAR')
    incar.update(run_spec['bs_hybrid']['incar'])
    # obtain the automatically generated kpoints list
    hskp = mg.symmetry.bandstructure.HighSymmKpath(structure)
    kpts_bs = hskp.get_kpoints(run_spec['bs_hybrid']['kpoints_division'], return_cartesian=False)
    kpoints = mg.io.vasp.Kpoints.from_file('IBZKPT')
    kpoints.kpts.extend([i.tolist() for i in kpts_bs[0]])
    kpoints.kpts_weights.extend([0 for i in kpts_bs[0]])
    kpoints.labels.extend(kpts_bs[1])
    kpoints.num_kpts += len(kpts_bs[0])

    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    run_vasp()

    vasprun = mg.io.vasp.Vasprun('vasprun.xml')
    bs = vasprun.get_band_structure(line_mode=True)
    bsp = mg.electronic_structure.plotter.BSPlotter(bs)
    bsp.save_plot('BS.pdf', 'pdf')
