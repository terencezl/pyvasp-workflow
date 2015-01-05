import os
import sys
import shutil
import json
import yaml
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import pymatgen as mg
import pydass_vasp
from run_module import chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure


if __name__ == '__main__':
    filename = sys.argv[1]
    subdirname = sys.argv[2]
    with open(filename) as f:
        run_spec = yaml.load(f)
    enter_main_dir(run_spec)
    with open('properties.json', 'r') as f:
        properties = json.load(f)

    (incar, kpoints) = read_incar_kpoints(run_spec)
    if not properties['is_mag']:
        incar.update({'ISPIN': 1})
    structure = generate_structure(run_spec)
    structure.scale_lattice(properties['V0'])

    chdir(subdirname)
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()
    os.chdir('..')
