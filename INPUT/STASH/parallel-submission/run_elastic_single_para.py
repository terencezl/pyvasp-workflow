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

    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    properties = fileload('../properties.json')
    V0 = properties['V0']
    incar = read_incar(run_spec)
    kpoints = read_kpoints(run_spec)
    is_mag = detect_is_mag(properties['mag'])
    if is_mag:
        incar.update({'ISPIN': 2})
    else:
        incar.update({'ISPIN': 1})

    if os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
    elif os.path.isfile('nostrain/CONTCAR'):
        structure = mg.Structure.from_file('nostrain/CONTCAR')
    else:
        structure = generate_structure(run_spec)
        structure.scale_lattice(V0)

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
                shutil.copy('../../../../INPUT/deploy.job', job)
                call('sed -i "/python/c time ' + VASP + ' > stdout" ' + job, shell=True)
                call('sed -i "/#BSUB -o/c #BSUB -o $PWD/' + job + '.o%J" ' + job, shell=True)
                call('sed -i "/#BSUB -e/c #BSUB -e $PWD/' + job + '.o%J" ' + job, shell=True)
                call('sed -i "/#BSUB -J/c #BSUB -J ' + job + '" ' + job, shell=True)
                call('bsub <' + job, shell=True)
                os.chdir('..')
            os.chdir('..')
