import os
from run_module import *
import pymatgen as mg
from glob import glob


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
            PREC: High
            IBRION: 1
            EDIFFG: -0.005
          kpoints:
            density: 6000

    """

    # pre-config
    run_specs, filename = get_run_specs_and_filename()
    chdir(get_run_dir(run_specs))
    filedump(run_specs, filename)
    init_stdout()

    # read settings
    incar = read_incar(run_specs)

    if 'poscar' in run_specs:
        structure = get_structure(run_specs)
    elif os.path.isfile('CONTCAR'):
        structure = mg.Structure.from_file('CONTCAR')
        stack_oszicar()

    kpoints = read_kpoints(run_specs, structure)

    # write input files and run vasp
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_specs)
    run_vasp()

    # if not converged ionically, rerun
    while not mg.io.vasp.Vasprun('vasprun.xml').converged_ionic:
        stack_oszicar()
        structure = mg.Structure.from_file('CONTCAR')
        structure.to(filename='POSCAR')
        if 'rerun' in run_specs:
            incar.update(run_specs['relax']['incar'])
            incar.write_file('INCAR')
            kpoints = read_kpoints(run_specs['rerun'], structure)
            kpoints.write_file('KPOINTS')
        run_vasp()
