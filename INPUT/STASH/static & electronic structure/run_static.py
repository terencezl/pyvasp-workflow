import os
import pymatgen as mg
import run_module as rmd


if __name__ == '__main__':
    """

    Do a static run. Make use of previously calculated POSCAR/CONTCAR and
    properties.json when possible.

    """

    # pre-config
    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()

    # read settings
    incar = rmd.read_incar(run_specs)
    if os.path.isfile('../properties.json'):
        properties = rmd.fileload('../properties.json')
        if 'ISPIN' not in incar:
            if rmd.detect_is_mag(properties['mag']):
                incar.update({'ISPIN': 2})
            else:
                incar.update({'ISPIN': 1})

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = rmd.get_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = rmd.read_kpoints(run_specs, structure)

    # write input files and run vasp
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    rmd.write_potcar(run_specs)
    rmd.run_vasp()
