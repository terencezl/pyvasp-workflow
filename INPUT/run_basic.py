import run_module as rmd


if __name__ == '__main__':
    """

    The simplest case of a VASP run.

    Load the specs file and copy it to the directory where the run is about to
    take place. Create a new file 'stdout' to capture the screen output. Read
    some VASP file objects from the specs file and write them to disk, and
    finally run VASP.

    """

    # pre-config
    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()

    # read settings
    rmd.infer_from_json(run_specs)
    structure = rmd.get_structure(run_specs)
    incar = rmd.read_incar(run_specs)
    kpoints = rmd.read_kpoints(run_specs, structure)

    # write input files and run vasp
    structure.to(filename='POSCAR')
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    rmd.write_potcar(run_specs)
    rmd.run_vasp()
