import run_module as rmd
import os
import numpy as np
import pymatgen as mg
import matplotlib.pyplot as plt

if __name__ == '__main__':
    """

    Obtain the frequency-dependent dielectric functions.

    Set a tag 'optics':

        optics:
          incar:
            CSHIFT: 0.1
            NEDOS: 2000

    Per VASP docs
    (http://cms.mpi.univie.ac.at/wiki/index.php/Dielectric_properties_of_SiC),
    two runs will be perforemd. The 'vasprun.xml' of the first static run is
    renamed as 'vasprun_static.xml', and that of the second optics run as
    'vasprun_loptics.xml'.

    If under 'optics', tag 'local_fields' is defined and set to True, a third
    calculation is performed to get the local fields.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()

    rmd.infer_from_json(run_specs)
    structure = rmd.get_structure(run_specs)
    incar = rmd.read_incar(run_specs)
    kpoints = rmd.read_kpoints(run_specs, structure)

    # static run
    structure.to(filename='POSCAR')
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    rmd.write_potcar(run_specs)
    rmd.run_vasp()
    os.rename('vasprun.xml', 'vasprun_static.xml')

    # independet particle dielectric functions
    incar['ALGO'] = 'Exact'
    incar['LOPTICS'] = True
    incar.update(run_specs['optics']['incar'])
    incar.write_file('INCAR')
    rmd.run_vasp()
    os.rename('vasprun.xml', 'vasprun_loptics.xml')

    # optional third run for local fields
    if 'local_fields' in run_specs['optics'] and run_specs['optics']['local_fields']:
        incar['ALGO'] = 'CHI'
        incar['LRPA'] = False
        incar.write_file('INCAR')
        rmd.run_vasp()

    vasprun = mg.io.vasp.Vasprun('vasprun_loptics.xml')
    E = np.array(vasprun.dielectric[0])
    mask = (E > 0.4) & (E < 6)
    plt.plot(E[mask], np.array(vasprun.dielectric[1])[mask, 0])
    plt.plot(E[mask], np.array(vasprun.dielectric[2])[mask, 0])
    plt.axhline(0, 0, 1, color='k', dashes=[4, 2], alpha=0.7)
    plt.title('Complex Dielectric Function')
    plt.xlabel('Energy (eV)')
    plt.ylabel('Complex Permittivity')
    plt.legend([r'$\varepsilon_1$', r'$\varepsilon_2$'], loc=0)
    plt.tight_layout()
    plt.savefig('dielectric.pdf')
    plt.close()
