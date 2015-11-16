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

    Run the full independent strain sets with changing delta values, fit the
    energy values from each strain set to a polynomial, extract the parameters
    and plot figures, and then linearly solve for the elastic constants.

    The strain sets used to solve the elastic constants are detailed in
    run_module_elastic.py.

    You should set a 'elastic' tag in the specs file, like

        elastic:
          cryst_sys: cubic

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)

    cryst_sys = run_specs['elastic']['cryst_sys']
    incar = rmd.read_incar(run_specs)
    is_properties = None
    if os.path.isfile(('../properties.json')):
        is_properties = True
        properties = rmd.fileload('../properties.json')

    if 'ISPIN' in incar:
        is_mag = incar['ISPIN'] == 2
    elif is_properties:
        is_mag = rmd.detect_is_mag(properties['mag'])
        if is_mag:
            incar.update({'ISPIN': 2})
        else:
            incar.update({'ISPIN': 1})
    else:
        is_mag = False

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = rmd.get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = rmd.read_kpoints(run_specs, structure)

    fitting_results_summary = {}

    rmd.chdir('nostrain')
    rmd.init_stdout()
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    rmd.write_potcar(run_specs)
    rmd.run_vasp()
    oszicar = mg.io.vasp.Oszicar('OSZICAR')
    energy_nostrain = oszicar.final_energy
    structure = mg.Structure.from_file('CONTCAR')
    if is_mag:
        mag_nostrain = oszicar.ionic_steps[-1]['mag']
    os.chdir('..')

    test_type_list, strain_list, delta_list = rmd_e.get_test_type_strain_delta_list(cryst_sys)
    for test_type, strain, delta in \
                zip(test_type_list, strain_list, delta_list):

        # skip the strain correspoinding to bulk modulus and use the value from properties.json
        # if test_type == 'c11+2c12':
            # continue

        rmd.chdir(test_type)
        energy = np.zeros(len(delta))
        energy[0] = energy_nostrain
        mag = np.zeros(len(delta))
        if is_mag:
            mag[0] = mag_nostrain

        for ind, value in enumerate(delta[1:]):
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
            rmd.run_vasp()
            oszicar = mg.io.vasp.Oszicar('OSZICAR')
            energy[ind+1] = oszicar.final_energy
            if is_mag:
                mag[ind+1] = oszicar.ionic_steps[-1]['mag']
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
        fitting_results_summary[test_type] = fitting_results
        rmd.filedump(fitting_results_summary, '../fitting_results.json')
        shutil.copy(test_type + '.pdf', '..')
        os.chdir('..')

    # fitting_results_summary['c11+2c12'] = {}
    # fitting_results_summary['c11+2c12']['params'] = [properties['B0'] * structure.volume / 160.2 * 9/2.]
    combined_econst_array = [fitting_results_summary[test_type]['params'][0] for test_type in test_type_list]
    combined_econst_array = np.array(combined_econst_array) * 160.2 / structure.volume
    solved = rmd_e.solve(cryst_sys, combined_econst_array)
    rmd.filedump(solved, 'elastic.json')

    if is_properties:
        # load again immediately before save
        properties = rmd.fileload('../properties.json')
        properties['elastic'] = solved
        rmd.filedump(properties, '../properties.json')
