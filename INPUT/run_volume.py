import os
import sys
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import pymatgen as mg
import pydass_vasp
from run_module import detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure


def volume_loop_fitting(run_spec, (incar, kpoints, structure), (volume, energy, mag), is_mag):
    """
    Loop over a set of volumes.
    """
    for i, V in enumerate(volume):
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        structure.scale_lattice(V)
        structure.to(filename='POSCAR')
        write_potcar(run_spec)
        run_vasp()
        oszicar = mg.io.vaspio.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy
        if is_mag:
            mag[i] = oszicar.ionic_steps[-1]['mag']

    fitting_result = pydass_vasp.fitting.eos_fit(volume, energy, save_figs=True)
    fitting_params = fitting_result['params']
    r_squared = fitting_result['r_squared']

    dict_to_json = fitting_params.copy()
    dict_to_json['r_squared'] = r_squared
    filedump(dict_to_json, 'fitting_result.json')

    return fitting_params, r_squared

if __name__ == '__main__':
    filename = sys.argv[1]
    subdirname = sys.argv[2]
    run_spec = fileload(filename)

    is_mag = run_spec['incar']['ISPIN'] == 2
    enter_main_dir(run_spec)
    (incar, kpoints) = read_incar_kpoints(run_spec)
    structure = generate_structure(run_spec)
    properties = {}

    chdir(subdirname)
    iterations = []
    mags_list = []

    volume_params = run_spec['volume']
    volume = np.linspace(volume_params['begin'], volume_params['end'], volume_params['sample_point_num'])
    energy = np.zeros(len(volume))
    mag = np.zeros(len(volume))
    fitting_params, r_squared = volume_loop_fitting(run_spec, (incar, kpoints, structure), (volume, energy, mag), is_mag)
    iterations.append(str(volume.tolist()))
    mags_list.append(str(mag.tolist()))
    is_mag = detect_is_mag(mag)
    if not is_mag:
        incar.update({'ISPIN': 1})

    V0 = fitting_params['V0']
    V0_ralative_pos = (V0 - volume_params['begin']) / (volume_params['end'] - volume_params['begin'])
    is_V0_within_valley = V0_ralative_pos > 0.4 and V0_ralative_pos < 0.6

    while not (is_V0_within_valley and (volume[-1] - volume[0])/V0 < 0.25 and (energy < 0).all()):
        V_begin = V0 * 9./10
        V_end = V0 * 11./10
        volume = np.linspace(V_begin, V_end, 5)
        energy = np.zeros(len(volume))
        mag = np.zeros(len(volume))
        fitting_params, r_squared = volume_loop_fitting(run_spec, (incar, kpoints, structure), (volume, energy, mag), is_mag)
        iterations.append(str(volume.tolist()))
        mags_list.append(str(mag.tolist()))
        is_mag = detect_is_mag(mag)
        if not is_mag:
            incar.update({'ISPIN': 1})

        V0 = fitting_params['V0']
        V0_ralative_pos = (V0 - V_begin) / (V_end - V_begin)
        is_V0_within_valley = V0_ralative_pos > 0.4 and V0_ralative_pos < 0.6

    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.scale_lattice(V0)
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()
    oszicar = mg.io.vaspio.Oszicar('OSZICAR')
    energy = oszicar.final_energy
    if is_mag:
        mag = oszicar.ionic_steps[-1]['mag']
        is_mag = detect_is_mag(mag)
    else:
        mag = 0
    shutil.copy('CONTCAR', '../POSCAR')

    with open('iterations.txt', 'w') as f:
        f.write('\n'.join(iterations))
    if is_mag:
        with open('mags.txt', 'w') as f:
            f.write('\n'.join(mags_list))

    os.chdir('..')

    properties.update(fitting_params)
    properties.update({'E0': energy, 'mag': mag})
    filedump(properties, 'properties.json')
