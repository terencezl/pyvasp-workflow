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

    kpoint_params = run_spec['kpoints_change']
    kpoints_change = np.array([range(kpoint_params['begin'][i], kpoint_params['end'][i], kpoint_params['step']) for i in range(3)]).T
    energy = np.zeros(len(kpoints_change))
    chdir(subdirname)

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
    plt.savefig('energy-kps.pdf')
    plt.close()
    np.savetxt('energy-kps.txt', np.column_stack((kpoints_change, energy)), '%12.4f', header='kp1 kp2 kp3 energy')

    energy_relative = np.abs(np.diff(energy))
    plt.plot(kpoints_change[1:, 0], energy_relative, 'o')
    plt.xlabel('KP1')
    plt.ylabel('Energy (eV)')
    plt.savefig('energy_relative-kps.pdf')
    plt.close()
    np.savetxt('energy_relative-kps.txt', np.column_stack((kpoints_change[1:], energy_relative)), '%12.4f', header='kp1 kp2 kp3 energy_relative')

    os.chdir('..')
