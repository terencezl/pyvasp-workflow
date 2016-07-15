import os
import sys
import argparse
import warnings
import shutil
from subprocess import call
import re
import json
import yaml
import numpy as np
import matplotlib
matplotlib.use('Agg')
import datetime
import pymatgen as mg

# environmental variable or manual setting these lines required
VASP_EXEC = os.getenv('VASP_EXEC', 'OR-PATH-TO-YOUR-VASP-EXEC-default')
VASP_POTENTIALS_DIR = os.getenv('VASP_POTENTIALS_DIR', 'OR-PATH-TO-YOUR-VASP_POTENTIALS_DIR-default')
# environmental variable optional, default to INPUT/TEMPLATES
VASP_TEMPLATES_DIR = os.getenv('VASP_TEMPLATES_DIR', os.path.join(os.getcwd(), 'INPUT/TEMPLATES'))


def fileload(filename):
    """

    Load a json or specs file, determined by the extension.

    """

    with open(filename, 'r') as f:
        if filename.endswith('.json'):
            file_dict = json.load(f)
        elif filename.endswith('.yaml'):
            file_dict = yaml.load(f)
    return file_dict


def filedump(dict_to_file, filename):
    """

    Dump a json or specs file, determined by the extension. Indentation of json
    and flow style of yaml is set.

    """

    with open(filename, 'w') as f:
        if filename.endswith('.json'):
            json.dump(dict_to_file, f, indent=4)
        elif filename.endswith('.yaml'):
            yaml.dump(dict_to_file, f, default_flow_style=False)


def chdir(dirname):
    """

    Enter a path. If it does not exist, create one recursively and enter.

    """

    os.makedirs(dirname, exist_ok=True)
    os.chdir(dirname)


def get_run_specs_and_filename():
    """

    Parse the sys.argv list, return the run_specs object from the specs file, and
    its filename.

    If the --remove_file option is turned on, remove the specs file. This is
    useful when you use a shell submission trigger file and has a temporary copy
    of a specs file that should be removed once it's used. By default the file is
    not removed.

    """

    parser = argparse.ArgumentParser()
    parser.add_argument('filepath', help='path of the specs file')
    parser.add_argument('--remove_file', action='store_true', help="if remove the specs file")
    args = parser.parse_args()

    run_specs = fileload(args.filepath)
    filename = os.path.basename(args.filepath)
    if args.remove_file:
        os.remove(filename)

    return run_specs, filename


def get_run_dir(run_specs):
    """

    Get the directory where the routine takes place.

    If 'run_dir' is in the specs file, use that.

    Otherwise, use a naming scheme that combines 'structure' and 'elem_types',
    like rocksalt-Ti_sv+N. If either 'run_supdir' or 'run_subdir' exist, wrap up
    this naming scheme with them. Not recommended.

    If none of the two exists, name it 'vasp_test'.

    """

    if 'run_dir' in run_specs:
        dirname = run_specs['run_dir']
    elif 'structure' in run_specs and 'elem_types' in run_specs:
        dirname = run_specs['structure'] + '-' + '+'.join(run_specs['elem_types'])
        if 'run_subdir' in run_specs:
            dirname = os.path.join(dirname, run_specs['run_subdir'])
        if 'run_supdir' in run_specs:
            dirname = os.path.join(run_specs['run_supdir'], dirname)
    else:
        dirname = 'vasp_test'

    return dirname


def enter_main_dir(run_specs):
    warnings.warn("Please use get_run_dir() instead.", DeprecationWarning)
    chdir(get_run_dir(run_specs))


def init_stdout():
    """

    Create a new stdout file and record working directory.

    """

    # stdout_str = 'stdout_' + datetime.datetime.now().isoformat(sep='-') + '.out'
    call('echo "Working directory: $PWD" | tee stdout', shell=True)


def run_vasp():
    """

    Run VASP, time it, print out to screen, and append it to a file named
    'stdout'. You need to set the VASP_EXEC environmental variable, or edit
    the head of this file to be able to use it.

    """

    time_format = ' "\n----------\nreal     %E" '
    time = '/usr/bin/time -f ' + time_format
    run = call(time + VASP_EXEC + ' 2>&1 | tee -a stdout', shell=True)
    if run != 0:
        sys.exit(1)
    hbreak = ' "\n' + '=' * 100 + '\n" '
    call('echo -e ' + hbreak + ' | tee -a stdout', shell=True)


def detect_is_mag(mag, tol=1e-3):
    """

    Detect if any of a list/numpy array, or a float/int value of magnetic
    moments is larger than some criterion (tol optional argument). Return the
    boolean.

    """

    if isinstance(mag, list) or isinstance(mag, np.ndarray):
        is_mag = (np.abs(mag) >= tol).any()
    elif isinstance(mag, float) or isinstance(mag, int):
        is_mag = np.abs(mag) >= tol
    return is_mag


