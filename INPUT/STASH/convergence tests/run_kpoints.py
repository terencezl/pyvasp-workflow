import os
import numpy as np
import run_module as rmd
import matplotlib.pyplot as plt
import pymatgen as mg


if __name__ == '__main__':
    """

    Run convergence test with changing kpoints subdivision values, and plot
    figures.

    You should set a 'kpoints_test' tag in the specs file, like

        kpoints_test:
          density_change: [1000, 2000, 4000]
          force_gamma: True

    Obviously, 'kpoints' tag should be omitted.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()
    incar = rmd.read_incar(run_specs)
    if os.path.isfile(('../properties.json')):
        properties = rmd.fileload('../properties.json')
        if 'ISPIN' not in incar:
            if rmd.detect_is_mag(properties['mag']):
                incar.update({'ISPIN': 2})
            else:
                incar.update({'ISPIN': 1})

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = rmd.get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
        rmd.insert_elem_types(run_specs, structure)

    kpoints_specs = run_specs['kpoints_test']
    if 'force_gamma' in kpoints_specs:
        force_gamma = kpoints_specs['force_gamma']
    else:
        force_gamma = False

    if 'density_change' in kpoints_specs:
        density_change = np.array(kpoints_specs['density_change'])
    else:
        density_change = np.array(range(kpoints_specs['begin'], kpoints_specs['end'], kpoints_specs['step']))
    energy = np.zeros(len(density_change))

    for i, kp in enumerate(density_change):
        incar.write_file('INCAR')
        kpoints = mg.io.vasp.Kpoints.automatic_density(structure, kp, force_gamma=force_gamma)
        kpoints.write_file('KPOINTS')
        structure.to(filename='POSCAR')
        rmd.write_potcar(run_specs)
        rmd.run_vasp()
        oszicar = mg.io.vasp.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy

    energy /= structure.num_sites
    plt.plot(density_change, energy, 'o')
    ax = plt.gca()
    plt.xlabel('KPPRA')
    plt.ylabel('Energy (eV)')
    plt.tight_layout()
    plt.savefig('energy-kps.pdf')
    plt.close()
    np.savetxt('energy-kps.txt', np.column_stack((density_change, energy)), '%12.4f', header='kps energy')

    energy_relative = np.abs(np.diff(energy))
    plt.plot(density_change[1:], energy_relative, 'o')
    plt.xlabel('KPPRA')
    plt.ylabel('Energy (eV)')
    plt.tight_layout()
    plt.savefig('energy_relative-kps.pdf')
    plt.close()
    np.savetxt('energy_relative-kps.txt', np.column_stack((density_change[1:], energy_relative)), '%12.4f', header='kps energy_relative')
