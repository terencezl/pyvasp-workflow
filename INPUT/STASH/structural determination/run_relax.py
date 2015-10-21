import os
import run_module as rmd
import pymatgen as mg
from glob import glob
import shutil


def stack_oszicar():
    if os.path.isfile('OSZICAR'):
        stack = glob('OSZICAR-*')
        if stack:
            stack_max_num = max([int(i.replace('OSZICAR-', '')) for i in stack])
            os.rename('OSZICAR', 'OSZICAR-' + str(stack_max_num + 1))
        else:
            os.rename('OSZICAR', 'OSZICAR-1')


if __name__ == '__main__':
    """

    Relax the structure. If convergence is not reached (maximum iteration count
    reached), rerun till converged.

    Optionally, you can set the rerun (after the first relaxation) parameters in
    the specs file like

        rerun:
          incar:
            ENCUT: 520
            PREC: A
            IBRION: 1
            EDIFFG: -0.005
          kpoints:
            density: 6000

    It will cause the INCAR and/or KPOINTS to change before starting the second
    and after reruns. This allows for the initial run with a large NSW and low
    relaxation parameters, and the second and after runs with high relaxation
    parameters.

    """

    # pre-config
    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()

    # read settings
    incar = rmd.read_incar(run_specs)

    if 'poscar' in run_specs:
        structure = rmd.get_structure(run_specs)
    elif os.path.isfile('CONTCAR'):
        stack_oszicar()
        structure = mg.Structure.from_file('CONTCAR')

    kpoints = rmd.read_kpoints(run_specs, structure)

    # write input files and run vasp
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    rmd.write_potcar(run_specs)
    rmd.run_vasp()

    # rerun once according to the specs
    if 'rerun' in run_specs:
        stack_oszicar()
        structure = mg.Structure.from_file('CONTCAR')
        structure.to(filename='POSCAR')
        if 'incar' in run_specs['rerun']:
            incar.update(run_specs['rerun']['incar'])
            incar.write_file('INCAR')
        if 'kpoints' in run_specs['rerun']:
            kpoints = rmd.read_kpoints(run_specs['rerun'], structure)
            kpoints.write_file('KPOINTS')
        rmd.run_vasp()

    # if not converged ionically, rerun
    while not mg.io.vasp.Vasprun('vasprun.xml').converged_ionic:
        stack_oszicar()
        structure = mg.Structure.from_file('CONTCAR')
        structure.to(filename='POSCAR')
        rmd.run_vasp()

    shutil.copy('CONTCAR', '../POSCAR')
