import pandas as pd
import run_module as rmd
import pymatgen as mg
from pymatgen.analysis import elasticity
import pymatgen.analysis.elasticity.elastic
import pymatgen.analysis.elasticity.stress
import pymatgen.analysis.elasticity.strain

if __name__ == '__main__':
    """

    After the set of VASP runs, use this process script
    process_elastic_stress_strain.py to solve for the elastic constants using
    pseudo-inverse.

    Not a VASP run script that requires a job submission. You can directly use
    it as

        python INPUT/process_elastic_stress_strain.py INPUT/run_elastic_stress_strain.yaml

    to read a specs file at INPUT/run_elastic_stress_strain.yaml, which is the
    file you used to actually run the routine script
    run_elastic_stress_strain.py before this.

    """

    # pre-config
    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))
    rmd.filedump(run_specs, filename)
    rmd.init_stdout()

    # read settings
    structure = rmd.get_structure(run_specs)

    # elastic
    strain_list = [i for i in rmd.fileload('strain_list.json')]
    stress_list = []
    for idx, strain in enumerate(strain_list):
        vasprun = mg.io.vasp.Vasprun(str(idx) + '/vasprun.xml')
        stress_list.append(elasticity.stress.Stress(vasprun.ionic_steps[-1]['stress'])/-10)

    rmd.filedump([i.tolist() for i in stress_list], 'stress_list.json')
    elastic_tensor = elasticity.elastic.ElasticTensor.from_strain_stress_list(strain_list, stress_list)
    elastic_tensor_df = pd.DataFrame(elastic_tensor, index=range(1, 7), columns=range(1, 7))
    elastic_tensor_df.to_csv('elastic_tensor.csv')
    pd.set_option('display.float_format', lambda x: '%.6f' % x)
    print(elastic_tensor_df)
