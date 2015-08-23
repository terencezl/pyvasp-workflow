import os
import sys
import shutil
import numpy as np
from run_module import *
from run_module_elastic import *
import pymatgen as mg
import pydass_vasp

if __name__ == '__main__':
    run_specs, filename = get_run_specs_and_filename()
    chdir(get_run_dir(run_specs))

    cryst_sys = run_specs['poscar']['cryst_sys']
    is_properties = None
    if os.path.isfile(('../properties.json')):
        is_properties = True
        properties = fileload('../properties.json')

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = generate_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    test_type_list, strain_list, delta_list = get_test_type_strain_delta_list(cryst_sys)
    fitting_results_summary = fileload('fitting_results.json')
    # fitting_results_summary['c11+2c12'] = {}
    # fitting_results_summary['c11+2c12']['params'] = [properties['B0'] * structure.volume / 160.2 * 9/2.]

    combined_econst_array = [fitting_results_summary[test_type]['params'][0] for test_type in test_type_list]
    combined_econst_array = np.array(combined_econst_array) * 160.2 / structure.volume
    solved = solve(cryst_sys, combined_econst_array)
    filedump(solved, 'elastic.json')

    if is_properties:
        properties['elastic'] = solved
        filedump(properties, '../properties.json')
