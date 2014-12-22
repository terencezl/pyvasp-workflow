import os
import sys
import shutil
from subprocess import call
import re
import json
import yaml
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import pymatgen as mg
import pydass_vasp

POTENTIAL_DATABASE = 'PATH-TO-YOUR-POTENTIAL-DATABASE'
VASP = 'PATH-TO-YOUR-EXECUTABLE'

template_dir = os.path.join(os.getcwd(), 'INPUT/')

def enter_main_dir(run_spec):
    """
    enter the main run directory
    """
    dirname = run_spec['structure'] + '-' + ','.join(run_spec['elem_types'])
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    os.chdir(dirname)


def run_vasp():
    """
    run mpi version of vasp
    """
    run = call('time mpiexec ' + VASP + ' | tee -a stdout', shell=True)
    if run != 0:
        raise RuntimeError("VASP run error!")


def generate_incar_kpoints_potcar(run_spec):
    """
    generate INCAR, KPOINTS and POTCAR
    """
    # INCAR
    incar = mg.io.vaspio.Incar()
    if run_spec.has_key('incar') and run_spec['incar']:
        incar.update(run_spec['incar'])
    incar.write_file('INCAR')

    # KPOINTS
    kpoints = mg.io.vaspio.Kpoints.monkhorst_automatic([11, 11, 11])
    if run_spec.has_key('kpoints') and run_spec['kpoints']:
        kpoints_spec = run_spec['kpoints']
        if kpoints_spec['mode'] == 'M':
            kpoints = mg.io.vaspio.Kpoints.monkhorst_automatic(kpoints_spec['divisions'])
        elif kpoints_spec['mode'] == 'G':
            kpoints = mg.io.vaspio.Kpoints.gamma_automatic(kpoints_spec['divisions'])
    kpoints.write_file('KPOINTS')

    # POTCAR
    POTENTIAL_BASE = os.path.join(POTENTIAL_DATABASE, run_spec['pot_type'], 'POTCAR_')
    with open('POTCAR', 'wb') as outfile:
        for filename in [POTENTIAL_BASE + e for e in run_spec['elem_types']]:
            with open(filename, 'rb') as infile:
                shutil.copyfileobj(infile, outfile)

def generate_structure(run_spec):
    """
    generate pymatgen.Structure
    """
    poscar_dict = run_spec['poscar']
    elem_types_struct = [re.sub(r'_.*', '', i) for i in run_spec['elem_types']]
    if poscar_dict.has_key('template') and poscar_dict['template']:
        poscar = mg.io.vaspio.Poscar.from_file(template_dir, poscar_dict['template'])
        structure = poscar.structure
        for i, item in enumerate(structure.symbol_set):
            structure.replace_species({item: elem_types_struct[i]})
        return structure

    cryst_sys = poscar_dict['cryst_sys']
    lattice_params = poscar_dict['lattice_params']
    if cryst_sys == 'cubic':
        lattice = mg.Lattice.cubic(lattice_params['a'])
    elif cryst_sys == 'hexagonal':
        lattice = mg.Lattice.hexagonal(lattice_params['a'], lattice_params['alpha'])
    elif cryst_sys == 'tetragonal':
        lattice = mg.Lattice.tetragonal(lattice_params['a'], lattice_params['c'])
    elif cryst_sys == 'orthorhombic':
        lattice = mg.Lattice.orthorhombic(lattice_params['a'], lattice_params['b'], lattice_params['c'])
    elif cryst_sys == 'rhombohedral':
        lattice = mg.Lattice.rhombohedral(lattice_params['a'], lattice_params['alpha'])
    elif cryst_sys == 'monoclinic':
        lattice = mg.Lattice.orthorhombic(lattice_params['a'], lattice_params['b'], lattice_params['c'],
            lattice_params['beta'])
    else:
        lattice = mg.Lattice.orthorhombic(lattice_params['a'], lattice_params['b'], lattice_params['c'],
            lattice_params['alpha'], lattice_params['beta'], lattice_params['gamma'])
    structure = mg.Structure.from_spacegroup(poscar_dict['spacegroup'], lattice,
            elem_types_struct, poscar_dict['atom_locs_direct']).get_primitive_structure()
    return structure