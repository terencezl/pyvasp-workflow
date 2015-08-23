import os
import sys
import shutil
import numpy as np
from run_module import *
from run_module_elastic import *
import pymatgen as mg
import pydass_vasp

if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    cryst_sys = run_spec['poscar']['cryst_sys']

    enter_main_dir(run_spec)
    is_properties = None
    if os.path.isfile(('../properties.json')):
        is_properties = True
        properties = fileload('../properties.json')

    # higher priority for run_spec
    if 'poscar' in run_spec:
        structure = generate_structure(run_spec)
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
