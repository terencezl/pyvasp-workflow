import os
import run_module as rmd
import pymatgen as mg
from subprocess import call
import shutil


def get_NBANDS_and_basisfunctions_str(potcars, structure):
    # count the needed NBANDS for LOBSTER
    # 'f' actually means semi-core p or s+p for 5d _pv and _sv. Why???
    num_orbitals_dict = {'s': 1, 'p': 3, 'd': 5}
    electron_configuration_change_dict = {
        'Pd': {'+': [(5, 's', 0)]},
    }

    for pot in ['Hf_pv', 'Ta_pv', 'W_pv']:
        electron_configuration_change_dict[pot] = {
            '+': [(5, 'p', 6)],
            '-': [(4, 'f', 14)]
        }

    NBANDS = 0
    basisfunctions_str = ''
    for potcar in potcars:
        n_sites = structure.composition[potcar.element]
        electron_configuration = potcar.electron_configuration

        if potcar.symbol in electron_configuration_change_dict:
            change_at_sym = electron_configuration_change_dict[potcar.symbol]
            if '+' in change_at_sym:
                for i in change_at_sym['+']:
                    electron_configuration.append(i)
            if '-' in change_at_sym:
                for i in change_at_sym['-']:
                    electron_configuration.remove(i)

        for conf in electron_configuration:
            NBANDS += num_orbitals_dict[conf[1]] * n_sites
        basisfunctions_str += ' '.join(['basisfunctions', potcar.element] +
            [str(i[0]) + i[1] for i in electron_configuration]) + '\n'

    return int(NBANDS), basisfunctions_str


if __name__ == '__main__':
    """

    Do a static run with the tags set for a LOBSTER COHP analysis with
    automatically calculated NBANDS inferred from the POTCAR. Append to
    lobsterin the corrsponding basisfunctions and run LOBSTER.

    A reminder of the settings in the 'incar' tag.

      incar:
        NSW: 0
        ISMEAR: -5
        LORBIT: 10
        NEDOS: 4000
        ISYM: -1
        LWAVE: True
        ISTART: 0

    It will cause the INCAR and/or KPOINTS to change before starting the static
    run.

    """

    # pre-config
    run_specs, filename = rmd.get_run_specs_and_filename()
    start_dir = os.getcwd()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()

    # read settings
    rmd.infer_from_json(run_specs)
    structure = rmd.get_structure(run_specs)
    incar = rmd.read_incar(run_specs)
    kpoints = rmd.read_kpoints(run_specs, structure)

    # POTCAR dump
    rmd.write_potcar(run_specs)
    potcars = mg.io.vasp.Potcar.from_file('POTCAR')
    incar['ENCUT'] = rmd.get_max_ENMAX(potcars)
    NBANDS, basisfunctions_str = get_NBANDS_and_basisfunctions_str(potcars, structure)
    incar['NBANDS'] = NBANDS

    # write input files and run vasp
    structure.to(filename='POSCAR')
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    rmd.run_vasp()

    # LOBSTER
    shutil.copy(os.path.join(start_dir, 'INPUT/lobsterin'), 'lobsterin')
    with open('lobsterin', 'a') as f:
        f.write(basisfunctions_str)
    call('lobster-2.0.0 | tee -a stdout', shell=True)
