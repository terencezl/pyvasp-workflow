import os
import sys
import shutil
import numpy as np
from run_module import *
import pymatgen as mg
import pydass_vasp


def central_poly(X, a, b, c):
    return b * X**3 + a * X**2 + c

if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    test_type_input = run_spec['elastic']['test_type']
    cryst_sys = run_spec['elastic']['cryst_sys']

    enter_main_dir(run_spec)
    if 'ISPIN' in incar:
        is_mag = incar['ISPIN'] == 2
    elif os.path.isfile(('../properties.json')):
        properties = fileload('../properties.json')
        is_mag = detect_is_mag(properties['mag'])
    else:
        is_mag = False

    test_type_list, strain_list, delta_list = get_test_type_strain_delta_list(cryst_sys)
    for test_type, strain, delta in zip(test_type_list, strain_list, delta_list):
        if test_type == test_type_input:
            chdir(test_type)
            energy = np.zeros(len(delta))
            mag = np.zeros(len(delta))
            for ind, value in enumerate(delta):
                chdir(str(value))
                oszicar = mg.io.vasp.Oszicar('OSZICAR')
                energy[ind] = oszicar.final_energy
                if is_mag:
                    mag[ind] = oszicar.ionic_steps[-1]['mag']
                os.chdir('..')

            fitting_results = pydass_vasp.fitting.curve_fit(central_poly, delta, energy, save_figs=True,
                      output_prefix=test_type)
            fitting_results['params'] = fitting_results['params'].tolist()
            fitting_results.pop('fitted_data')
            fitting_results['delta'] = delta.tolist()
            fitting_results['energy'] = energy.tolist()
            fitting_results['mag'] = mag.tolist()
            filedump(fitting_results, 'fitting_results.json')
            # higher level fitting_results.json
            if os.path.isfile('../fitting_results.json'):
                fitting_results_summary = fileload('../fitting_results.json')
            else:
                fitting_results_summary = {}
            fitting_results_summary[test_type] = fitting_results
            filedump(fitting_results_summary, '../fitting_results.json')
            shutil.copy(test_type + '.pdf', '..')
            os.chdir('..')