def infer_from_json(run_specs):
    """

    Specify a relative path to the run_dir in the specs file, under the tag of
    "infer_from_json".

    Infer some information not given in the specs file from a specified json
    file, if that file exists. Adjust run_specs.

    e.g. If ISPIN is not specified in the yaml file, try the 'mag' key in the
    json file.

    """

    if 'infer_from_json' in run_specs:
        properties = fileload(run_specs['infer_from_json'])
        incar = run_specs['incar']
        if 'ISPIN' not in incar:
            if detect_is_mag(properties['mag']):
                incar.update({'ISPIN': 2})
            else:
                incar.update({'ISPIN': 1})

        run_specs['poscar']['volume'] = properties['V0']


def read_incar(run_specs):
    """

    Read contents of 'incar' from the specs file. If 'incar' does not exist,
    return an empty Incar object, still functional.

    """

    incar = mg.io.vasp.Incar()
    if 'incar' in run_specs and run_specs['incar']:
        incar.update(run_specs['incar'])
    return incar


def read_kpoints(run_specs, structure=None):
    """

    Read contents of 'kpoints' from the specs file. If 'kpoints' does not
    exist, return an automatic (A) mesh with 5 subdivisions along each
    reciprocal vector.

    If 'kpoints' exists, it follows the sequence below.

    If 'density' exists in 'kpoints', automatic density mesh is returned, with
    density being KPPRA. In this case you need to provide the structure as an
    argument. 'force_gamma' can be specified to True.

    Otherwise, if 'divisions', specified as a list, exists in 'kpoints', MP mesh or Gamma-centered
    mesh is returned, according to 'mode' that starts with 'M' or 'G'.

    """

    kpoints = mg.io.vasp.Kpoints.automatic(5)
    if 'kpoints' in run_specs and run_specs['kpoints']:
        kpoints_spec = run_specs['kpoints']
        if 'density'in kpoints_spec:
            if 'force_gamma'in kpoints_spec:
                force_gamma = kpoints_spec['force_gamma']
            else:
                force_gamma = False
            kpoints = mg.io.vasp.Kpoints.automatic_density(structure, kpoints_spec['density'],
                force_gamma=force_gamma)
        elif 'divisions' in kpoints_spec:
            if kpoints_spec['mode'].upper().startswith('M'):
                kpoints = mg.io.vasp.Kpoints.monkhorst_automatic(kpoints_spec['divisions'])
            elif kpoints_spec['mode'].upper().startswith('G'):
                kpoints = mg.io.vasp.Kpoints.gamma_automatic(kpoints_spec['divisions'])
    return kpoints


