
import numpy as np
from _memoize import memoize

def WfromE(E, d=np.array([0., 0., 0.]), L=24):
    """Calculates the CM energery from the energy.

    Args:
        E: the energy
        d: total momentum vector of the system
        L: lattice size

    Returns:
        The center of mass energy.
    """
    return np.sqrt(E*E + np.dot(d, d) * 4. * np.pi*np.pi / (float(L)*float(L)))

@memoize(50)
def EfromW(W, d=np.array([0., 0., 0.]), L=24):
    """Calculates the moving frame energy from the CM energy.

    Args:
        W: the energy
        d: total momentum vector of the system
        L: lattice size

    Returns:
        The energy.
    """
    return np.sqrt(W*W - np.dot(d, d) * 4. * np.pi*np.pi / (float(L)* float(L)))

@memoize(50)
def WfromE_lat(E, d=np.array([0., 0., 0.]), L=24):
    """Calculates the CM energery from the energy using the lattice dispersion
    relation.

    Args:
        E: the energy
        d: total momentum vector of the system
        L: lattice size

    Returns:
        The center of mass energy.
    """
    return np.arccosh(np.cosh(E) + 2. * np.sum(np.sin(d*np.pi/float(L))**2))

@memoize(50)
def EfromW_lat(W, d=np.array([0., 0., 0.]), L=24):
    """Calculates the moving frame energy from the CM energy using the lattice
    dispersion relation.

    Args:
        W: the energy
        d: total momentum vector of the system
        L: lattice size

    Returns:
        The energy.
    """
    return np.arccosh(np.cosh(W) - 2. * np.sum(np.sin(d*np.pi/float(L))**2))

@memoize(50)
def EfromMpi(mpi, q, L):
    """Calculates the center of mass energy for a pion with momentum q.

    Args:
        mpi: pion mass
        q: pion momentum
        L: lattice size

    Returns:
        The energy.
    """
    return 2.*np.sqrt(mpi*mpi + 4.*q*q*np.pi*np.pi/(float(L)*float(L)))

@memoize(50)
def EfromMpi_lat(mpi, q, L):
    """Calculates the center of mass energy for a pion with momentum q using
    the lattice dispersion relation.

    Args:
        mpi: pion mass
        q: pion momentum
        L: lattice size

    Returns:
        The energy.
    """
    return 2. * np.arccosh(np.cosh(mpi) + 2. * np.sin(q * np.pi / float(L))**2)

def calc_gamma(q2, mpi, L, d):
    """Calculates the Lorentz boost factor for the given energy and momentum.

    Args:
        q2: the momentum squared
        mpi: the pion mass
        L: the lattice size
        d: the total momentum vector of the system

    Returns:
        The Lorentz boost factor.
    """
    E = EfromMpi(mpi, np.sqrt(q2), L)
    return WfromE(E, d, L) / E

def calc_Ecm(E, L, d=np.array([0., 0., 1.]), lattice=False):
    """Calculates the center of mass energy and the boost factor.

    Calculates the Lorentz boost factor and the center of mass energy
    for moving frames.

    Args:
        E: The energy of the moving frame.
        d: The total momentum of the moving frame.
        lattice: Use the lattice relation, see arxiv:1011.5288.

    Returns:
        The boost factor and the center of mass energies.
    """
    # if the data is from the cm system, return immediately
    if np.array_equal(d, np.array([0., 0., 0.])):
        gamma = np.ones(E.shape)
        return gamma, E
    # create the array for results
    Ecm = np.zeros((E.shape))
    gamma = np.zeros((E.shape))
    # lattice version, see arxiv:1011.5288
    if lattice:
        Ecm = EfromW_lat(E, d, L)
    # continuum relation
    else:
        Ecm = EfromW(E, d, L)
    gamma = E / Ecm
    return gamma, Ecm

def q2fromE_mpi(E, mpi, L):
    """Caclulates the q2 from the energy and pion mass.

    Args:
        E: The CM energy.
        mpi: The pion mass.
        L: The lattice size.

    Returns:
        q2: The CM momentum squared.
    """
    return (0.25*E*E - mpi*mpi) * (float(L) / (2. * np.pi))**2

def q2fromE_mpi_latt(E, mpi, L):
    """Caclulates the q2 from the energy and pion mass, lattice version.

    Args:
        E: The CM energy.
        mpi: The pion mass.
        L: The lattice size.

    Returns:
        q2: The CM momentum squared.
    """
    return (np.arcsin(np.sqrt((np.cosh(E*0.5)-np.cosh(mpi))*0.5))*\
            float(L)/ np.pi)**2

def calc_q2(E, mpi, L, lattice=False):
    """Calculates the momentum squared.

    Calculates the difference in momentum between interaction and non-
    interacting systems. The energy must be the center of mass energy.

    Args:
        E: The energy values for the bootstrap samples.
        mpi: The pion mass of the lattice.
        L: The spatial extent of the lattice.
        lattice: Use the lattice relation, see arxiv:1011.5288.

    Returns:
        An array of the q^2 values
    """
    if lattice:
        q2 = q2fromE_mpi_latt(E, mpi, L)
    else:
        q2 = q2fromE_mpi(E, mpi, L)
    return q2
