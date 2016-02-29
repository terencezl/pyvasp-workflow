import os
import run_module as rmd
import pymatgen as mg
import pymatgen.electronic_structure.plotter


if __name__ == '__main__':
    """

    Obtain the density of states by the non-self-consistent method.

    You should set a 'dos' tag in the specs file, like

        dos:
          incar:
            ISMEAR: -5
            ICHARG: 11
            NEDOS: 3001
            LORBIT: 10
          kpoints:
            mode: M
            divisions: [10, 10, 10]

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()
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

    # first SC run
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    rmd.write_potcar(run_specs)
    rmd.run_vasp()

    # second non-SC run
    incar.update(run_specs['dos']['incar'])
    kpoints = rmd.read_kpoints(run_specs['dos'], structure)
    structure = mg.Structure.from_file('CONTCAR')

    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    rmd.run_vasp()

    vasprun = mg.io.vasp.Vasprun('vasprun.xml')
    dos = vasprun.tdos
    dosp = mg.electronic_structure.plotter.DosPlotter()
    dosp.add_dos('total', dos)
    dosp.save_plot('TDOS.pdf', 'pdf')
