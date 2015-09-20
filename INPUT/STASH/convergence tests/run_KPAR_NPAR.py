import os
import subprocess
import numpy as np
from run_module import *
import matplotlib.pyplot as plt
import pymatgen as mg


if __name__ == '__main__':
    """

    Run test with chaning KPAR and NPAR, and plot figures.

    You should set a 'KPAR_NPAR_change' tag in the specs file, like

        KPAR_NPAR_change: [[4,1], [4,2], [4,4], [4,8], [4,16], [8,1], [8,2],
                        [8,4], [8,8], [16,1], [16,2], [16,4], [32,1], [32,2]]

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

    KPAR_NPAR_change = np.array(run_specs['KPAR_NPAR_change'])
    energy = np.zeros(len(KPAR_NPAR_change))
    time = np.zeros(len(KPAR_NPAR_change))

    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_specs)

    # main workflow
    for i, KPAR_NPAR in enumerate(KPAR_NPAR_change):
        incar['KPAR'] = KPAR_NPAR[0]
        incar['NPAR'] = KPAR_NPAR[1]
        incar.write_file('INCAR')
        run_vasp()
        oszicar = mg.io.vasp.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy
        time_list = list(map(float, subprocess.getoutput("grep real stdout | tail -1 | awk '{print $2}'").split(':')))
        if len(time_list) == 2:
            time[i] = time_list[0] + time_list[1]/60.
        elif len(time_list) == 3:
            time[i] = time_list[0] * 60 + time_list[1] + time_list[2]/60.

    np.savetxt('data.txt', np.column_stack((KPAR_NPAR_change, energy, time)), '%12.4f', header='KPAR NPAR energy time')

    energy = np.round(energy, 4)
    xticklabel = list(map(str, KPAR_NPAR_change))
    fig, axes = plt.subplots(2, 1, sharex=True)
    plt.sca(axes[0])
    plt.plot(energy, 'o')
    plt.ylabel('Energy (eV)')

    plt.sca(axes[1])
    plt.plot(time, 'o')
    plt.ylabel('Time (min.)')

    plt.xlabel('[KPAR,NPAR]')
    axes[1].xaxis.set_ticklabels(xticklabel[::2])
    plt.locator_params(nbins=len(KPAR_NPAR_change)/2)
    plt.tight_layout()
    plt.savefig('figs.pdf')
    plt.close()
