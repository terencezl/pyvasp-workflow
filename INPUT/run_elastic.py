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
from run_module import detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure, get_test_type_strain_delta_list, solve


def central_2nd_poly(X, a, c):
    return a * X**2 + c

if __name__ == '__main__':
    filename = sys.argv[1]
    subdirname = sys.argv[2]
    run_spec = fileload(filename)
    cryst_sys = run_spec['poscar']['cryst_sys']
    enter_main_dir(run_spec)

    properties = fileload('properties.json')
    V0 = properties['V0']
    is_mag = detect_is_mag(properties['mag'])
    (incar, kpoints) = read_incar_kpoints(run_spec)
    if not is_mag:
        incar.update({'ISPIN': 1})

    if os.path.isfile('POSCAR'):
        structure = mg.Structure.from_file('POSCAR')
    else:
        structure = generate_structure(run_spec)
        structure.scale_lattice(V0)

    chdir(subdirname)
    combined_econst_array = []
    mags_dict = {}
    fitting_result_to_json = {}

    chdir('nostrain')
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()
    oszicar = mg.io.vaspio.Oszicar('OSZICAR')
    energy_nostrain = oszicar.final_energy
    if is_mag:
        mag_nostrain = oszicar.ionic_steps[-1]['mag']
    chdir('..')

    for test_type, strain, delta in \
                zip(*get_test_type_strain_delta_list(cryst_sys)):
        chdir(test_type)
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
            oszicar = mg.io.vaspio.Oszicar('OSZICAR')
            energy[ind+1] = oszicar.final_energy
            if is_mag:
                mag[ind+1] = oszicar.ionic_steps[-1]['mag']

        mags_dict[test_type] = mag.tolist()
        fitting_result = pydass_vasp.fitting.curve_fit(central_2nd_poly, delta, energy, save_figs=True,
                    output_prefix=test_type)
        combined_econst_array.append(fitting_result['params'][0])
        fitting_result['params'] = fitting_result['params'].tolist()
        fitting_result.pop('fitted_data')
        fitting_result_to_json[test_type] = fitting_result
        shutil.copy(test_type + '.pdf', '..')
        os.chdir('..')

    combined_econst_array = np.array(combined_econst_array) * 160.2 / V0
    solved = solve(cryst_sys, combined_econst_array)
    filedump(solved, 'elastic.json')
    filedump(fitting_result_to_json, 'fitting_result.json')
    if is_mag:
        filedump(mags_dict, 'mags.json')
    os.chdir('..')

    properties['elastic'] = solved
    filedump(properties, 'properties.json')