def get_structure(run_specs):
    """

    Get pymatgen.Structure. There are many ways to get a structure. They are all
    specified under 'poscar' tag in the specs file. There are two ways to get a
    structure.

    1. From an already made structure, either from a template POSCAR, or a
    Materials Project database entry. (Recommended)

    If 'template' is present in 'poscar', you can either set the
    VASP_TEMPLATES_DIR environmental variable, or just leave it to the default
    'INPUT/TEMPLATES'. After that, this specified POSCAR-type template file path
    will be used to obtain the structure from the VASP_TEMPLATES_DIR, and a
    structure is returned. If you set 'rel_to_run_dir' to True, 'template'
    refers to the file relative to the 'run_dir'.

    If 'material_id' is present in 'poscar', MAPI_KEY environmental variable
    needs to be set according to the Materials Project (materialsproject.org).

    An optional 'get_structure' can be set to one of

        ['primitive', 'reduced', 'sorted', 'conventional_standard',
         'primitive_standard', 'refined']

    For 'primitive', 'conventional_standard' and so on, an additional tag 'prec'
    controls the tolerence/symmetry finding precision threshold.

    The 'primitive', 'reduced' and 'sorted' are methods of the object
    pmg.Structure, while the rest are methods of
    pmg.symmetry.analyzer.SpacegroupAnalyzer. Please refer to the pymatgen docs
    to see what they are exactly. Be careful about whether the resultent
    structure is what you want. When in doubt, always manually run the pymatgen
    commands and see the outcome.

    By default, the code uses the element types written in the structure to
    generate the POTCAR by maintaining the existence of 'elem_types'. However,
    if you set 'repl_elems' with a dict, like {N: C, Ti: Ti_sv}, the elements in
    the structure will be accordingly replaced and the necessary mechanism is in
    place to make sure POTCAR is to be generated with the flavored potentials.

    Setting 'elem_types' in the specs file as a list of potentials (can have
    flavors like Ti_sv) in the same sequence as in the structure also works, but
    one has to be careful to match the sequence correctly. Not recommended.

    An optional 'volume' can be set to scale the structure of the template.

    2. From manual description. (Cumbersome)

    The manual generation from spacegroup is done by specifying

    'spacegroup' (international number or symbol)

    'cryst_sys' (one of the seven)

    'lattice_params' ('a', 'b', 'c', 'alpha', 'beta', 'gamma', some of which
    'can be omitted because of a more symmetric crystallographic system)

    'elem_types' (the elements in the structure, which can be flavored
    'potentials, e.g. Ti_sv)

    'atoms_multitude' (multitude of atoms of the same element type in a list,
    'the sequence following 'elem_types'. Only symmetrically distinct species and
    'coords should be provided, according to the Wychoff positions)

    'atoms_direct_coords' (direct locations, relative to the lattice vectors
    'of the symmetrically distinct atoms. There should be the same number of
    'them as the sum of atoms_multitude)

    """

    is_template = None
    is_material_id = None
    poscar_specs = run_specs['poscar']

    if 'template' in poscar_specs:
        is_template = True
        if 'rel_to_run_dir' in poscar_specs and poscar_specs['rel_to_run_dir']:
            poscar = mg.io.vasp.Poscar.from_file(poscar_specs['template'])
        else:
            poscar = mg.io.vasp.Poscar.from_file(os.path.join(VASP_TEMPLATES_DIR, poscar_specs['template']))
        structure = poscar.structure
    elif 'material_id' in poscar_specs:
        is_material_id = True
        m = mg.MPRester()
        structure = m.get_structure_by_material_id(poscar_specs['material_id'])
    if is_template or is_material_id:
        if 'get_structure' in poscar_specs:
            prec = poscar_specs['prec'] if 'prec' in poscar_specs else 0.01
            sga = mg.symmetry.analyzer.SpacegroupAnalyzer(structure, symprec=prec)
            if poscar_specs['get_structure'] == 'sorted':
                structure = structure.get_sorted_structure()
            if poscar_specs['get_structure'] == 'reduced':
                structure = structure.get_reduced_structure()
            elif poscar_specs['get_structure'] == 'primitive':
                structure = structure.get_primitive_structure(prec)
            elif poscar_specs['get_structure'] == 'primitive_standard':
                structure = sga.get_primitive_standard_structure()
            elif poscar_specs['get_structure'] == 'conventional_standard':
                structure = sga.get_conventional_standard_structure()
            elif poscar_specs['get_structure'] == 'refined':
                structure = sga.get_refined_structure()

        if 'elem_types' not in run_specs:
            symbol_set = list(structure.symbol_set)
            if 'repl_elems' in run_specs:
                for idx, symbol in enumerate(symbol_set):
                    if symbol in run_specs['repl_elems']:
                        symbol_set[idx] = run_specs['repl_elems'][symbol]
                repl_elems_struct = {key: re.sub(r'_.*', '', value) for key, value in run_specs['repl_elems'].items()}
                structure.replace_species(repl_elems_struct)
            run_specs['elem_types'] = symbol_set
        else:
            # deprecated
            elem_types_struct = [re.sub(r'_.*', '', i) for i in run_specs['elem_types']]
            for i, item in enumerate(structure.symbol_set):
                structure.replace_species({item: elem_types_struct[i]})

        if 'volume' in poscar_specs:
            structure.scale_lattice(poscar_specs['volume'])
        return structure
    else:
        cryst_sys = poscar_specs['cryst_sys']
        lattice_params = poscar_specs['lattice_params']
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

        elem_types_struct = [re.sub(r'_.*', '', i) for i in poscar_specs['elem_types']]
        elem_types_struct_multi = []
        for i, elem in enumerate(elem_types_struct):
            elem_types_struct_multi.extend([elem] * poscar_specs['atoms_multitude'][i])

        structure = mg.Structure.from_spacegroup(poscar_specs['spacegroup'], lattice,
                elem_types_struct_multi, poscar_specs['atoms_direct_coords'])
        return structure


def generate_structure(run_specs):
    warnings.warn("Please use get_structure() instead.", DeprecationWarning)
    return get_structure(run_specs)


def write_potcar(run_specs):
    """

    Write POTCAR. It gets the POTCAR types from 'elem_types' in the specs file.
    You need to set the VASP_POTENTIALS_DIR environmental variable, or edit
    the head of this file to be able to use it.

    """

    potential_base = os.path.join(VASP_POTENTIALS_DIR, run_specs['pot_type'])
    with open('POTCAR', 'wb') as outfile:
        for filename in [os.path.join(potential_base, e, 'POTCAR') for e in run_specs['elem_types']]:
            with open(filename, 'rb') as infile:
                shutil.copyfileobj(infile, outfile)


def get_max_ENMAX(potcars):
    """

    Get the largest ENMAX from POTCAR.

    """
    max_ENMAX = 0
    for potcar in potcars:
        if potcar.keywords['ENMAX'] > max_ENMAX:
            max_ENMAX = potcar.keywords['ENMAX']
    return max_ENMAX
