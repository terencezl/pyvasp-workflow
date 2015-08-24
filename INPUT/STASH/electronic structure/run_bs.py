import os
from run_module import *
import pymatgen as mg
import pymatgen.electronic_structure.plotter

if __name__ == '__main__':
    """

    Obtain the band structure by the non-self-consistent method with
    automatically generated high symmetry line kpoints.

    You should set a 'bs' tag in the specs file, like

        bs:
          incar:
            ICHARG: 11
            NEDOS: 3001
            LORBIT: 10
            ISMEAR: 0
          kpoints_division: 20

    """

    run_specs, filename = get_run_specs_and_filename()
    chdir(get_run_dir(run_specs))
    filedump(run_specs, filename)
    init_stdout()
    incar = read_incar(run_specs)
    if os.path.isfile('../properties.json'):
        properties = fileload('../properties.json')
        if 'ISPIN' not in incar:
            if detect_is_mag(properties['mag']):
                incar.update({'ISPIN': 2})
            else:
                incar.update({'ISPIN': 1})

    # higher priority for run_specs
    if 'poscar' in run_specs:
        structure = generate_structure(run_specs)
    elif os.path.isfile('../POSCAR'):
        structure = mg.Structure.from_file('../POSCAR')

    kpoints = read_kpoints(run_specs, structure)

    # first SC run
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_specs)
    run_vasp()

    # second non-SC run
    structure = mg.Structure.from_file('CONTCAR')
    incar.update(run_specs['bs']['incar'])
    # obtain the automatically generated kpoints list
    hskp = mg.symmetry.bandstructure.HighSymmKpath(structure)
    kpoints = mg.io.vasp.Kpoints.automatic_linemode(run_specs['bs']['kpoints_division'], hskp)
    kpoints.comment = ','.join(['-'.join(i) for i in hskp.kpath['path']])

    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    run_vasp()

    vasprun = mg.io.vasp.Vasprun('vasprun.xml')
    bs = vasprun.get_band_structure()
    bsp = mg.electronic_structure.plotter.BSPlotter(bs)
    bsp.save_plot('BS.pdf', 'pdf')
