import os
import shutil
import numpy as np
from run_module import *
import matplotlib.pyplot as plt
import pymatgen as mg
import pydass_vasp


def volume_fitting(structure, is_mag, fitting_results):
    """

    Construct a loop to get and fit the energy with changing volumes, return
    some indicators showing if the fit is "good" or not.

    """

    volume = np.linspace(V_begin, V_end, V_sample_point_num)
    energy = np.zeros(len(volume))
    mag = np.zeros(len(volume))
    structures = []
    for i, V in enumerate(volume):
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        structure.scale_lattice(V)
        structure.to(filename='POSCAR')
        write_potcar(run_specs)
        run_vasp()
        oszicar = mg.io.vasp.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy
        structure = mg.Structure.from_file('CONTCAR')
        structures.append(structure.as_dict())
        if is_mag:
            mag[i] = oszicar.ionic_steps[-1]['mag']

    # dump in case error in fitting
    fitting_results.append({'volume': volume.tolist(), 'energy': energy.tolist(), 'mag': mag.tolist(), 'structures': structures})
    filedump(fitting_results, 'fitting_results.json')
    # plot in case error in fitting
    plt.plot(volume, energy, 'o')
    plt.tight_layout()
    plt.savefig('eos_fit.pdf')
    plt.close()
    # fitting and dumping
    fitting_result_raw = pydass_vasp.fitting.eos_fit(volume, energy, save_figs=True)
    fitting_results[-1]['params'] = fitting_result_raw['params']
    fitting_results[-1]['r_squared'] = fitting_result_raw['r_squared']
    filedump(fitting_results, 'fitting_results.json')
    # a simplifed version of the file dump
    fitting_params = fitting_result_raw['params'].copy()
    fitting_params['r_squared'] = fitting_result_raw['r_squared']
    filedump(fitting_params, 'fitting_params.json')

    is_mag = detect_is_mag(mag)
    # uncomment to make calculation faster by switching off ISPIN if possible
    # if not is_mag:
        # incar.update({'ISPIN': 1})

    V0 = fitting_result_raw['params']['V0']
    V0_ralative_pos = (V0 - V_begin) / (V_end - V_begin)
    is_V0_within_valley = V0_ralative_pos > 0.4 and V0_ralative_pos < 0.6
    is_range_proportional = (volume[-1] - volume[0])/V0 < 0.25
    is_well_fitted = (is_V0_within_valley and is_range_proportional)

    return is_well_fitted, V0, structure, is_mag


if __name__ == '__main__':
    """

    Obtain the equilibrium volume and bulk modulus by third order Burch-
    Murnaghan EOS fit. If the "goodness" (see the actual code) is not reached,
    reconstruct the volume range and rerun till the fit is "good".

    Optionally, you can set a 'volume' tag in the specs file like

        volume:
          begin: 15
          end:   25
          sample_point_num: 5

    If 'volume' does not exist, a ../properties.json file is attempted and if it
    exists, it should contain a 'V0' field, the volume range is constructed with
    5 points between 0.9 * V0 and 1.1 * V0. If this file doesn't exsit, the
    volume of the structure returned by get_structure() is used to do the
    same construction.

    """

    run_specs, filename = get_run_specs_and_filename()
    chdir(get_run_dir(run_specs))
    filedump(run_specs, filename)
    init_stdout()

    incar = read_incar(run_specs)
    is_properties = None
    if os.path.isfile(('../properties.json')):
        is_properties = True
        properties = fileload('../properties.json')

    if 'ISPIN' in incar:
        is_mag = incar['ISPIN'] == 2
    elif is_properties:
        is_mag = detect_is_mag(properties['mag'])
        if is_mag:
            incar.update({'ISPIN': 2})
        else:
            incar.update({'ISPIN': 1})
    else:
        is_mag = False

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = read_kpoints(run_specs, structure)

    if 'volume' in run_specs and run_specs['volume']:
        volume_params = run_specs['volume']
        V_begin = volume_params['begin']
        V_end = volume_params['end']
        V_sample_point_num = volume_params['sample_point_num']
    elif is_properties:
        V0 = properties['V0']
        V_begin = V0 * 9./10
        V_end = V0 * 11./10
        V_sample_point_num = 5
    else:
        V0 = structure.volume
        V_begin = V0 * 9./10
        V_end = V0 * 11./10
        V_sample_point_num = 5

    fitting_results = []
    # first round
    is_well_fitted, V0, structure, is_mag = volume_fitting(structure, is_mag, fitting_results)

    # possible next rounds
    while not is_well_fitted:
        V_begin = V0 * 9./10
        V_end = V0 * 11./10
        is_well_fitted, V0, structure, is_mag = volume_fitting(structure, is_mag, fitting_results)

    # equilibrium volume run
    structure.scale_lattice(V0)
    structure.to(filename='POSCAR')
    run_vasp()
    oszicar = mg.io.vasp.Oszicar('OSZICAR')
    E0 = oszicar.final_energy
    if is_mag:
        mag = oszicar.ionic_steps[-1]['mag']
    else:
        mag = 0

    if 'LWAVE' not in incar:
        os.remove('WAVECAR')

    # dump properties.json
    if is_properties:
        # load again immediately before save
        properties = fileload('../properties.json')
    else:
        properties = {}
    properties['V0'] = fitting_results[-1]['params']['V0']
    properties['B0'] = fitting_results[-1]['params']['B0']
    properties.update({'E0': E0, 'mag': mag})
    filedump(properties, '../properties.json')

    shutil.copy('CONTCAR', '../POSCAR')
