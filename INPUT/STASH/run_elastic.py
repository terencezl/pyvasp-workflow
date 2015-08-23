import os
import sys
import shutil
import numpy as np
from run_module import *
from run_module_elastic import *
import pymatgen as mg
import pydass_vasp


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    cryst_sys = run_spec['elastic']['cryst_sys']

    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    incar = read_incar(run_spec)
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

    # higher priority for run_spec
    if 'poscar' in run_spec:
        structure = generate_structure(run_spec)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = read_kpoints(run_spec, structure)

    combined_econst_array = []
    fitting_results_summary = {}

    chdir('nostrain')
    init_stdout()
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()
    oszicar = mg.io.vasp.Oszicar('OSZICAR')
    energy_nostrain = oszicar.final_energy
    structure = mg.Structure.from_file('CONTCAR')
    if is_mag:
        mag_nostrain = oszicar.ionic_steps[-1]['mag']
    if 'LWAVE' not in incar:
        os.remove('WAVECAR')
    os.chdir('..')

    for test_type, strain, delta in \
                zip(*get_test_type_strain_delta_list(cryst_sys)):
        chdir(test_type)
        init_stdout()
        energy = np.zeros(len(delta))
        energy[0] = energy_nostrain
        mag = np.zeros(len(delta))
        if is_mag:
            mag[0] = mag_nostrain

        for ind, value in enumerate(delta[1:]):
            incar.write_file('INCAR')
            kpoints.write_file('KPOINTS')
            lattice_modified = mg.Lattice(
                np.dot(structure.lattice_vectors(), strain(value)))
            structure_copy = structure.copy()
            structure_copy.modify_lattice(lattice_modified)
            structure_copy.to(filename='POSCAR')
            write_potcar(run_spec)
            run_vasp()
            oszicar = mg.io.vasp.Oszicar('OSZICAR')
            energy[ind+1] = oszicar.final_energy
            if is_mag:
                mag[ind+1] = oszicar.ionic_steps[-1]['mag']

        if 'LWAVE' not in incar:
            os.remove('WAVECAR')
        fitting_results = pydass_vasp.fitting.curve_fit(central_poly, delta, energy, save_figs=True,
                    output_prefix=test_type)
        combined_econst_array.append(fitting_results['params'][0])
        fitting_results['params'] = fitting_results['params'].tolist()
        fitting_results.pop('fitted_data')
        fitting_results['delta'] = delta.tolist()
        fitting_results['energy'] = energy.tolist()
        fitting_results['mag'] = mag.tolist()
        filedump(fitting_results, 'fitting_results.json')
        # higher level fitting_results.json
        fitting_results_summary[test_type] = fitting_results
        filedump(fitting_results_summary, '../fitting_results.json')
        shutil.copy(test_type + '.pdf', '..')
        os.chdir('..')

    combined_econst_array = np.array(combined_econst_array) * 160.2 / structure.volume
    solved = solve(cryst_sys, combined_econst_array)
    filedump(solved, 'elastic.json')

    if is_properties:
        # load again immediately before save
        properties = fileload('../properties.json')
        properties['elastic'] = solved
        filedump(properties, '../properties.json')
