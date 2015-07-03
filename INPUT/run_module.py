import os
import sys
import shutil
from subprocess import call
import re
import json
import yaml
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
try:
  plt.style.use('research')
except ValueError:
  pass
import pymatgen as mg

POTENTIAL_DATABASE = 'PATH-TO-YOUR-POTENTIAL-DATABASE'
VASP = 'PATH-TO-YOUR-EXECUTABLE'

template_dir = os.path.join(os.getcwd(), 'INPUT/TEMPLATES')


def fileload(filename):
    with open(filename, 'r') as f:
        if filename.endswith('.json'):
            file_dict = json.load(f)
        elif filename.endswith('.yaml'):
            file_dict = yaml.load(f)
    return file_dict


def filedump(dict_to_file, filename):
    with open(filename, 'w') as f:
        if filename.endswith('.json'):
            json.dump(dict_to_file, f, indent=4)
        elif filename.endswith('.yaml'):
            yaml.dump(dict_to_file, f, default_flow_style=False)
        else:
            raise IOError("Can't read file!")


def chdir(dirname):
    try:
        os.makedirs(dirname)
    except OSError:
        if not os.path.isdir(dirname):
            raise OSError
    os.chdir(dirname)


def init_stdout():
    """
    Empty the stdout file and record working directory.
    """
    call('echo "Working directory: $PWD" | tee stdout', shell=True)


def enter_main_dir(run_spec):
    """
    Enter the run directory.
    """
    dirname = run_spec['structure'] + '-' + '+'.join(run_spec['elem_types'])
    chdir(os.path.join(dirname, run_spec['run_subdir']))


def run_vasp():
    """
    Run vasp.
    """
    time_format = ' "\n----------\nreal     %E" '
    time = '/usr/bin/time -f ' + time_format
    run = call(time + VASP + ' 2>&1 | tee -a stdout', shell=True)
    if run != 0:
        sys.exit(1)
    hbreak = ' "\n' + '=' * 100 + '\n" '
    call('echo -e ' + hbreak + ' | tee -a stdout', shell=True)


def read_incar(run_spec):
    """
    Read INCAR.
    """
    incar = mg.io.vaspio.Incar()
    if 'incar' in run_spec and run_spec['incar']:
        incar.update(run_spec['incar'])
    return incar


def read_kpoints(run_spec):
    """
    Read KPOINTS.
    """
    kpoints = mg.io.vaspio.Kpoints.monkhorst_automatic([11, 11, 11])
    if 'kpoints' in run_spec and run_spec['kpoints']:
        kpoints_spec = run_spec['kpoints']
        if kpoints_spec['mode'] == 'M':
            kpoints = mg.io.vaspio.Kpoints.monkhorst_automatic(kpoints_spec['divisions'])
        elif kpoints_spec['mode'] == 'G':
            kpoints = mg.io.vaspio.Kpoints.gamma_automatic(kpoints_spec['divisions'])
    return kpoints


def write_potcar(run_spec):
    """
    Write POTCAR.
    """
    potential_base = os.path.join(POTENTIAL_DATABASE, run_spec['pot_type'])
    with open('POTCAR', 'wb') as outfile:
        for filename in [os.path.join(potential_base, e, 'POTCAR') for e in run_spec['elem_types']]:
            with open(filename, 'rb') as infile:
                shutil.copyfileobj(infile, outfile)


def generate_structure(run_spec):
    """
    Generate pymatgen.Structure.
    """
    poscar_dict = run_spec['poscar']
    elem_types_struct = [re.sub(r'_.*', '', i) for i in run_spec['elem_types']]
    if 'template' in poscar_dict and poscar_dict['template']:
        poscar = mg.io.vaspio.Poscar.from_file(os.path.join(template_dir, poscar_dict['template']))
        structure = poscar.structure
        for i, item in enumerate(structure.symbol_set):
            structure.replace_species({item: elem_types_struct[i]})
        return structure

    cryst_sys = poscar_dict['cryst_sys']
    lattice_params = poscar_dict['lattice_params']
    if cryst_sys == 'cubic':
        lattice = mg.Lattice.cubic(lattice_params['a'])
    elif cryst_sys == 'hexagonal':
        lattice = mg.Lattice.hexagonal(lattice_params['a'], lattice_params['alpha'])
    elif cryst_sys == 'tetragonal':
        lattice = mg.Lattice.tetragonal(lattice_params['a'], lattice_params['c'])
    elif cryst_sys == 'orthorhombic':
        lattice = mg.Lattice.orthorhombic(lattice_params['a'], lattice_params['b'], lattice_params['c'])
    elif cryst_sys == 'rhombohedral':
        lattice = mg.Lattice.rhombohedral(lattice_params['a'], lattice_params['alpha'])
    elif cryst_sys == 'monoclinic':
        lattice = mg.Lattice.orthorhombic(lattice_params['a'], lattice_params['b'], lattice_params['c'],
            lattice_params['beta'])
    else:
        lattice = mg.Lattice.orthorhombic(lattice_params['a'], lattice_params['b'], lattice_params['c'],
            lattice_params['alpha'], lattice_params['beta'], lattice_params['gamma'])

    elem_types_struct_multi = []
    for i, elem in enumerate(elem_types_struct):
        elem_types_struct_multi.extend([elem] * poscar_dict['atoms_multi'][i])

    structure = mg.Structure.from_spacegroup(poscar_dict['spacegroup'], lattice,
            elem_types_struct_multi, poscar_dict['atoms_direct_locs'])
    return structure


