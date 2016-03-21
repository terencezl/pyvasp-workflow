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
          mode: G
          kpoints_change: [[7, 7, 7], [9, 9, 9], [11, 11, 11], [13, 13, 13]]

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
    # empty kpoints to begin with
    kpoints = mg.io.vasp.Kpoints()

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = rmd.get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
        rmd.insert_elem_types(run_specs, structure)

    kpoints.style = run_specs['kpoints_test']['mode']
    kpoints_params = run_specs['kpoints_test']['kpoints_change']
    assert isinstance(kpoints_params, list)
    kpoints_change = np.array(kpoints_params)
    energy = np.zeros(len(kpoints_change))

    for i, kp in enumerate(kpoints_change):
        incar.write_file('INCAR')
        kpoints.kpts = [[kp[0], kp[1], kp[2]]]
        kpoints.write_file('KPOINTS')
        structure.to(filename='POSCAR')
        rmd.write_potcar(run_specs)
        rmd.run_vasp()
        oszicar = mg.io.vasp.Oszicar('OSZICAR')
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
