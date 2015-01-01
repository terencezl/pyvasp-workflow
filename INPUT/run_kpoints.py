import os
import sys
import shutil
import json
import yaml
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import pymatgen as mg
import pydass_vasp
from run_module import chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure


if __name__ == '__main__':
    filename = sys.argv[1]
    subdirname = sys.argv[2]
    with open(filename) as f:
        run_spec = yaml.load(f)

    enter_main_dir(run_spec)
    (incar, kpoints) = read_incar_kpoints(run_spec)
    structure = generate_structure(run_spec)
    kpoint_params = run_spec['kpoints_change']
    kpoints_change = np.linspace(kpoint_params['begin'], kpoint_params['end'], kpoint_params['sample_point_num'])
    energy = np.zeros(len(kpoints_change))
    chdir(subdirname)

    for i, kp in enumerate(kpoints_change):
        kp_dir = '{:.2f}'.format(kp)
        os.makedirs(kp_dir)
        os.chdir(kp_dir)
        incar.write_file('INCAR')
        kpoints.kp.kpts = [[kp, kp, kp]]
        kpoints.write_file('KPOINTS')
        structure.to(filename='POSCAR')
        write_potcar(run_spec)
        run_vasp()
        oszicar = mg.io.vaspio.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy
        os.chdir('..')

    plt.plot(kpoints_change, energy, 'o')
    plt.savefig('energy-kps.pdf')
    plt.close()
    np.savetxt('energy-kps.txt', np.column_stack((kpoints_change, energy)), '%12.4f', header='kps energy')

    energy_relative = np.diff(energy)
    plt.plot(kpoints_change[1:], energy_relative, 'o')
    plt.savefig('energy_relative-kps.pdf')
    plt.close()
    np.savetxt('energy_relative-kps.txt', np.column_stack((kpoints_change, energy)), '%12.4f', header='kps energy_relative')

    os.chdir('..')
