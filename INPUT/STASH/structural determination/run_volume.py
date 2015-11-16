import os
import shutil
import numpy as np
import run_module as rmd
import matplotlib.pyplot as plt
import pymatgen as mg
import pydass_vasp as pv


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
        rmd.write_potcar(run_specs)
        rmd.run_vasp()
        oszicar = mg.io.vasp.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy
        structure = mg.Structure.from_file('CONTCAR')
        structures.append(structure.as_dict())
        if is_mag:
            mag[i] = oszicar.ionic_steps[-1]['mag']

    # dump in case error in fitting
    fitting_results.append({'volume': volume.tolist(), 'energy': energy.tolist(), 'mag': mag.tolist(), 'structures': structures})
    rmd.filedump(fitting_results, 'fitting_results.json')
    # plot in case error in fitting
    plt.plot(volume, energy, 'o')
    plt.tight_layout()
    plt.savefig('eos_fit.pdf')
    plt.close()
    # fitting and dumping
    fitting_result_raw = pv.fitting.eos_fit(volume, energy, plot=True)
    plt.savefig('eos_fit.pdf')
    plt.close()
    params = fitting_result_raw['params']
    fitting_results[-1]['pressure'] = pv.fitting.birch_murnaghan_p(volume,
        params['V0'], params['B0'],
        params['B0_prime']).tolist()
    fitting_results[-1]['params'] = params
    fitting_results[-1]['r_squared'] = fitting_result_raw['r_squared']
    rmd.filedump(fitting_results, 'fitting_results.json')
    # a simplifed version of the file dump
    fitting_params = params.copy()
    fitting_params['r_squared'] = fitting_result_raw['r_squared']
    rmd.filedump(fitting_params, 'fitting_params.json')

    # uncomment to make calculation faster by switching off ISPIN if possible
    # is_mag = rmd.detect_is_mag(mag)
    # if not is_mag:
        # incar.update({'ISPIN': 1})

    V0 = params['V0']
    V0_ralative_pos = (V0 - V_begin) / (V_end - V_begin)
    is_V0_within_valley = V0_ralative_pos > 0.4 and V0_ralative_pos < 0.6
    is_range_proportional = (volume[-1] - volume[0])/V0 < 0.25
    is_well_fitted = (is_V0_within_valley and is_range_proportional)

    return is_well_fitted, V0, structure, is_mag


if __name__ == '__main__':
    """

    Obtain the equilibrium volume and bulk modulus by third order Burch-
    Murnaghan EOS fit.

    Optionally, with the tag 'rerun' set to True, if the "goodness" (see the
    actual code) is not reached, reconstruct the volume range and rerun till the
    fit is "good".

    Optionally, you can set a 'volume' tag in the specs file like

        volume:
          begin: 15
          end:   25
          sample_point_num: 5

    If 'volume' or 'pressure' does not exist, a ../properties.json file is
    attempted and if it exists, it should contain a 'V0' field, the volume range
    is constructed with 5 points between 0.9 * V0 and 1.1 * V0. If this file
    doesn't exsit, the volume of the structure returned by rmd.get_structure()
    is used to do the same construction.

    Optionally, you can set a 'pressure' tag in the specs file like

        pressure:
          skip_test_run: True
          begin: -1
          end:   50
          sample_point_num: 5

    In this case, an intial run will take action and obtain the fitting
    parameters and find the correct volumes corresponding to the given pressure
    range. A second run is done using those volume values. the tag
    'skip_test_run' tells the code to just use the fitting_params.json in the
    working directory without doing the test run.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()

    incar = rmd.read_incar(run_specs)
    is_properties = None
    if os.path.isfile(('../properties.json')):
        is_properties = True
        properties = rmd.fileload('../properties.json')

    if 'ISPIN' in incar:
        is_mag = incar['ISPIN'] == 2
    elif is_properties:
        is_mag = rmd.detect_is_mag(properties['mag'])
        if is_mag:
            incar.update({'ISPIN': 2})
        else:
            incar.update({'ISPIN': 1})
    else:
        is_mag = False

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = rmd.get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = rmd.read_kpoints(run_specs, structure)

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

    if not ('pressure' in run_specs and 'skip_test_run' in run_specs['pressure'] and \
            run_specs['pressure']['skip_test_run']):
        # first round
        is_well_fitted, V0, structure, is_mag = volume_fitting(structure, is_mag, fitting_results)

    if 'rerun' in run_specs and run_specs['rerun']:
        # possible next rounds
        while not is_well_fitted:
            V_begin = V0 * 9./10
            V_end = V0 * 11./10
            is_well_fitted, V0, structure, is_mag = volume_fitting(structure, is_mag, fitting_results)

    # pressure runs
    if 'pressure' in run_specs and run_specs['pressure']:
        pressure_params = run_specs['pressure']
        p_begin = pressure_params['begin']
        p_end = pressure_params['end']
        V_sample_point_num = pressure_params['sample_point_num']
        params = rmd.fileload('fitting_params.json')
        from scipy import optimize
        def pressure_func(V):
            return pv.fitting.vinet_p(V, params['V0'], params['B0'], params['B0_prime']) - p0
        V_list = []
        for p0 in [p_begin, p_end]:
            V_list.append(optimize.fsolve(pressure_func, structure.volume)[0])
        V_begin, V_end = V_list
        is_well_fitted, V0, structure, is_mag = volume_fitting(structure, is_mag, fitting_results)

    # equilibrium volume run
    structure.scale_lattice(V0)
    structure.to(filename='POSCAR')
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    rmd.write_potcar(run_specs)
    rmd.run_vasp()
    oszicar = mg.io.vasp.Oszicar('OSZICAR')
    E0 = oszicar.final_energy
    if is_mag:
        mag = oszicar.ionic_steps[-1]['mag']
    else:
        mag = 0

    # dump properties.json
    if is_properties:
        # load again immediately before save
        properties = rmd.fileload('../properties.json')
    else:
        properties = {}
    properties['V0'] = fitting_results[-1]['params']['V0']
    properties['B0'] = fitting_results[-1]['params']['B0']
    properties.update({'E0': E0, 'mag': mag})
    rmd.filedump(properties, '../properties.json')

    shutil.copy('CONTCAR', '../POSCAR')
