import os
import sys
import shutil
import numpy as np
from run_modules import *
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
    kpoints = read_kpoints(run_spec)
    if detect_is_mag(properties['mag']):
        incar.update({'ISPIN': 2})
    else:
        incar.update({'ISPIN': 1})

    if os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
    else:
        structure = generate_structure(run_spec)
        structure.scale_lattice(properties['V0'])

    kpoints_params = run_spec['kpoints_change']
    if isinstance(kpoints_params, dict):
        kpoints_change = np.array([range(kpoints_params['begin'][i], kpoints_params['end'][i], kpoints_params['step']) for i in range(3)]).T
    elif isinstance(kpoints_params, list):
        kpoints_change = np.array(kpoints_params)
    energy = np.zeros(len(kpoints_change))

    for i, kp in enumerate(kpoints_change):
        incar.write_file('INCAR')
        kpoints.kpts = [[kp[0], kp[1], kp[2]]]
        kpoints.write_file('KPOINTS')
        structure.to(filename='POSCAR')
        write_potcar(run_spec)
        run_vasp()
        oszicar = mg.io.vaspio.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy

    energy /= structure.num_sites
    plt.plot(kpoints_change[:, 0], energy, 'o')
    plt.xlabel('KP1')
    plt.ylabel('Energy (eV)')
    plt.tight_layout()
    plt.savefig('energy-kps.pdf')
    plt.close()
    np.savetxt('energy-kps.txt', np.column_stack((kpoints_change, energy)), '%12.4f', header='kp1 kp2 kp3 energy')

    energy_relative = np.abs(np.diff(energy))
    plt.plot(kpoints_change[1:, 0], energy_relative, 'o')
    plt.xlabel('KP1')
    plt.ylabel('Energy (eV)')
    plt.tight_layout()
    plt.savefig('energy_relative-kps.pdf')
    plt.close()
    np.savetxt('energy_relative-kps.txt', np.column_stack((kpoints_change[1:], energy_relative)), '%12.4f', header='kp1 kp2 kp3 energy_relative')
