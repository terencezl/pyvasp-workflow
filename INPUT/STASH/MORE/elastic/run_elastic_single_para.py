import os
import sys
import shutil
import numpy as np
from run_module import *
from run_module_elastic import *
import pymatgen as mg
import pydass_vasp
from subprocess import call


if __name__ == '__main__':
    run_specs, filename = get_run_specs_and_filename()
    cwd = os.getcwd()
    chdir(get_run_dir(run_specs))
    filedump(run_specs, filename)

    test_type_input = run_specs['elastic']['test_type']
    cryst_sys = run_specs['elastic']['cryst_sys']
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
        structure = generate_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = read_kpoints(run_specs, structure)

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
                write_potcar(run_specs)
                job = test_type + '-' + str(value)
                shutil.copy(cwd + '/INPUT/deploy.job', job)
                call('sed -i "/python/c time ' + VASP_EXEC + ' 2>&1 | tee -a stdout" ' + job, shell=True)
                call('M ' + job, shell=True)
                os.remove(job)
                os.chdir('..')
            os.chdir('..')
