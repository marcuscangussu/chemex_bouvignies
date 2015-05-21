from __future__ import print_function

import importlib
import collections

import numpy as np

from chemex import util

sign = np.array([1.0, -1.0])


def calculate_shift_ex_2st(pb=0.0, kex=0.0, dw=0.0, r_ixy=0.0, dr_ixy=0.0):
    """Corrects major and minor peak positions in presence of exchange."""

    kab = kex * pb
    kba = kex - kab

    k2ab = r_ixy + kab
    k2ba = r_ixy + dr_ixy - 1j * dw + kba

    k2ex = k2ab + k2ba
    fac = ((k2ab - k2ba) ** 2 + 4.0 * kab * kba) ** 0.5

    nu1, nu2 = (0.5 * (-k2ex + sign * fac)).imag

    if abs(nu1) > abs(nu2):
        nu1, nu2 = nu2, nu1

    return nu1, nu2


def correct_intensities(magz_a=1.0, magz_b=0.0, pb=0.0, kex=0.0, dw=0.0,
                        r_ixy=0.0, dr_ixy=0.0):
    """Corrects major and minor peak intensities in presence of exchange."""

    kab = kex * pb
    kba = kex - kab

    k2ab = r_ixy + kab
    k2ba = r_ixy + dr_ixy - 1j * dw + kba

    k2ex = k2ab + k2ba
    fac = ((k2ab - k2ba) ** 2 + 4.0 * kab * kba) ** 0.5

    nu1, nu2 = 0.5 * (-k2ex + sign * fac)

    magz_a_c = +(
        (kab - nu2 - k2ab) * magz_a +
        (kba + nu1 + k2ab) * magz_b
    ) / (nu1 - nu2)

    magz_b_c = -(
        (kab - nu1 - k2ab) * magz_a +
        (kba + nu2 + k2ab) * magz_b
    ) / (nu1 - nu2)

    if abs(nu1.imag) > abs(nu2.imag):
        magz_a_c, magz_b_c = magz_b_c, magz_a_c

    if abs(np.angle(magz_a_c)) <= 0.5 * np.pi:
        magz_a_c = +abs(magz_a_c)
    else:
        magz_a_c = -abs(magz_a_c)

    if abs(np.angle(magz_b_c)) <= 0.5 * np.pi:
        magz_b_c = +abs(magz_b_c)
    else:
        magz_b_c = -abs(magz_b_c)

    return magz_a_c, magz_b_c


def calc_peak_intensity(pb=0.0, kex=0.0, dw=0.0, intensities=None):
    """Calculates the intensity of the volume of the peak in presence of
    chemical exchange.
    """

    if intensities is None:
        return None

    magz_a, magz_b = intensities
    magz_a, magz_b = correct_intensities(
        magz_a=magz_a,
        magz_b=magz_b,
        pb=pb,
        kex=kex,
        dw=dw,
        r_ixy=0.0
    )

    return magz_a


def get_par(par_name, par, par_indexes, par_fixed=list()):

    if par_name in par_indexes:
        return par[par_indexes[par_name]]

    else:
        return par_fixed[par_name]


def calc_multiplet(couplings=None, multiplet=None):
    couplings = list(couplings)

    if multiplet is None:
        multiplet = [0.0]

    if couplings:

        j = couplings.pop()

        multiplet_updated = [
            frq + sign * j * np.pi
            for frq in multiplet
            for sign in (1.0, -1.0)
        ]

        return calc_multiplet(couplings, multiplet_updated)

    else:

        counter = collections.Counter(multiplet)
        nb_component = sum(counter.values())

        multiplet = tuple((val, count / float(nb_component))
                          for val, count in sorted(counter.items()))

        return multiplet


def format_experiment_help(type_experiment, name_experiment):

    headline1 = "Experimental parameters"
    headline2 = "Fitted parameters (by default)"
    headline3 = "Fixed parameters (by default)"

    subtype_experiment = name_experiment.replace(
        ''.join(['_', type_experiment]), '')

    module_exp = importlib.import_module(
        '.'.join(['chemex.experiments', type_experiment, subtype_experiment])
    )

    title = module_exp.__doc__.split('\n')[0]
    description = '\n'.join(module_exp.__doc__.split('\n')[1:]).strip('\n')

    util.header1(title)
    print("")
    print(description)
    print("")

    util.header2(headline1)
    for name in module_exp.attributes_exp:
        print("  * {:s}".format(name))

    util.header2(headline2)
    for name, settings in module_exp.params_exp.items():
        if settings['vary']:
            print("  * {:s}".format(name))

    util.header2(headline3)
    for name, settings in module_exp.params_exp.items():
        if not settings['vary']:
            print("  * {:s}".format(name))
