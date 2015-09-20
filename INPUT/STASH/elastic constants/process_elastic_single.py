import os
import shutil
import numpy as np
import run_module as rmd
import run_module_elastic as rmd_e
import pymatgen as mg
import pydass_vasp


if __name__ == '__main__':
    """

    Fit the energy values from a single strain set to a polynomial, extract the
    parameters and plot figures.

    Not a VASP run script that requires a job submission. You can directly use
    it as

        INPUT/process_elastic_single.py INPUT/run_elastic_single.yaml

    to read a specs file at INPUT/run_elastic_single.yaml, which is the file you
    would use to actually run the routine script run_elastic_single.py before
    this.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))

    test_type_input = run_specs['elastic']['test_type']
    cryst_sys = run_specs['elastic']['cryst_sys']
    if 'ISPIN' in incar:
        is_mag = incar['ISPIN'] == 2
    elif os.path.isfile(('../properties.json')):
        properties = rmd.fileload('../properties.json')
        is_mag = rmd.detect_is_mag(properties['mag'])
    else:
        is_mag = False

    test_type_list, strain_list, delta_list = rmd_e.get_test_type_strain_delta_list(cryst_sys)
    for test_type, strain, delta in zip(test_type_list, strain_list, delta_list):
        if test_type == test_type_input:
            rmd.chdir(test_type)
            energy = np.zeros(len(delta))
            mag = np.zeros(len(delta))
            for ind, value in enumerate(delta):
                rmd.chdir(str(value))
                oszicar = mg.io.vasp.Oszicar('OSZICAR')
                energy[ind] = oszicar.final_energy
                if is_mag:
                    mag[ind] = oszicar.ionic_steps[-1]['mag']
                os.chdir('..')

            fitting_results = pydass_vasp.fitting.curve_fit(rmd_e.central_poly, delta, energy, save_figs=True,
                      output_prefix=test_type)
            fitting_results['params'] = fitting_results['params'].tolist()
            fitting_results.pop('fitted_data')
            fitting_results['delta'] = delta.tolist()
            fitting_results['energy'] = energy.tolist()
            fitting_results['mag'] = mag.tolist()
            rmd.filedump(fitting_results, 'fitting_results.json')
            # higher level fitting_results.json
            if os.path.isfile('../fitting_results.json'):
                fitting_results_summary = rmd.fileload('../fitting_results.json')
            else:
                fitting_results_summary = {}
            fitting_results_summary[test_type] = fitting_results
            rmd.filedump(fitting_results_summary, '../fitting_results.json')
            shutil.copy(test_type + '.pdf', '..')
            os.chdir('..')
