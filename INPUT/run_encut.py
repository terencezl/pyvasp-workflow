import os
import sys
import shutil
import numpy as np
from run_module import *
import matplotlib.pyplot as plt
import pymatgen as mg


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)

    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    rm_stdout()
    properties = fileload('../properties.json')
    incar = read_incar(run_spec)
    kpoints = mg.io.vaspio.Kpoints()
    if detect_is_mag(properties['mag']):
        incar.update({'ISPIN': 2})
    else:
        incar.update({'ISPIN': 1})

    if os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
    else:
        structure = generate_structure(run_spec)
        structure.scale_lattice(properties['V0'])

    encut_params = run_spec['encut_change']
    if isinstance(encut_params, dict):
        encut_change = np.array(range(encut_params['begin'], encut_params['end'], encut_params['step']))
    elif isinstance(encut_params, list):
        encut_change = np.array(encut_params)
    energy = np.zeros(len(encut_change))

    for i, encut in enumerate(encut_change):
        incar['ENCUT'] = encut
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        structure.to(filename='POSCAR')
        write_potcar(run_spec)
        run_vasp()
        oszicar = mg.io.vaspio.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy

    energy /= structure.num_sites
    plt.plot(encut_change, energy, 'o')
    plt.xlabel('ENCUT (eV)')
    plt.ylabel('Energy (eV)')
    plt.tight_layout()
    plt.savefig('energy-encut.pdf')
    plt.close()
    np.savetxt('energy-encut.txt', np.column_stack((encut_change, energy)), '%12.4f', header='encut energy')

    energy_relative = np.abs(np.diff(energy))
    plt.plot(encut_change[1:], energy_relative, 'o')
    plt.xlabel('ENCUT (eV)')
    plt.ylabel('Energy (eV)')
    plt.tight_layout()
    plt.savefig('energy_relative-encut.pdf')
    plt.close()
    np.savetxt('energy_relative-encut.txt', np.column_stack((encut_change[1:], energy_relative)), '%12.4f', header='encut energy_relative')
