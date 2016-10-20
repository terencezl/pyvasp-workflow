import numpy as np


def central_poly(X, a, b, c):
    return b * X**3 + a * X**2 + c


def get_test_type_strain_delta_list(cryst_sys):
    """

    Generates elastic strains.

    Argument cryst_sys is one of ['cubic', 'hexagonal', 'tetragonal',
    'orthorhombic'] for now.

    Returns:

    test_type_list, different independent test_type strings
    strain_list, the strain tensor function corresponding to each test_type
    delta_list, a 2-dimensional array, with each row corresponding to each
    test_type, and each column the small displacement value.

    """
    strain_list = []

    if cryst_sys == 'cubic':
        test_type_list = ["c11+2c12", "c11-c12", "c44"]
        delta_list = np.ones(((3, 5))) * [0, -0.02, 0.02, -0.03, 0.03]
        delta_list[0] = delta_list[0]/np.sqrt(3)

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1 + delta, 0],
                                                   [0, 0, 1 + delta]]))

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1 - delta, 0],
                                                   [0, 0, 1 + delta ** 2 / (1 - delta ** 2)]]))

        strain_list.append(lambda delta: np.array([[1, delta/2, 0],
                                                   [delta/2, 1, 0],
                                                   [0, 0, 1 + delta ** 2 / (4 - delta ** 2)]]))

    elif cryst_sys == 'hexagonal':
        test_type_list = ["2c11+2c12+4c13+c33", "c11-c12", "c11+c12", "c44", "c33"]
        delta_list = np.ones(((5, 5))) * [0, -0.02, 0.02, -0.03, 0.03]

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1 + delta, 0],
                                                   [0, 0, 1 + delta]]))

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1 - delta, 0],
                                                   [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1 + delta, 0],
                                                   [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                                   [0, 1, delta],
                                                   [0, delta, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                                   [0, 1, 0],
                                                   [0, 0, 1 + delta]]))

    elif cryst_sys == 'tetragonal':
        test_type_list = ["c11", "c33", "c44",
                "5c11-4c12-2c13+c33", "c11+c12-4c13+2c33", "c11+c12-4c13+2c33+2c66"]
        delta_list = np.ones(((6, 5))) * [0, -0.02, 0.02, -0.03, 0.03]
        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1, 0],
                                                   [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                                   [0, 1, 0],
                                                   [0, 0, 1 + delta]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                                   [0, 1, delta],
                                                   [0, delta, 1]]))

        strain_list.append(lambda delta: np.array([[1 + 2 * delta, 0, 0],
                                                   [0, 1 - delta, 0],
                                                   [0, 0, 1 - delta]]))

        strain_list.append(lambda delta: np.array([[1 - delta, 0, 0],
                                                   [0, 1 - delta, 0],
                                                   [0, 0, 1 + 2 * delta]]))

        strain_list.append(lambda delta: np.array([[1 + delta, delta, 0],
                                                   [delta, 1 + delta, 0],
                                                   [0, 0, 1 - 2 * delta]]))

    elif cryst_sys == 'orthorhombic':
        test_type_list = ["c11", "c22", "c33", "c44", "c55", "c66",
            "4c11-4c12-4c13+c22+2c23+c33", "c11-4c12+2c13+4c22-4c23+c33", "c11+2c12-4c13+c22-4c23+4c33"]
        delta_list = np.ones(((9, 5))) * [0, -0.02, 0.02, -0.03, 0.03]

        strain_list.append(lambda delta: np.array([[1 + delta, 0, 0],
                                                   [0, 1, 0],
                                                   [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                                   [0, 1 + delta, 0],
                                                   [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                                   [0, 1, 0],
                                                   [0, 0, 1 + delta]]))

        strain_list.append(lambda delta: np.array([[1, 0, 0],
                                                   [0, 1, delta/2],
                                                   [0, delta/2, 1]]))

        strain_list.append(lambda delta: np.array([[1, 0, delta/2],
                                                   [0, 1, 0],
                                                   [delta/2, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1, delta/2, 0],
                                                   [delta/2, 1, 0],
                                                   [0, 0, 1]]))

        strain_list.append(lambda delta: np.array([[1 + 2 * delta, 0, 0],
                                                   [0, 1 - delta, 0],
                                                   [0, 0, 1 - delta]]))

        strain_list.append(lambda delta: np.array([[1 - delta, 0, 0],
                                                   [0, 1 + 2 * delta, 0],
                                                   [0, 0, 1 - delta]]))

        strain_list.append(lambda delta: np.array([[1 - delta, delta, 0],
                                                   [delta, 1 - delta, 0],
                                                   [0, 0, 1 + 2 * delta]]))

    return test_type_list, strain_list, delta_list


def solve(cryst_sys, combined_econst_array):
    """

    Solves for the elastic constants from the matrix and coeffs.

    Argument cryst_sys is one of ['cubic', 'hexagonal', 'tetragonal',
    'orthorhombic'] for now.

    Used in combination with the function get_test_type_strain_delta_list. The
    argument combined_econst_array is an array of the second order polynomial
    coefficients coming from the runs with various test_type, in the same order.

    """
    if cryst_sys == 'cubic':
        econsts_str = ["C11", "C12", "C44"]
        coeff_matrix = np.array([[3/2., 3, 0],
                                 [1, -1, 0],
                                 [0, 0, 1/2.]])

    elif cryst_sys == 'hexagonal':
        econsts_str = ["C11", "C12", "C13", "C33", "C44"]
        coeff_matrix = np.array([[1, 1, 2, 1/2., 0],
                                 [1, -1, 0, 0, 0],
                                 [1, 1, 0, 0, 0],
                                 [0, 0, 0, 0, 2],
                                 [0, 0, 0, 1/2., 0]])

    elif cryst_sys == 'tetragonal':
        econsts_str = ["C11", "C33", "C44", "C12", "C13", "C66"]
        coeff_matrix = np.array([[1/2., 0, 0, 0, 0, 0],
                                 [0, 1/2., 0, 0, 0, 0],
                                 [0, 0, 2, 0, 0, 0],
                                 [5 / 2., 1/2., 0, -2, -1, 0],
                                 [1, 2, 0, 1, -4, 0],
                                 [1, 2, 0, 1, -4, 2]])

    elif cryst_sys == 'orthorhombic':
        econsts_str = ["C11", "C22", "C33", "C44", "C55", "C66", "C12", "C13", "C23"]
        coeff_matrix = np.array([[1/2., 0, 0, 0, 0, 0, 0, 0, 0],
                                 [0, 1/2., 0, 0, 0, 0, 0, 0, 0],
                                 [0, 0, 1/2., 0, 0, 0, 0, 0, 0],
                                 [0, 0, 0, 1/2., 1, 0, 0, 0, 0],
                                 [0, 0, 0, 0, 1/2., 0, 0, 0, 0],
                                 [0, 0, 0, 0, 0, 1/2., 0, 0, 0],
                                 [2, 1/2., 1/2., 0, 0, 0, -2, -2, 1],
                                 [1/2., 2, 1/2., 0, 0, 0, -2, 1, -2],
                                 [1/2., 1/2., 2, 0, 0, 0, 1, -2, -2]])

    solved = np.linalg.solve(coeff_matrix, combined_econst_array)
    return dict(zip(econsts_str, solved))
