import os
import run_module as rmd
import pymatgen as mg
import pymatgen.electronic_structure.plotter

if __name__ == '__main__':
    """

    Obtain the hybrid functional band structure by the self-consistent method
    with automatically generated empty weighted high symmetry line kpoints.

    You should set a 'bs_hybrid' tag in the specs file, like

        bs_hybrid:
          incar:
            LHFCALC: True
            HFSCREEN: 0.2
            PRECFOCK: Fast
            ALGO: Damped
            NEDOS: 3001
            LORBIT: 10
          kpoints_division: 10

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

    # first DFT run
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    rmd.write_potcar(run_specs)
    rmd.run_vasp()

    # second hybrid run
    structure = mg.Structure.from_file('CONTCAR')
    incar.update(run_specs['bs_hybrid']['incar'])
    # obtain the automatically generated kpoints list
    hskp = mg.symmetry.bandstructure.HighSymmKpath(structure)
    kpts_bs = hskp.get_kpoints(run_specs['bs_hybrid']['kpoints_division'], coords_are_cartesian=False)
    kpoints = mg.io.vasp.Kpoints.from_file('IBZKPT')
    kpoints.kpts.extend([i.tolist() for i in kpts_bs[0]])
    kpoints.kpts_weights.extend([0 for i in kpts_bs[0]])
    kpoints.labels.extend(kpts_bs[1])
    kpoints.num_kpts += len(kpts_bs[0])

    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    rmd.run_vasp()

    vasprun = mg.io.vasp.Vasprun('vasprun.xml')
    bs = vasprun.get_band_structure(line_mode=True)
    bsp = mg.electronic_structure.plotter.BSPlotter(bs)
    bsp.save_plot('BS.pdf', 'pdf')
