import os
import numpy as np
from run_module import *
import matplotlib.pyplot as plt
import pymatgen as mg


if __name__ == '__main__':
    """

    Run convergence test with changing energy cut-off values, and plot figures.

    You should set a 'encut_change' tag in the specs file, like

        encut_change: [320, 330, 340, 350, 360, 370, 380, 390, 400]
        or
        encut_change:
          begin: 300
          end: 500
          step: 10

    Obviously, ENCUT should be omitted under the 'incar' tag.

    """

    run_specs, filename = get_run_specs_and_filename()
    chdir(get_run_dir(run_specs))
    filedump(run_specs, filename)
    init_stdout()
    incar = read_incar(run_specs)
    if os.path.isfile(('../properties.json')):
        properties = fileload('../properties.json')
        if 'ISPIN' not in incar:
            if detect_is_mag(properties['mag']):
                incar.update({'ISPIN': 2})
            else:
                incar.update({'ISPIN': 1})

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = read_kpoints(run_specs, structure)

    encut_params = run_specs['encut_change']
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
        write_potcar(run_specs)
        run_vasp()
        oszicar = mg.io.vasp.Oszicar('OSZICAR')
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
