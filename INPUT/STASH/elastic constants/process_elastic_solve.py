import os
import numpy as np
import run_module as rmd
import run_module_elastic as rmd_e
import pymatgen as mg

if __name__ == '__main__':
    """

    Linearly solve for the elastic constants.

    Not a VASP run script that requires a job submission. You can directly use
    it as

        INPUT/process_elastic_solve.py INPUT/run_elastic_single.yaml

    to read a specs file at INPUT/run_elastic_single.yaml, which is the file you
    would use to actually run the routine script run_elastic_single.py and the
    process script process_elastic_single.py for all the independent strain
    sets before this.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))

    cryst_sys = run_specs['elastic']['cryst_sys']
    is_properties = None
    if os.path.isfile(('../properties.json')):
        is_properties = True
        properties = rmd.fileload('../properties.json')

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = rmd.get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
        rmd.insert_elem_types(run_specs, structure)

    test_type_list, strain_list, delta_list = rmd_e.get_test_type_strain_delta_list(cryst_sys)
    fitting_results_summary = rmd.fileload('fitting_results.json')
    # fitting_results_summary['c11+2c12'] = {}
    # fitting_results_summary['c11+2c12']['params'] = [properties['B0'] * structure.volume / 160.2 * 9/2.]

    combined_econst_array = [fitting_results_summary[test_type]['params'][0] for test_type in test_type_list]
    combined_econst_array = np.array(combined_econst_array) * 160.2 / structure.volume
    solved = rmd_e.solve(cryst_sys, combined_econst_array)
    rmd.filedump(solved, 'elastic.json')

    if is_properties:
        properties['elastic'] = solved
        rmd.filedump(properties, '../properties.json')
