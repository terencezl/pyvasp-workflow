import os
import sys
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import pymatgen as mg
import pydass_vasp
from run_module import rm_stdout, detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure


def volume_fitting(run_spec, (incar, kpoints, structure), (V_begin, V_end, V_sample_point_num), is_mag, iterations):
    poscars = []
    volume = np.linspace(V_begin, V_end, V_sample_point_num)
    energy = np.zeros(len(volume))
    mag = np.zeros(len(volume))
    for i, V in enumerate(volume):
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        structure.scale_lattice(V)
        structure.to(filename='POSCAR')
        write_potcar(run_spec)
        run_vasp()
        oszicar = mg.io.vaspio.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy
        structure = mg.Structure.from_file('CONTCAR')
        poscars.append(structure.to_dict)
        if is_mag:
            mag[i] = oszicar.ionic_steps[-1]['mag']

    fitting_result = pydass_vasp.fitting.eos_fit(volume, energy, save_figs=True)
    r_squared = fitting_result['r_squared']
    fitting_result = fitting_result['params']
    fitting_result['r_squared'] = r_squared
    iterations.append({'volume': volume.tolist(), 'energy': energy.tolist(), 'mag': mag.tolist()})
    is_mag = detect_is_mag(mag)
    if not is_mag:
        incar.update({'ISPIN': 1})

    V0 = fitting_result['V0']
    V0_ralative_pos = (V0 - V_begin) / (V_end - V_begin)
    is_V0_within_valley = V0_ralative_pos > 0.4 and V0_ralative_pos < 0.6
    is_range_proportional = (volume[-1] - volume[0])/V0 < 0.25
    is_all_energy_positive = (energy < 0).all()
    is_well_fitted = (is_V0_within_valley and is_range_proportional and is_all_energy_positive)

    return is_well_fitted, V0, structure, is_mag, fitting_result, poscars


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    is_mag = run_spec['incar']['ISPIN'] == 2

    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    rm_stdout()

    # for solution runs
    if run_spec.has_key('solution') and run_spec['solution'].has_key('ratio'):
        ratio = str(run_spec['solution']['ratio'])
        ratio_list = [float(i) for i in ratio.split('-')]
        if ratio_list[0] == 0 and ratio_list[1] == 1:
            run_spec['elem_types'] = [run_spec['elem_types'][1], run_spec['elem_types'][2]]
        elif ratio_list[0] == 1 and ratio_list[1] == 0:
            run_spec['elem_types'] = [run_spec['elem_types'][0], run_spec['elem_types'][2]]

    (incar, kpoints) = read_incar_kpoints(run_spec)
    structure = generate_structure(run_spec)
    volume_params = run_spec['volume']
    V_sample_point_num = volume_params['sample_point_num']
    iterations = []

    if os.path.isfile('../properties.json'):
        properties = fileload('../properties.json')
        V0 = properties['V0']
        V_begin = V0 * 9./10
        V_end = V0 * 11./10
    else:
        properties = {}
        V_begin = volume_params['begin']
        V_end = volume_params['end']

    # first round
    is_well_fitted, V0, structure, is_mag, fitting_result, poscars = \
            volume_fitting(run_spec, (incar, kpoints, structure), (V_begin, V_end, V_sample_point_num), is_mag, iterations)

    # possible next rounds
    while not is_well_fitted:
        V_begin = V0 * 9./10
        V_end = V0 * 11./10
        is_well_fitted, V0, structure, is_mag, fitting_result, poscars = \
                volume_fitting(run_spec, (incar, kpoints, structure), (V_begin, V_end, V_sample_point_num), is_mag, iterations)

    # equilibrium volume relaxation run
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

    # record keeping
    fitting_result['iterations'] = iterations
    filedump(fitting_result, 'fitting_result.json')

    fitting_result.pop('r_squared')
    fitting_result.pop('iterations')
    properties.update(fitting_result)
    properties.update({'E0': energy, 'mag': mag})
    if run_spec.has_key('phonopy'):
        properties.update({'volume': iterations[-1]['volume'], 'energy': iterations[-1]['energy'], 'poscars': poscars})
        e_v_dat = np.column_stack((iterations[-1]['volume'], iterations[-1]['energy']))
        np.savetxt('e-v.dat', e_v_dat, '%15.6f', header='volume energy')
    filedump(properties, '../properties.json')

    shutil.copy('CONTCAR', '../POSCAR')
