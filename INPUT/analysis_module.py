import pandas as pd
from monty.serialization import loadfn
from itertools import product

structures = ['rocksalt', 'cc', 'wurtzite']
elements = ['Sc_sv', 'Ti_sv', 'V_sv', 'Cr_pv', 'Mn_pv', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
            'Y_sv', 'Zr_sv', 'Nb_sv', 'Mo_pv', 'Tc_pv', 'Ru_pv', 'Rh_pv', 'Pd', 'Ag', 'Cd',
                    'Hf_pv', 'Ta_pv', 'W_pv', 'Re', 'Os', 'Ir', 'Pt', 'Au']


def getdf(structures, elements, filepath):
    properties_list = [[pd.io.json.json_normalize(loadfn(st + '-' + e + '+' + 'N/' + filepath))
                        for e in elements] for st in structures]

    data = pd.concat([j for i in properties_list for j in i], ignore_index=True)
    ind = pd.MultiIndex.from_tuples(
        [(j[0], j[1][0][0], j[1][0][1], j[1][1]) for j in product(
            structures,
            zip(
                [i for i in product(['3d', '4d', '5d'], range(3,13))
                    if not (i[0] == '5d' and (i[1] == 3 or i[1] == 12))],
                elements
                )
            )
        ],
        names=['structure', 'period', 'group', 'element']
        )

    data.index = ind
    data.sortlevel(inplace=True)
    return data
