import run_module as rmd
import os
import pymatgen as mg
import shutil


if __name__ == '__main__':
    """

    Relax the structure, then do a static run.

    You should set a 'static' tag in the specs file, like

        static:
          incar:
            NSW: 0
            PREC: A
            ISMEAR: -5
          kpoints:
            density: 6000

    It will cause the INCAR and/or KPOINTS to change before starting the static
    run.

    """

    # pre-config
    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()

    # read settings
    incar = rmd.read_incar(run_specs)
    structure = rmd.get_structure(run_specs)
    kpoints = rmd.read_kpoints(run_specs, structure)

    # write input files and run vasp
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    rmd.write_potcar(run_specs)
    rmd.run_vasp()

    # static
    structure = mg.Structure.from_file('CONTCAR')
    structure.to(filename='POSCAR')
    if 'incar' in run_specs['static']:
        incar.update(run_specs['static']['incar'])
        incar.write_file('INCAR')
    if 'kpoints' in run_specs['static']:
        kpoints = rmd.read_kpoints(run_specs['static'], structure)
        kpoints.write_file('KPOINTS')
    rmd.run_vasp()

    shutil.copy('CONTCAR', '../POSCAR')
