import run_module as rmd
import pymatgen as mg
import pymatgen.electronic_structure.plotter

if __name__ == '__main__':
    """

    Obtain the band structure.

    NOTE: set below to make sure the calculated structure is consistent with
    the automatically generated high symmetry line kpoints.

        poscar:
          get_structure: primitive_standard

    If tag 'bs' tag is set in the specs file, the non-self-consistent method
    with automatically generated high symmetry line kpoints is used. Set the
    following in addition to what you typically have:

        incar:
          LCHARG: True
        bs:
          incar:
            ICHARG: 11
            NEDOS: 3001
            LORBIT: 10
            ISMEAR: 0
          kpoints_division: 10

    If tag 'bs_hybrid' is set instead, the self-consistent method with
    automatically generated empty weighted high symmetry line kpoints is used.
    Set the following in addition to what you typically have:

        incar:
          LWAVE: True
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

    rmd.infer_from_json(run_specs)
    structure = rmd.get_structure(run_specs)
    incar = rmd.read_incar(run_specs)
    kpoints = rmd.read_kpoints(run_specs, structure)

    # first SC run
    structure.to(filename='POSCAR')
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    rmd.write_potcar(run_specs)
    rmd.run_vasp()

    # structure = mg.Structure.from_file('CONTCAR')

    hskp = mg.symmetry.bandstructure.HighSymmKpath(structure)
    if 'bs' in run_specs:
        # second non-SC run
        line_mode = False
        incar.update(run_specs['bs']['incar'])
        kpoints = mg.io.vasp.Kpoints.automatic_linemode(run_specs['bs']['kpoints_division'], hskp)
        kpoints.comment = ','.join(['-'.join(i) for i in hskp.kpath['path']])
    elif 'bs_hybrid' in run_specs:
        # second hybrid run
        line_mode = True
        incar.update(run_specs['bs_hybrid']['incar'])
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
    bs = vasprun.get_band_structure(line_mode=line_mode)
    bsp = mg.electronic_structure.plotter.BSPlotter(bs)
    bsp.save_plot('BS.pdf', 'pdf')
