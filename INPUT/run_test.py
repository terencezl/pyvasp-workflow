from run_module import *


if __name__ == '__main__':
    """

    The simplest case of a VASP run.

    Load the yaml file and copy it to the directory where the run is about to
    take place. Create a new file 'stdout' to capture the screen output. Read
    some VASP file objects from the yaml file and write them to disk, and
    finally run VASP.

    """

    # pre-config
    run_specs, filename = get_run_specs_and_filename()
    chdir(get_run_dir(run_specs))
    filedump(run_specs, filename)
    init_stdout()

    # read settings
    incar = read_incar(run_specs)
    structure = generate_structure(run_specs)
    kpoints = read_kpoints(run_specs, structure)

    # write input files and run vasp
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_specs)
    run_vasp()
