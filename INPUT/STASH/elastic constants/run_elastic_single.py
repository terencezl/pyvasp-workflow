import os
import shutil
import numpy as np
from run_module import *
from run_module_elastic import *
import pymatgen as mg
import pydass_vasp


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

    run_specs, filename = get_run_specs_and_filename()
    chdir(get_run_dir(run_specs))
    filedump(run_specs, filename)

    cryst_sys = run_specs['elastic']['cryst_sys']
    test_type_input = run_specs['elastic']['test_type']
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
        structure = get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = read_kpoints(run_specs, structure)

    test_type_list, strain_list, delta_list = get_test_type_strain_delta_list(cryst_sys)
    for test_type, strain, delta in zip(test_type_list, strain_list, delta_list):
        if test_type == test_type_input:
            chdir(test_type)
            energy = np.zeros(len(delta))
            mag = np.zeros(len(delta))
            for ind, value in enumerate(delta):
                chdir(str(value))
                init_stdout()
                incar.write_file('INCAR')
                kpoints.write_file('KPOINTS')
                lattice_modified = mg.Lattice(
                    np.dot(structure.lattice_vectors(), strain(value)))
                structure_copy = structure.copy()
                structure_copy.modify_lattice(lattice_modified)
                structure_copy.to(filename='POSCAR')
                write_potcar(run_specs)
                run_vasp()
                oszicar = mg.io.vasp.Oszicar('OSZICAR')
                energy[ind] = oszicar.final_energy
                if is_mag:
                    mag[ind] = oszicar.ionic_steps[-1]['mag']
                os.chdir('..')

            if 'LWAVE' not in incar:
                os.remove('WAVECAR')
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
