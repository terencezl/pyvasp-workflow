import os
import sys
import shutil
import numpy as np
from run_modules import *
import pymatgen as mg
import pydass_vasp


def central_poly(X, a, b, c):
    return b * X**3 + a * X**2 + c

if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    cryst_sys = run_spec['elastic']['cryst_sys']
    test_type_input = run_spec['elastic']['test_type']

    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    properties = fileload('../properties.json')
    V0 = properties['V0']
    incar = read_incar(run_spec)
    kpoints = read_kpoints(run_spec)
    is_mag = detect_is_mag(properties['mag'])
    if is_mag:
        incar.update({'ISPIN': 2})
    else:
        incar.update({'ISPIN': 1})

    if not incar['LWAVE']:
        LWAVE = False
        incar['LWAVE'] = True
    else:
        LWAVE = True

    if os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
    elif os.path.isfile('nostrain/CONTCAR'):
        structure = mg.Structure.from_file('nostrain/CONTCAR')
    else:
        structure = generate_structure(run_spec)
        structure.scale_lattice(V0)

    test_type_list, strain_list, delta_list = get_test_type_strain_delta_list(cryst_sys)
    for test_type, strain, delta in zip(test_type_list, strain_list, delta_list):
        if test_type == test_type_input:
            chdir(test_type)
            rm_stdout()
            energy = np.zeros(len(delta))
            mag = np.zeros(len(delta))
            for ind, value in enumerate(delta):
                incar.write_file('INCAR')
                kpoints.write_file('KPOINTS')
                lattice_modified = mg.Lattice(
                    np.dot(structure.lattice_vectors(), strain(value)))
                structure_copy = structure.copy()
                structure_copy.modify_lattice(lattice_modified)
                structure_copy.to(filename='POSCAR')
                write_potcar(run_spec)
                run_vasp()
                oszicar = mg.io.vaspio.Oszicar('OSZICAR')
                energy[ind] = oszicar.final_energy
                if is_mag:
                    mag[ind] = oszicar.ionic_steps[-1]['mag']

            if not LWAVE:
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
