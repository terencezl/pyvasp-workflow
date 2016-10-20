import os
import shutil
import numpy as np
import run_module as rmd
import run_module_elastic as rmd_e
import pymatgen as mg
import pydass_vasp
import matplotlib.pyplot as plt


if __name__ == '__main__':
    """

    Run a single strain set with changing delta values, fit the energy values to a
    polynomial, extract the parameters and plot figures.

    You should set a 'elastic' tag in the specs file, like

        elastic:
          cryst_sys: cubic
          test_type: c11-c12

    The 'test_type' tag defines the name of the strain set, whose mathematical
    form is detailed in run_module_elastic.py.

    After this kind of VASP run for for all the independent strain sets, you
    need to use the process script process_elastic_solve.py to obtain the
    elastic constants.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)

    cryst_sys = run_specs['elastic']['cryst_sys']
    test_type_input = run_specs['elastic']['test_type']

    rmd.infer_from_json(run_specs)
    structure = rmd.get_structure(run_specs)
    incar = rmd.read_incar(run_specs)
    kpoints = rmd.read_kpoints(run_specs, structure)

    is_mag = incar['ISPIN'] == 2 if 'ISPIN' in incar else False

    test_type_list, strain_list, delta_list = rmd_e.get_test_type_strain_delta_list(cryst_sys)
    for test_type, strain, delta in zip(test_type_list, strain_list, delta_list):
        if test_type == test_type_input:
            rmd.chdir(test_type)
            energy = np.zeros(len(delta))
            mag = np.zeros(len(delta))
            for ind, value in enumerate(delta):
                rmd.chdir(str(value))
                rmd.init_stdout()
                incar.write_file('INCAR')
                kpoints.write_file('KPOINTS')
                lattice_modified = mg.Lattice(
                    np.dot(structure.lattice.matrix, strain(value)))
                structure_copy = structure.copy()
                structure_copy.modify_lattice(lattice_modified)
                structure_copy.to(filename='POSCAR')
                rmd.write_potcar(run_specs)
                rmd.run_vasp()
                oszicar = mg.io.vasp.Oszicar('OSZICAR')
                energy[ind] = oszicar.final_energy
                if is_mag:
                    mag[ind] = oszicar.ionic_steps[-1]['mag']
                os.chdir('..')

            fitting_results = pydass_vasp.fitting.curve_fit(rmd_e.central_poly, delta, energy, plot=True)
            plt.savefig(test_type + '.pdf')
            plt.close()
            fitting_results['params'] = fitting_results['params'].tolist()
            fitting_results.pop('fitted_data')
            fitting_results.pop('ax')
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
