import os
import sys
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import pymatgen as mg
import pydass_vasp
from run_module import rm_stdout, detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure, get_test_type_strain_delta_list, solve


def central_poly(X, a, b, c):
    return b * X**3 + a * X**2 + c

if __name__ == '__main__':
    filename = sys.argv[1]
    test_type_input = sys.argv[2]
    run_spec = fileload(filename)
    os.remove(filename)
    cryst_sys = run_spec['poscar']['cryst_sys']

    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    properties = fileload('../properties.json')

    V0 = properties['V0']
    is_mag = detect_is_mag(properties['mag'])
    (incar, kpoints) = read_incar_kpoints(run_spec)
    if not is_mag:
        incar.update({'ISPIN': 1})

    if os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')
    elif os.path.isfile('nostrain/CONTCAR'):
        structure = mg.Structure.from_file('nonstrain/CONTCAR')
    else:
        structure = generate_structure(run_spec)
        structure.scale_lattice(V0)

    fitting_result_to_json = fileload('fitting_result.json')

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

          fitting_result = pydass_vasp.fitting.curve_fit(central_poly, delta, energy, save_figs=True,
                    output_prefix=test_type)
          fitting_result['params'] = fitting_result['params'].tolist()
          fitting_result.pop('fitted_data')
          fitting_result['mag'] = mag.tolist()
          fitting_result_to_json[test_type] = fitting_result
          shutil.copy(test_type + '.pdf', '..')
          os.chdir('..')

    combined_econst_array = [fitting_result_to_json[test_type]['params'][0] for test_type in test_type_list]
    combined_econst_array = np.array(combined_econst_array) * 160.2 / V0
    solved = solve(cryst_sys, combined_econst_array)
    filedump(solved, 'elastic.json')
    filedump(fitting_result_to_json, 'fitting_result.json')

    properties['elastic'] = solved
    filedump(properties, '../properties.json')