def detect_is_mag(mag):
    if isinstance(mag, np.ndarray):
        is_mag = (np.abs(mag) >= 0.001).any()
    elif isinstance(mag, float) or isinstance(mag, int):
        is_mag = np.abs(mag) >= 0.001
    return is_mag


def get_test_type_strain_delta_list(cryst_sys):
    """
    Generate elastic strain.
    """
    strain_list = []

    if cryst_sys == 'cubic':
        test_type_list = ["c11+2c12", "c11-c12", "c44"]
        delta_list = np.ones(((3, 5))) * [0, -0.02, 0.02, -0.03, 0.03]
        delta_list[0] = delta_list[0]/np.sqrt(3)

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1 + delta, 0],
                                                   [0, 0, 1 + delta]]))

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1 - delta, 0],
                                                   [0, 0, 1 + delta ** 2 / (1 - delta ** 2)]]))

        strain_list.append(lambda delta: np.array([[1, delta/2, 0],
                                                   [delta/2, 1, 0],
                                                   [0, 0, 1 + delta ** 2 / (4 - delta ** 2)]]))

    elif cryst_sys == 'hexagonal':
        test_type_list = ["2c11+2c12+4c13+c33", "c11-c12", "c11+c12", "c44", "c33"]
        delta_list = np.ones(((5, 5))) * [0, -0.02, 0.02, -0.03, 0.03]

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1 + delta, 0],
                                                   [0, 0, 1 + delta]]))

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1 - delta, 0],
                                                   [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1 + delta, 0],
                                                   [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                                   [0, 1, delta],
                                                   [0, delta, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                                   [0, 1, 0],
                                                   [0, 0, 1 + delta]]))

    elif cryst_sys == 'tetragonal':
        test_type_list = ["c11", "c33", "c44",
                "5c11-4c12-2c13+c33", "c11+c12-4c13+2c33", "c11+c12-4c13+2c33+2c66"]
        delta_list = np.ones(((6, 5))) * [0, -0.02, 0.02, -0.03, 0.03]
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
        delta_list = np.ones(((9, 5))) * [0, -0.02, 0.02, -0.03, 0.03]

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
                                                   [0, 1, delta/2],
                                                   [0, delta/2, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, delta/2],
                                                   [0, 1, 0],
                                                   [delta/2, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, delta/2, 0],
                                                   [delta/2, 1, 0],
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
    """
    Solve for the elastic constants from the matrix and coeffs.
    """
    if cryst_sys == 'cubic':
        econsts_str = ["C11", "C12", "C44"]
        coeff_matrix = np.array([[3/2., 3, 0],
                                 [1, -1, 0],
                                 [0, 0, 1/2.]])

    elif cryst_sys == 'hexagonal':
        econsts_str = ["C11", "C12", "C13", "C33", "C44"]
        coeff_matrix = np.array([[1, 1, 2, 1/2., 0],
                                 [1, -1, 0, 0, 0],
                                 [1, 1, 0, 0, 0],
                                 [0, 0, 0, 0, 2],
                                 [0, 0, 0, 1/2., 0]])

    elif cryst_sys == 'tetragonal':
        econsts_str = ["C11", "C33", "C44", "C12", "C13", "C66"]
        coeff_matrix = np.array([[1/2., 0, 0, 0, 0, 0],
                                 [0, 1/2., 0, 0, 0, 0],
                                 [0, 0, 2, 0, 0, 0],
                                 [5 / 2., 1/2., 0, -2, -1, 0],
                                 [1, 2, 0, 1, -4, 0],
                                 [1, 2, 0, 1, -4, 2]])

    elif cryst_sys == 'orthorhombic':
        econsts_str = ["C11", "C22", "C33", "C44", "C55", "C66", "C12", "C13", "C23"]
        coeff_matrix = np.array([[1/2., 0, 0, 0, 0, 0, 0, 0, 0],
                                 [0, 1/2., 0, 0, 0, 0, 0, 0, 0],
                                 [0, 0, 1/2., 0, 0, 0, 0, 0, 0],
                                 [0, 0, 0, 1/2., 1, 0, 0, 0, 0],
                                 [0, 0, 0, 0, 1/2., 0, 0, 0, 0],
                                 [0, 0, 0, 0, 0, 1/2., 0, 0, 0],
                                 [2, 1/2., 1/2., 0, 0, 0, -2, -2, 1],
                                 [1/2., 2, 1/2., 0, 0, 0, -2, 1, -2],
                                 [1/2., 1/2., 2, 0, 0, 0, 1, -2, -2]])

    solved = np.linalg.solve(coeff_matrix, combined_econst_array)
    return dict(zip(econsts_str, solved))
