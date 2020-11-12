import numpy as np
import cmath
import math


def complex_phase(c):
    """
   compute phase of a complex number

   MB 2014-06-19:
   since I switched to use linalg.eigen to calculate
   eigen values and vectors, I noticed that some z1 vectors have an
   imaginary value of -0 that results in Z1 phase to be -pi
   and as a result would produce Phi VH values > +/-90 degrees
   I am now using this function to compute phase to avoid
   this issue.
   """
    if abs(c) < 1.0e-6:
        return 0.0
    if c.imag == -0.0:
        c = complex(c.real, 0.0)
    return cmath.phase(c)


def lambda_power(eigenvalue, norm):
    """
   degree of polarization (Beta^2)

   Variation of this spectrum is very similar to that of
   the individual components
   """
    return 10 * np.log10(norm * eigenvalue)


def polarization_degree(m11, m12, m13, m22, m23, m33):
    """
    degree of polarization (Beta^2)

   based on the C code from Keith Koper

   compute degree of polarization (between 0 and 1
   EQ 31, Samson (1983), GJRAS 72, 647-664

   The degree of polarization Beta^2 of a process with spectral
   density matrix S is given by (Samson & Olson 1980)

   Beta^2 measures the extent to which the noise is organized
   and can be described by fewer than 3 degree of freedom.
   It varies from
       0 when all the eigenvalues are equal (not polarized) to
       1 when only a single non-zero eigenvalue (pure body wave) exists
   polarization is considered to be substantial when
   Beta^2 >= 0.5

   Beta^2 = (nTrS^2 - (TrS)^2) / (n -1)x( TrS)^2 0<= Beta^2 <=1

   where Beta^2 = 0, only if S =dIn

   Tr is trace of matrix S -> (S11+S22+S33)
   """
    t1 = ((m11.real * m11.real) +
          (m22.real * m22.real) +
          (m33.real * m33.real) +
          2.0 * abs(m12) * abs(m12) +
          2.0 * abs(m13) * abs(m13) +
          2.0 * abs(m23) * abs(m23))

    t2 = m11.real + m22.real + m33.real

    beta = (3.0 * t1 - t2 * t2) / (2.0 * t2 * t2)

    return beta


def lambda_power(eigenvalue):
    """
   Lambda Power

   power spectrum of the primary eigenvalue (Lambda).
   Variation of this spectrum is very similar to that of
   the individual components

   """
    return eigenvalue


def polarization_angles(z1, z2, z3):
    """
       Polarization Angles

      based on the C code from Keith Koper

      This is the main function that takes the primary eigenvector
      and compute relavant phase relationships and polarizations following
      Park et al. 1987, page 12:665-666s


      z1, z2, and z3 are eigenvectors of the maximum eigenvalue
   """

    # Theta_h first by trying 4 posibilities of equation 7
    # picking the one that maximizes (not minimizes) equation 5.
    val = -0.5 * complex_phase(z2 * z2 + z3 * z3)
    for l in range(0, 4):
        angle = val + float(l) * math.pi / 2.0
        tmp = (abs(z2) * abs(z2) * np.cos(angle + complex_phase(z2)) * np.cos(angle + complex_phase(z2))) + \
              (abs(z3) * abs(z3) * np.cos(angle + complex_phase(z3)) * np.cos(angle + complex_phase(z3)))
        if l == 0:
            max = tmp
            theta_h = angle
        elif tmp > max:
            max = tmp
            theta_h = angle

    # Now calculate thetaH from theta_h following equation 8 and taking care
    # to get the sign right. Note the Park et al. gives thetaH as counterclockwise
    # from East, whearas for backazimuth we normally want clockwise from North.
    ztmp = complex(np.cos(theta_h), - np.sin(theta_h))

    zval3 = z3 * ztmp
    zval2 = z2 * ztmp
    thetah = math.atan2(zval3.real, zval2.real)

    zval13 = z1 * z3.conjugate()
    val = float(zval13.real)

    if val < 0.0:
        if thetah < 0.0:
            thetah += math.pi
    else:
        if thetah > 0.0:
            thetah -= math.pi

    thetah = math.pi / 2.0 - thetah
    if thetah < 0.0:
        thetah += 2.0 * math.pi

    thetah *= 180.0 / math.pi

    # Get phiHH, which is the phase difference between horizontals.
    phihh = (complex_phase(z3) - complex_phase(z2)) * 180.0 / math.pi
    if phihh > 180.0:
        phihh -= 360.0
    elif phihh < -180.0:
        phihh += 360.0

    # Theta_v by trying 4 posibilities of equation 9
    # picking the one that maximizes the proper expression (not in the paper).
    val = -0.5 * complex_phase(z1 * z1 + z2 * z2 + z3 * z3)
    for l in range(0, 4):
        angle = val + float(l) * math.pi / 2.0
        tmp = abs(z1) * abs(z1) * np.cos(angle + complex_phase(z1)) * np.cos(angle + complex_phase(z1)) + \
              abs(z2) * abs(z2) * np.cos(angle + complex_phase(z2)) * np.cos(angle + complex_phase(z2)) + \
              abs(z3) * abs(z3) * np.cos(angle + complex_phase(z3)) * np.cos(angle + complex_phase(z3))
        if l == 0:
            max = tmp
            theta_v = angle
        elif tmp > max:
            max = tmp
            theta_v = angle
    # Calculate thetav from theta_v following equation 10
    # this gives the incidence angle, 0 for vertical, 90 for horizontal.
    zh = cmath.sqrt(z2 * z2 + z3 * z3)

    if zh.imag < 0:
        zh = complex(-1 * zh.real, -1 * zh.imag)
    ztmp = complex(np.cos(theta_v), -1 * np.sin(theta_v))
    thetav = math.atan(abs((z1 * ztmp).real / (zh * ztmp).real))
    thetav *= 180.0 / math.pi
    thetav = 90 - thetav

    # Get phiVH, between -90 and 90.
    phivh = (theta_h - complex_phase(z1)) * 180.0 / math.pi

    if phivh > 90.0:
        phivh -= 180.0
    elif phivh < -90.0:
        phivh += 180.0

    return thetah, phihh, thetav, phivh

