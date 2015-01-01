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


def get_test_type_strain_delta_list(cryst_sys):
    if cryst_sys == 'cubic':
        test_type_list = ["c11+2c12", "c11-c12", "c44"]
        strain_list = []
        delta_list = np.ones(((3, 3))) * [0, -0.03, 0.03]
        delta_list[0] = delta_list[0]/np.sqrt(3)

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                          [0, 1 + delta, 0],
                                          [0, 0, 1 + delta]]))

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                          [0, 1 - delta, 0],
                                          [0, 0, 1 + delta ** 2 / (1 - delta ** 2)]]))

        strain_list.append(lambda delta: np.array([[1, delta / 2., 0],
                                          [delta / 2., 1, 0],
                                          [0, 0, 1 + delta ** 2 / (4 - delta ** 2)]]))

    elif cryst_sys == 'hexagonal':
        pass


    elif cryst_sys == 'tetragonal':
        test_type_list = ["c11", "c33", "c44",
                "5c11-4c12-2c13+c33", "c11+c12-4c13+2c33", "c11+c12-4c13+2c33+2c66"]
        strain_list = []
        delta_list = np.ones(((6, 3))) * [0, -0.03, 0.03]
        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                          [0, 1, 0],
                                          [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                          [0, 1, 0],
                                          [0, 0, 1 + delta]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                          [0, 1, delta],
                                          [0, delta, 1]]))

        strain_list.append(lambda delta: np.array([[1 + 2 * delta, 0, 0],
                                          [0, 1 - delta, 0],
                                          [0, 0, 1 - delta]]))

        strain_list.append(lambda delta: np.array([[1 - delta, 0, 0],
                                          [0, 1 - delta, 0],
                                          [0, 0, 1 + 2 * delta]]))

        strain_list.append(lambda delta: np.array([[1 + delta, delta, 0],
                                          [delta, 1 + delta, 0],
                                          [0, 0, 1 - 2 * delta]]))

    elif cryst_sys == 'orthorhombic':
        test_type_list = ["c11", "c22", "c33", "c44", "c55", "c66",
            "4c11-4c12-4c13+c22+2c23+c33", "c11-4c12+2c13+4c22-4c23+c33", "c11+2c12-4c13+c22-4c23+4c33"]
        strain_list = []
        delta_list = np.ones(((9, 3))) * [0, -0.03, 0.03]

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                          [0, 1, 0],
                                          [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                          [0, 1 + delta, 0],
                                          [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                          [0, 1, 0],
                                          [0, 0, 1 + delta]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                          [0, 1, delta / 2],
                                          [0, delta / 2, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, delta / 2],
                                          [0, 1, 0],
                                          [delta / 2, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, delta / 2, 0],
                                          [delta / 2, 1, 0],
                                          [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1 + 2 * delta, 0, 0],
                                          [0, 1 - delta, 0],
                                          [0, 0, 1 - delta]]))

        strain_list.append(lambda delta: np.array([[1 - delta, 0, 0],
                                          [0, 1 + 2 * delta, 0],
                                          [0, 0, 1 - delta]]))

        strain_list.append(lambda delta: np.array([[1 - delta, delta, 0],
                                          [delta, 1 - delta, 0],
                                          [0, 0, 1 + 2 * delta]]))

    return test_type_list, strain_list, delta_list


def solve(cryst_sys, combined_econst_array):
    if cryst_sys == 'cubic':
        econsts_str = ["C11", "C12", "C44"]
        coeff_matrix = np.array([[3/2., 3, 0],
                                 [1, -1, 0],
                                 [0, 0, 1 / 2.]])

    elif cryst_sys == 'hexagonal':
        pass

    elif cryst_sys == 'tetragonal':
        econsts_str = ["C11", "C33", "C44", "C12", "C13", "C66"]
        coeff_matrix = np.array([[1 / 2., 0, 0, 0, 0, 0],
                                 [0, 1 / 2., 0, 0, 0, 0],
                                 [0, 0, 2, 0, 0, 0],
                                 [5 / 2., 1 / 2., 0, -2, -1, 0],
                                 [1, 2, 0, 1, -4, 0],
                                 [1, 2, 0, 1, -4, 2]])

    elif cryst_sys == 'orthorhombic':
        econsts_str = ["C11", "C22", "C33", "C44", "C55", "C66", "C12", "C13", "C23"]
        coeff_matrix = np.array([[1 / 2., 0, 0, 0, 0, 0, 0, 0, 0],
                                 [0, 1 / 2., 0, 0, 0, 0, 0, 0, 0],
                                 [0, 0, 1 / 2., 0, 0, 0, 0, 0, 0],
                                 [0, 0, 0, 1 / 2., 1, 0, 0, 0, 0],
                                 [0, 0, 0, 0, 1 / 2., 0, 0, 0, 0],
                                 [0, 0, 0, 0, 0, 1 / 2., 0, 0, 0],
                                 [2, 1 / 2., 1 / 2., 0, 0, 0, -2, -2, 1],
                                 [1 / 2., 2, 1 / 2., 0, 0, 0, -2, 1, -2],
                                 [1 / 2., 1 / 2., 2, 0, 0, 0, 1, -2, -2]])

    solved = np.linalg.solve(coeff_matrix, combined_econst_array)
    return dict(zip(econsts_str, solved))


if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename) as f:
        run_spec = yaml.load(f)
    cryst_sys = run_spec['elastic']['cryst_sys']

    enter_main_dir(run_spec)
    with open('properties.json', 'r') as f:
        properties = json.load(f)

    (incar, kpoints) = read_incar_kpoints(run_spec)
    if not properties['is_mag']:
        incar.update({'ISPIN': 1})
    structure = generate_structure(run_spec)
    structure.scale_lattice(properties['V0'])

    chdir('elastic_run_energy')
    combined_econst_array = []
    for test_type, strain, delta in \
                zip(*get_test_type_strain_delta_list(cryst_sys)):
        chdir(test_type)
        energy = np.zeros(len(delta))
        energy[0] = properties['E0_equi-relax']
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
            energy[ind+1] = mg.io.vaspio.Oszicar('OSZICAR').final_energy

        fitting_result = pydass_vasp.fitting.polyfit(delta, energy, 2, save_figs=True)
        combined_econst_array.append(fitting_result['coeffs'][2])
        os.chdir('..')

    combined_econst_array = np.array(combined_econst_array) * 160.2 / properties['V0']
    solved = solve(cryst_sys, combined_econst_array)
    with open('elastic.json', 'w') as f:
        json.dump(solved, f, indent=4)
    os.chdir('..')

    properties['elastic'] = {}
    properties['elastic'].update(solved)
    with open('properties.json', 'w') as f:
        json.dump(properties, f, indent=4)
