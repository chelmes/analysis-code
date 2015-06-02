"""
determinant equations for different moving frames and representations.
"""

import numpy as np

from ._memoize import memoize
from ._omega import omega
from ._calc_energies import calc_gamma

@memoize(50)
def det000(L, mpi, a0, r0, q2):
    """Calculates the determinant equation for CMF in A1 irrep.

    Args:
        mpi: lattice pion mass
        L: lattice size
        a0: scattering length for l=0
        r0: scattering radius for l=0
        q2: momentum squared

    Returns:
        The value of the determinant equation for the given parameters.
    """
    d = np.array([0., 0., 0.])
    omega00 = omega(q2, gamma=1., l=0, m=0, d=d)
    q = np.sqrt(q2) * 2. * np.pi / float(L)
    delta = a0 / q + 0.5 * r0 * q
    return (omega00 - delta).real

@memoize(50)
def det000_E(L, mpi, a2, r2, q2):
    """Calculates the determinant equation for CMF in E irrep.

    Args:
        mpi: lattice pion mass
        L: lattice size
        a2: scattering length for l=2
        r2: scattering radius for l=2
        q2: momentum squared

    Returns:
        The value of the determinant equation for the given parameters.
    """
    d = np.array([0., 0., 0.])
    omega00 = omega(q2, gamma=1., l=0, m=0, d=d)
    omega40 = omega(q2, gamma=1., l=4, m=0, d=d)
    q = np.sqrt(q2) * 2. * np.pi / float(L)
    delta = a2 / q**5 + 0.5 * r2 / q**3
    return (omega00 + 18. * omega40 / 7. - delta).real

@memoize(50)
def det000_T2(L, mpi, a2, r2, q2):
    """Calculates the determinant equation for CMF in T2 irrep.

    Args:
        mpi: lattice pion mass
        L: lattice size
        a2: scattering length for l=2
        r2: scattering radius for l=2
        q2: momentum squared

    Returns:
        The value of the determinant equation for the given parameters.
    """
    d = np.array([0., 0., 0.])
    omega00 = omega(q2, gamma=1., l=0, m=0, d=d)
    omega40 = omega(q2, gamma=1., l=4, m=0, d=d)
    q = np.sqrt(q2) * 2. * np.pi / float(L)
    delta = a2 / q**5 + 0.5 * r2 / q**3
    return (omega00 - 12. * omega40 / 7. - delta).real

@memoize(50)
def det001(L, mpi, a0, r0, a2, r2, q2):
    """Calculates the determinant equation for MF1 in A1 irrep.

    Args:
        mpi: lattice pion mass
        L: lattice size
        a0: scattering length for l=0
        r0: scattering radius for l=0
        a2: scattering length for l=2
        r2: scattering radius for l=2
        q2: momentum squared

    Returns:
        The value of the determinant equation for the given parameters.
    """
    d = np.array([0., 0., 1.])
    gamma = calc_gamma(q2, mpi, L, d)
    omega00 = omega(q2, gamma=gamma, l=0, m=0, d=d)
    omega20 = omega(q2, gamma=gamma, l=2, m=0, d=d)
    omega40 = omega(q2, gamma=gamma, l=4, m=0, d=d)
    q = np.sqrt(q2) * 2. * np.pi / float(L)
    delta0 = a0 / q + 0.5 * r0 * q
    delta2 = a2 / q**5 + 0.5 * r2 / q**3
    return ((omega00 - delta0) * (omega00 + 10. * omega20 / 7. + \
           18. * omega40 / 7. - delta2) - 5. * omega20**2).real

@memoize(50)
def det110(L, mpi, a0, r0, a2, r2, q2):
    """Calculates the determinant equation for MF2 in A1 irrep.

    Args:
        mpi: lattice pion mass
        L: lattice size
        a0: scattering length for l=0
        r0: scattering radius for l=0
        a2: scattering length for l=2
        r2: scattering radius for l=2
        q2: momentum squared

    Returns:
        The value of the determinant equation for the given parameters.
    """
    d = np.array([1., 1., 0.])
    gamma = calc_gamma(q2, mpi, L, d)
    omega00 = omega(q2, gamma=gamma, l=0, m=0, d=d)
    omega20 = omega(q2, gamma=gamma, l=2, m=0, d=d)
    omega22 = omega(q2, gamma=gamma, l=2, m=2, d=d)
    omega40 = omega(q2, gamma=gamma, l=4, m=0, d=d)
    omega42 = omega(q2, gamma=gamma, l=4, m=2, d=d)
    omega44 = omega(q2, gamma=gamma, l=4, m=4, d=d)
    q = np.sqrt(q2) * 2. * np.pi / float(L)
    delta0 = a0 / q + 0.5 * r0 * q
    delta2 = a2 / q**5 + 0.5 * r2 / q**3
    # splitted over several lines, maybe there is a way to make structure
    # more clear
    term1 =-(10. * np.sqrt(2.) * omega22 / 7. -\
           3. * np.sqrt(30.) * omega42 / 7.) * \
           ((3. * np.sqrt(30.) * omega42 / 7. -\
           10. * np.sqrt(2.) * omega22 / 7.) * (omega00 - delta0) -\
           5. * np.sqrt(2.) * omega20 * omega22)
    term2 = np.sqrt(5.) * omega20 *\
           (-np.sqrt(5.) * delta2 * omega20 -\
           10. * np.sqrt(5.) * omega20**2 / 7. +\
           np.sqrt(5.) * omega00 * omega20 +\
           3. * np.sqrt(5.0) * omega40 * omega20 / 7. -\
           15. * np.sqrt(2.0) * omega44 * omega20 / np.sqrt(7.) -\
           20. * np.sqrt(5.0) * omega22**2 / 7. +\
           30. * np.sqrt(3.0) * omega22 * omega42 / 7.)
    term3 = (omega00 + 10. * omega20 / 7. + 18. * omega40 / 7. - delta2) *\
           ((omega00 - delta0) *\
           (omega00 - 10. * omega20 / 7. + 3. * omega40 / 7. -\
           3. * np.sqrt(10.) * omega44 / np.sqrt(7.) - delta2) +\
           10. * omega22**2)
    return (term1 - term2 + term3).real

@memoize(50)
def det111(L, mpi, a0, r0, a2, r2, q2):
    """Calculates the determinant equation for MF3 in A1 irrep.

    Args:
        mpi: lattice pion mass
        L: lattice size
        a0: scattering length for l=0
        r0: scattering radius for l=0
        a2: scattering length for l=2
        r2: scattering radius for l=2
        q2: momentum squared

    Returns:
        The value of the determinant equation for the given parameters.
    """
    d = np.array([1., 1., 1.])
    gamma = calc_gamma(q2, mpi, L, d)
    omega00 = omega(q2, gamma=gamma, l=0, m=0, d=d)
    omega22 = omega(q2, gamma=gamma, l=2, m=2, d=d)
    omega40 = omega(q2, gamma=gamma, l=4, m=0, d=d)
    omega42 = omega(q2, gamma=gamma, l=4, m=2, d=d)
    q = np.sqrt(q2) * 2. * np.pi / float(L)
    delta0 = a0 / q + 0.5 * r0 * q
    delta2 = a2 / q**5 + 0.5 * r2 / q**3
    return ( (omega00 - delta0) *\
        (omega00 - 12. * omega40 / 7. - 12.j * np.sqrt(10.) * omega42 / 7. -\
        10.j * np.sqrt(6.) * omega22 / 7. - delta2) +\
        30. * omega22**2 ).real
