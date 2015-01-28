import os
import sys
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import pymatgen as mg
import pydass_vasp
from run_module import rm_stdout, detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure


def volume_loop_fitting(run_spec, (incar, kpoints, structure), (volume, energy, mag), is_mag):
    """
    Loop over a set of volumes.
    """
    for i, V in enumerate(volume):
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        if os.path.isfile('CONTCAR'):
            structure = mg.Structure.from_file('CONTCAR')
        structure.scale_lattice(V)
        structure.to(filename='POSCAR')
        # poscar = mg.io.vaspio.Poscar(structure, selective_dynamics=[[0, 0, 0]] + [[1,1,1]]*(structure.num_sites-1))
        # poscar.write_file('POSCAR')
        write_potcar(run_spec)
        run_vasp()
        oszicar = mg.io.vaspio.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy
        if is_mag:
            mag[i] = oszicar.ionic_steps[-1]['mag']

    fitting_result = pydass_vasp.fitting.eos_fit(volume, energy, save_figs=True)
    r_squared = fitting_result['r_squared']
    fitting_result = fitting_result['params']
    fitting_result['r_squared'] = r_squared

    return fitting_result


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    is_mag = run_spec['incar']['ISPIN'] == 2

    enter_main_dir(run_spec)
    shutil.move('../../' + filename, './')
    rm_stdout()
    (incar, kpoints) = read_incar_kpoints(run_spec)
    structure = generate_structure(run_spec)
    if os.path.isfile('CONTCAR'):
        os.remove('CONTCAR')

    if os.path.isfile('../properties.json'):
        reference_properties_exists = True
        properties = fileload('../properties.json')
        V0 = properties['V0']
    else:
        reference_properties_exists = False
        properties = {}
    iterations = []

    # first round
    if reference_properties_exists:
        V_begin = V0 * 9./10
        V_end = V0 * 11./10
        volume = np.linspace(V_begin, V_end, 6)
    else:
        volume_params = run_spec['volume']
        volume = np.linspace(volume_params['begin'], volume_params['end'], volume_params['sample_point_num'])

    energy = np.zeros(len(volume))
    mag = np.zeros(len(volume))
    fitting_result = volume_loop_fitting(run_spec, (incar, kpoints, structure), (volume, energy, mag), is_mag)
    iterations.append({'volume': volume.tolist(), 'energy': energy.tolist(), 'mag': mag.tolist()})
    is_mag = detect_is_mag(mag)
    if not is_mag:
        incar.update({'ISPIN': 1})

    V0 = fitting_result['V0']
    if reference_properties_exists:
        V0_ralative_pos = (V0 - V_begin) / (V_end - V_begin)
    else:
        V0_ralative_pos = (V0 - volume_params['begin']) / (volume_params['end'] - volume_params['begin'])
    is_V0_within_valley = V0_ralative_pos > 0.4 and V0_ralative_pos < 0.6
    is_range_proportional = (volume[-1] - volume[0])/V0 < 0.25
    is_all_energy_positive = (energy < 0).all()

    # possible next rounds
    while not (is_V0_within_valley and is_range_proportional and is_all_energy_positive):
        V_begin = V0 * 9./10
        V_end = V0 * 11./10
        volume = np.linspace(V_begin, V_end, 6)
        energy = np.zeros(len(volume))
        mag = np.zeros(len(volume))
        fitting_result = volume_loop_fitting(run_spec, (incar, kpoints, structure), (volume, energy, mag), is_mag)
        iterations.append({'volume': volume.tolist(), 'energy': energy.tolist(), 'mag': mag.tolist()})
        is_mag = detect_is_mag(mag)
        if not is_mag:
            incar.update({'ISPIN': 1})

        V0 = fitting_result['V0']
        V0_ralative_pos = (V0 - V_begin) / (V_end - V_begin)
        is_V0_within_valley = V0_ralative_pos > 0.4 and V0_ralative_pos < 0.6
        is_range_proportional = (volume[-1] - volume[0])/V0 < 0.25
        is_all_energy_positive = (energy < 0).all()

    # equilibrium volume relaxation run
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    if os.path.isfile('CONTCAR'):
        structure = mg.Structure.from_file('CONTCAR')
    structure.scale_lattice(V0)
    # poscar = mg.io.vaspio.Poscar(structure, selective_dynamics=[[0, 0, 0]] + [[1,1,1]]*(structure.num_sites-1))
    # poscar.write_file('POSCAR')
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

    # recording
    fitting_result['iterations'] = iterations
    filedump(fitting_result, 'fitting_result.json')
    shutil.copy('CONTCAR', '../POSCAR')

    fitting_result.pop('r_squared')
    fitting_result.pop('iterations')
    properties.update(fitting_result)
    properties.update({'E0': energy, 'mag': mag})
    filedump(properties, '../properties.json')
