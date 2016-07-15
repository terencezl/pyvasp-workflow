import os
import shutil
import numpy as np
import run_module as rmd
import run_module_elastic as rmd_e
import pymatgen as mg
from subprocess import call


if __name__ == '__main__':
    """

    Run a single strain set with changing delta values in python level parallel
    submission mode.

    You should set a 'elastic' tag in the specs file, like

        elastic:
          cryst_sys: cubic
          test_type: c11-c12

    The 'test_type' tag defines the name of the strain set, whose mathematical
    form is detailed in run_module_elastic.py.

    After this VASP run for a specific strain set, you need to use the process
    script process_elastic_single.py to fit the energy values to a polynomial,
    extract the parameters and plot figures.

    And then, after this kind of VASP run and process for all the independent
    strain sets, you need to use the process script process_elastic_solve.py to
    obtain the elastic constants.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    cwd = os.getcwd()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)

    test_type_input = run_specs['elastic']['test_type']
    cryst_sys = run_specs['elastic']['cryst_sys']

    rmd.infer_from_json(run_specs)
    structure = rmd.get_structure(run_specs)
    incar = rmd.read_incar(run_specs)
    kpoints = rmd.read_kpoints(run_specs, structure)

    is_mag = incar['ISPIN'] == 2 if 'ISPIN' in incar else False

    test_type_list, strain_list, delta_list = rmd_e.get_test_type_strain_delta_list(cryst_sys)
    for test_type, strain, delta in zip(test_type_list, strain_list, delta_list):
        if test_type == test_type_input:
            rmd.chdir(test_type)
            for ind, value in enumerate(delta):
                rmd.chdir(str(value))
                rmd.init_stdout()
                incar.write_file('INCAR')
                kpoints.write_file('KPOINTS')
                lattice_modified = mg.Lattice(
                    np.dot(structure.lattice_vectors(), strain(value)))
                structure_copy = structure.copy()
                structure_copy.modify_lattice(lattice_modified)
                structure_copy.to(filename='POSCAR')
                rmd.write_potcar(run_specs)
                job = test_type + '-' + str(value)
                shutil.copy(cwd + '/INPUT/deploy.job', job)
                call('sed -i "/python/c time ' + rmd.VASP_EXEC + ' 2>&1 | tee -a stdout" ' + job, shell=True)
                call('M ' + job, shell=True)
                os.remove(job)
                os.chdir('..')
            os.chdir('..')
