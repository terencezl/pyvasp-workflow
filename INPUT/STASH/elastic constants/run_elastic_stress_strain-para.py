import os
import shutil
from subprocess import call
import numpy as np
import run_module as rmd
import pymatgen as mg
from pymatgen.analysis import elasticity
import pymatgen.analysis.elasticity.elastic
import pymatgen.analysis.elasticity.stress
import pymatgen.analysis.elasticity.strain

if __name__ == '__main__':
    """

    Run 6 sets of strains, normal or shear, with each set containing a number of
    runs of differnet extent in python level parallel submission mode.

    The strain sets used to solve the elastic constants are detailed in
    pymatgen.analysis.elasticity.strain.DeformedStructureSet(). See their docs.

    Optionally, you can set a 'elastic' tag in the specs file to pass the
    arguments of pymatgen.analysis.elasticity.strain.DeformedStructureSet(),
    like

        elastic:
          num_norm: 2
          num_shear: 2

    After the set of VASP runs, you need to use the process script
    process_elastic_stress_strain to solve for the elastic constants.

    """

    # pre-config
    run_specs, filename = rmd.get_run_specs_and_filename()
    cwd = os.getcwd()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)

    # read settings
    rmd.infer_from_json(run_specs)
    structure = rmd.get_structure(run_specs)
    incar = rmd.read_incar(run_specs)
    kpoints = rmd.read_kpoints(run_specs, structure)

    # elastic
    if 'elastic' in run_specs and ('num_norm' in run_specs['elastic'] or 'num_shear' in run_specs['elastic']):
        dss = elasticity.strain.DeformedStructureSet(structure, num_norm=run_specs['elastic']['num_norm'], num_shear=run_specs['elastic']['num_shear'])
    else:
        dss = elasticity.strain.DeformedStructureSet(structure)
    strain_list = [i.green_lagrange_strain for i in dss.deformations]
    rmd.filedump([i.tolist() for i in strain_list], 'strain_list.json')
    for idx, defo in enumerate(dss.deformations):
        rmd.chdir(str(idx))
        rmd.init_stdout()
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        rmd.write_potcar(run_specs)
        st_copy = structure.copy()
        st_copy.modify_lattice(mg.Lattice(np.dot(st_copy.lattice.matrix, defo.green_lagrange_strain + np.eye(3))))
        st_copy.to(filename='POSCAR')
        job = 'elastic-' + str(idx)
        shutil.copy(cwd + '/INPUT/deploy.job', job)
        call('sed -i "/python/c time ' + rmd.VASP_EXEC + ' 2>&1 | tee -a stdout" ' + job, shell=True)
        call('M ' + job, shell=True)
        os.remove(job)
        os.chdir('..')
