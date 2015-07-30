import os
import sys
import shutil
import numpy as np
from run_module import *
import pymatgen as mg
import pydass_vasp
from subprocess import call


def central_poly(X, a, b, c):
    return b * X**3 + a * X**2 + c

if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    test_type_input = run_spec['elastic']['test_type']
    cryst_sys = run_spec['elastic']['cryst_sys']

    cwd = os.getcwd()
    enter_main_dir(run_spec)
    filedump(run_spec, filename)

    incar = read_incar(run_spec)
    if os.path.isfile(('../properties.json')):
        is_properties = True
        properties = fileload('../properties.json')

    if 'ISPIN' in incar:
        is_mag = incar['ISPIN'] == 2
    else:
        if is_properties:
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

    test_type_list, strain_list, delta_list = get_test_type_strain_delta_list(cryst_sys)
    for test_type, strain, delta in zip(test_type_list, strain_list, delta_list):
        if test_type == test_type_input:
            chdir(test_type)
            init_stdout()
            for ind, value in enumerate(delta):
                chdir(str(value))
                incar.write_file('INCAR')
                kpoints.write_file('KPOINTS')
                lattice_modified = mg.Lattice(
                    np.dot(structure.lattice_vectors(), strain(value)))
                structure_copy = structure.copy()
                structure_copy.modify_lattice(lattice_modified)
                structure_copy.to(filename='POSCAR')
                write_potcar(run_spec)
                job = test_type + '-' + str(value)
                shutil.copy(cwd + '/INPUT/deploy.job', job)
                call('sed -i "/python/c time ' + VASP + ' 2>&1 | tee -a stdout" ' + job, shell=True)
                call('M ' + job, shell=True)
                os.remove(job)
                os.chdir('..')
            os.chdir('..')
