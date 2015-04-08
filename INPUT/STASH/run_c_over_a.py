import os
import sys
import shutil
import numpy as np
from run_module import rm_stdout, detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure
import matplotlib.pyplot as plt
import pymatgen as mg


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

    V = run_spec['poscar']['volume']
    structure.scale_lattice(V)
    c_over_a_params = run_spec['c_over_a']
    c_over_a = np.linspace(c_over_a_params['begin'], c_over_a_params['end'], c_over_a_params['sample_point_num'])
    energy = np.zeros(len(c_over_a))

    for i, c_a in enumerate(c_over_a):
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        a = (V/c_a)**(1/3.)
        c = a * c_a
        lat = mg.Lattice.tetragonal(a, c)
        structure.modify_lattice(lat)
        structure.to(filename='POSCAR')
        write_potcar(run_spec)
        run_vasp()
        oszicar = mg.io.vaspio.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy
        structure = mg.Structure.from_file('CONTCAR')

    plt.plot(c_over_a, energy, 'o')
    plt.tight_layout()
    plt.savefig('energy.pdf')
    plt.close()
