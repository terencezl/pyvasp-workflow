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
from run_module import enter_main_dir, run_vasp, generate_incar_kpoints_potcar, generate_structure


def volume_loop_fitting(run_spec, volume, energy, structure):
    """
    loop over a set of volumes
    """
    for i, V in enumerate(volume):
        volume_str = '{:.2f}'.format(V)
        os.makedirs(volume_str)
        os.chdir(volume_str)
        generate_incar_kpoints_potcar(run_spec)
        structure.scale_lattice(V)
        structure.to(filename='POSCAR')
        run_vasp()
        energy[i] = mg.io.vaspio.Vasprun('vasprun.xml', parse_dos=False, parse_eigen=False).final_energy
        os.chdir('..')

    fitting_params = pydass_vasp.fitting.eos_fit(
        volume, energy, save_figs=True)['parameters']
    with open('fitting_params.json', 'w') as f:
        json.dump(fitting_params, f, indent=4)

    return fitting_params


if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename) as f:
        run_spec = yaml.load(f)

    enter_main_dir(run_spec)
    structure = generate_structure(run_spec)

    if os.path.isdir('volume_run'):
        shutil.rmtree('volume_run')
    if os.path.isdir('volume_run_coarse'):
        shutil.rmtree('volume_run_coarse')
    if os.path.isdir('equi-relax'):
        shutil.rmtree('equi-relax')

    # first round
    os.makedirs('volume_run')
    os.chdir('volume_run')
    volume_params = run_spec['volume']
    volume = np.linspace(volume_params['begin'], volume_params['end'], volume_params['sample_point_num'])
    energy = np.zeros(len(volume))
    fitting_params = volume_loop_fitting(run_spec, volume, energy, structure)
    os.chdir('..')

    # second round
    os.renames('volume_run', 'volume_run_coarse')
    os.makedirs('volume_run')
    os.chdir('volume_run')
    V0 = fitting_params['V0']
    volume = np.linspace(V0 * 9./10, V0 * 11./10, 5)
    energy = np.zeros(len(volume))
    fitting_params = volume_loop_fitting(run_spec, volume, energy, structure)
    np.savetxt('eos.txt', np.column_stack((volume, energy)), '%12.4f', header='volume energy')
    os.chdir('..')

    # # equi-relax
    # os.makedirs('equi-relax')
    # os.chdir('equi-relax')
    # generate_incar_kpoints_potcar(run_spec)
    # structure.scale_lattice(fitting_params['V0'])
    # structure.to(filename='POSCAR')
    # run_vasp()
    # vasprun = mg.io.vaspio.Vasprun('vasprun.xml', parse_dos=False, parse_eigen=False)
    # os.chdir('..')
