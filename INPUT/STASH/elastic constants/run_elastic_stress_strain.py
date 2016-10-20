import numpy as np
import pandas as pd
import run_module as rmd
import pymatgen as mg
from pymatgen.analysis import elasticity
import pymatgen.analysis.elasticity.elastic
import pymatgen.analysis.elasticity.stress
import pymatgen.analysis.elasticity.strain

if __name__ == '__main__':
    """

    Run 6 sets of strains, normal or shear, with each set containing a number of
    runs of differnet extent, collect the stress output, and solve for the
    elastic constants using pseudo-inverse.

    The strain sets used to solve the elastic constants are detailed in
    pymatgen.analysis.elasticity.strain.DeformedStructureSet(). See their docs.

    Optionally, you can set a 'elastic' tag in the specs file to pass the
    arguments of pymatgen.analysis.elasticity.strain.DeformedStructureSet(),
    like

        elastic:
          num_norm: 2
          num_shear: 2

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

    # write input files
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    rmd.write_potcar(run_specs)

    # elastic
    if 'elastic' in run_specs and ('num_norm' in run_specs['elastic'] or 'num_shear' in run_specs['elastic']):
        dss = elasticity.strain.DeformedStructureSet(structure, num_norm=run_specs['elastic']['num_norm'], num_shear=run_specs['elastic']['num_shear'])
    else:
        dss = elasticity.strain.DeformedStructureSet(structure)
    strain_list = [i.green_lagrange_strain for i in dss.deformations]
    rmd.filedump([i.tolist() for i in strain_list], 'strain_list.json')
    stress_list = []
    for defo in dss.deformations:
    # for st_deformed in dss.def_structs:
    #     st_deformed.to(filename='POSCAR')
        st_copy = structure.copy()
        st_copy.modify_lattice(mg.Lattice(np.dot(st_copy.lattice.matrix, defo.green_lagrange_strain + np.eye(3))))
        st_copy.to(filename='POSCAR')
        rmd.run_vasp()
        vasprun = mg.io.vasp.Vasprun('vasprun.xml')
        stress_list.append(elasticity.stress.Stress(vasprun.ionic_steps[-1]['stress'])/-10)
        rmd.filedump([i.tolist() for i in stress_list], 'stress_list.json')

    elastic_tensor = elasticity.elastic.ElasticTensor.from_strain_stress_list(strain_list, stress_list).voigt
    elastic_tensor_df = pd.DataFrame(elastic_tensor, index=range(1, 7), columns=range(1, 7))
    elastic_tensor_df.to_csv('elastic_tensor.csv')
    pd.set_option('display.float_format', lambda x: '%.6f' % x)
    print(elastic_tensor_df)
