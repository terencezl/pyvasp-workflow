import pymatgen as mg
st = mg.Structure.from_file('POSCAR-hcp-1')
sym = mg.SymmOp.from_axis_angle_and_translation([0,0,1], 45)
st.modify_lattice(mg.Lattice(sym.operate_multi(st.lattice_vectors())))
st.to('POSCAR', 'POSCAR-hcp-3')