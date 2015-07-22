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
    init_stdout()
    properties = fileload('../properties.json')
    incar = read_incar(run_spec)
    # empty kpoints to begin with
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

    kpoints.style = run_spec['kpoints_test']['mode']
    kpoints_params = run_spec['kpoints_test']['kpoints_change']
    assert isinstance(kpoints_params, list)
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
    plt.plot(energy, 'o')
    ax = plt.gca()
    ax.xaxis.set_ticklabels([','.join(map(str, i)) for i in kpoints_change.tolist()])
    plt.xlabel('KP')
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
