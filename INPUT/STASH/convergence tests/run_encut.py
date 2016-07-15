import os
import numpy as np
import run_module as rmd
import matplotlib.pyplot as plt
import pymatgen as mg


if __name__ == '__main__':
    """

    Run convergence test with changing energy cut-off values, and plot figures.

    You should set a 'encut_test' tag in the specs file, like

        encut_test:
          change: [320, 330, 340, 350, 360, 370, 380, 390, 400]
        or
        encut_test:
          begin: 300
          end: 500
          step: 10

    Obviously, ENCUT should be omitted under the 'incar' tag.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()

    rmd.infer_from_json(run_specs)
    structure = rmd.get_structure(run_specs)
    incar = rmd.read_incar(run_specs)
    kpoints = rmd.read_kpoints(run_specs, structure)

    encut_specs = run_specs['encut_test']
    if 'change' in encut_specs:
        change = np.array(encut_specs['change'])
    else:
        change = np.array(range(encut_specs['begin'], encut_specs['end'], encut_specs['step']))
    energy = np.zeros(len(change))

    for i, encut in enumerate(change):
        incar['ENCUT'] = encut
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        structure.to(filename='POSCAR')
        rmd.write_potcar(run_specs)
        rmd.run_vasp()
        oszicar = mg.io.vasp.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy

    energy /= structure.num_sites
    plt.plot(change, energy, 'o')
    plt.xlabel('ENCUT (eV)')
    plt.ylabel('Energy (eV)')
    plt.tight_layout()
    plt.savefig('energy-encut.pdf')
    plt.close()
    np.savetxt('energy-encut.txt', np.column_stack((change, energy)), '%12.4f', header='encut energy')

    energy_relative = np.abs(np.diff(energy))
    plt.plot(change[1:], energy_relative, 'o')
    plt.xlabel('ENCUT (eV)')
    plt.ylabel('Energy (eV)')
    plt.tight_layout()
    plt.savefig('energy_relative-encut.pdf')
    plt.close()
    np.savetxt('energy_relative-encut.txt', np.column_stack((change[1:], energy_relative)), '%12.4f', header='encut energy_relative')
