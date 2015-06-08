################################################################################
#
# Author: Bastian Knippschild (b.knippschild@gmx.de)
# Date:   Februar 2015
#
# Copyright (C) 2015 Bastian Knippschild
# 
# This program is free software: you can redistribute it and/or modify it under 
# the terms of the GNU General Public License as published by the Free Software 
# Foundation, either version 3 of the License, or (at your option) any later 
# version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT 
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with tmLQCD. If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
#
# Function: Functions to fit and plot.
#
# For informations on input parameters see the description of the function.
#
################################################################################

from scipy.optimize import leastsq
import scipy.stats
import numpy as np
import matplotlib
matplotlib.use('QT4Agg') # has to be imported before the next lines
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import analyze_fcts as af

def fitting(fitfunc, X, Y, start_parm, correlated=True, verbose=True):
    """A function that fits a correlation function.

    This function fits the given function fitfunc to the data given in X and Y.
    The function needs some start values, given in start_parm, and can use a
    correlated or an uncorrelated fit.

    Args:
        fitfunc: The function to fit to the data.
        X: The time slices.
        Y: The bootstrap samples of the data.
        start_parm: The starting parameters for the fit.
        correlated: Flag to use a correlated or uncorrelated fit.
        verbose: Controls the amount of information written to the screen.

    Returns:
        The function returns the fitting parameters, the chi^2 and the p-value
        for every bootstrap sample.
    """
    errfunc = lambda p, x, y, error: np.dot(error, (y-fitfunc(p,x)).T)
    # compute inverse, cholesky decomposed covariance matrix
    if not correlated:
        cov = np.diag(np.diagonal(np.cov(Y.T)))
    else:
        cov = np.cov(Y.T)
    cov = (np.linalg.cholesky(np.linalg.inv(cov))).T

    # degrees of freedom
    dof = float(Y.shape[1]-len(start_parm)) 
    # create results arrays
    res = np.zeros((Y.shape[0], len(start_parm)))
    chisquare = np.zeros(Y.shape[0])
    # The FIT to the boostrap samples
    for b in range(0, Y.shape[0]):
        p,cov1,infodict,mesg,ier = leastsq(errfunc, start_parm,
                                   args=(X, Y[b,:], cov), full_output=1)
        chisquare[b] = float(sum(infodict['fvec']**2.))
        res[b] = np.array(p)
    # calculate mean and standard deviation
    res_mean, res_std = np.mean(res, axis=0), np.std(res, axis=0)
    chi2 = np.median(chisquare)
    # p-value calculated
    pvals = 1. - scipy.stats.chi2.cdf(chisquare, dof)

    # The fit to the mean value
    y = np.mean(Y, axis=0)
    p,cov1,infodict,mesg,ier = leastsq(errfunc, start_parm, \
                               args=(X, y, cov), full_output=1)

    # writing results to screen
    if verbose:
        if correlated:
            print("fit results for a correlated fit:")
        else:
            print("fit results for an uncorrelated fit:")
        print("degrees of freedom: %f\n" % dof)
        
        print("bootstrap fit:")
        for rm, rs in zip(res_mean, res_std):
            print("  %.6e +/- %.6e") % (rm, rs)
        print("Chi^2/dof: %.6e +/- %.6e\n" % (chi2/dof,
              np.std(chisquare)/dof))

        print("mean value fit:")
        for rm, rs in zip(p, res_std):
            print("  %.6e +/- %.6e") % (rm, rs)
        print("Chi^2/dof: %.6e +/- %.6e\n" % (float(sum(infodict['fvec']**2.) /
              dof), np.std(chisquare)/dof))

        print("original data fit:")
        for rm, rs in zip(res[0], res_std):
            print("  %.6e +/- %.6e") % (rm, rs)
        print("Chi^2/dof: %.6e +/- %.6e" % (chisquare[0]/dof, np.std(chisquare)
              /dof))
        print("p-value: %lf" % pvals[0]) 

    return res, chisquare, pvals

def quantile_1D(data, weights, quantile):
    ind_sort = np.argsort(data)
    sort_data = data[ind_sort]
    sort_weig = wheights[ind_sort]
    Sn = np.cumsum(sort_weig)
    Pn = (Sn - 0.5*sort_weig) / np.sum(sort_weig)
    return np.interp(quantile, Pn, sort_data)

def fitting_range(fitfunc, X, Y, start_parm, correlated=True, verbose=True):
    """A function that fits a correlation function for different fit ranges.

    This function fits the given function fitfunc to the data given in X and Y.
    The function needs some start values, given in start_parm, and can use a
    correlated or an uncorrelated fit. Fits are performed for many different
    fit ranges.

    Args:
        fitfunc: The function to fit to the data.
        X: The time slices.
        Y: The bootstrap samples of the data.
        start_parm: The starting parameters for the fit.
        correlated: Flag to use a correlated or uncorrelated fit.
        verbose: Controls the amount of information written to the screen.

    Returns:
    """
    # vary the lower and upper end of the fit range
    for lo in range(int(Y.shape[1]/4), Y.shape[1]-5):
        for up in range(lo+5, x.shape[1]):
            # fit the data
            res, chi2, pval=fitting(fitfunc, X[lo:up], Y[:,lo:up], start_params,
                                    correlated=correlated, verbose=verbose)
            # calculate the weight
            weight = ((1. - np.abs(pval - 0.5)) * (1.0))**2
            # calculate weighted median
            median = quantile_1D(res[:,1], weight, 0.5)

            # print some result on screen
            print("%2d-%2d: p-value %.7lf, chi2/dof %.7lf, E %.7lf" % (lo, up,
                  pval[0], chi2[0]/(len(X[lo:up])-len(start_params)),median))




def scan_fit_range(fitfunc, X, Y, start_params, correlated=True, verbose=False):
    """Fits the fitfunction to the data for different fit ranges and prints the
       result.

       Args:
           fitfunc: The function to fit.
           X: The time slices.
           Y: The bootstrap samples of the data.
           start_params: The start parameters for the fit.
           correlated: Correlated or uncorrelated fit.
           verbose: Verbosity of the fit function.

       Returns:
           Nothing.
    """
    ## vary the lower end of the fit range
    #for lo in range(int(Y.shape[1]/4), Y.shape[1]-5):
    #    # vary the upper end of the fit range
    #    for up in range(lo+5, Y.shape[1]):
    # vary the lower end of the fit range
    for lo in range(7, 13):
        # vary the upper end of the fit range
        for up in range(15, 19):
            # fir the data
            res, chi2, pval=fitting(fitfunc, X[lo:up], Y[:,lo:up], start_params,
                                    correlated=correlated, verbose=verbose)
            # print some result on screen
            print("%2d-%2d: p-value %.7lf, chi2/dof %.7lf, E %.7lf" % (lo, up,
                  pval[0], chi2[0]/(len(X[lo:up])-len(start_params)),res[0,-1]))

    return

def set_fit_intervall(data, lolist, uplist, intervallsize):
    """Initialize intervalls to fit in with borders given for every principal
    correlator

    Args: 
        data: The lattice results to fit to. Necessary to obtain the number of
              gevp-eigenvalues.
        lolist: List of lower interval borders for every gevp-eigenvalue.
        uplist: List of upper interval borders for every gevp-eigenvalue.
        intervallsize: Minimal number of points to be contained in the 
                intervall

    Returns:
        fit_intervals: list of pairs [lo, up] for every gevp-eigenvalue.
    """

    ncorr = data.shape[2]
    fit_intervalls = []
    for _l in range(ncorr):
        fit_intervalls.append([])
        for lo in range(lolist[_l], uplist[_l]):
            for up in range(lolist[_l], uplist[_l]):
                if (up - lo) > intervallsize - 1:
                    fit_intervalls[_l].append([lo, up])

    return fit_intervalls


def genfit(data, fit_intervalls, fitfunc, start_params, tmin, lattice, d, label,
            path=".plots/", plotlabel="corr", verbose=True):
    """Fit and plot the correlation function.
    
    Args:
        data: The correlation functions.
        fit_intervalls: List of intervalls for the fit for the different
              correlation functions.
        fitfunc: The function to fit to the data.
        start_params: The starting parameters for the fit function.
        tmin: Lower bound of the plot.
        lattice: The name of the lattice, used for the output file.
        d: The total momentum of the reaction.
        label: Labels for the title and the axis.
        path: Path to the saving place of the plot.
        plotlabel: Label for the plot file.
        verbose: Amount of information printed to screen.

    Returns:
        res: Result of the fit to each bootstrap sample.
        chi2: Chi^2 for every fit
        pval: p-value for every fit.
    """
    # init variables
    nboot = data.shape[0]
    T2 = data.shape[1]
    ncorr = data.shape[2]
    npar = len(start_params)
    # same intervall size for all correlators hardcoded
    ninter = len(fit_intervalls[0])
    d2 = np.dot(d,d)
    # initialize empty arrays
    res = np.zeros((nboot, npar, ncorr, ninter))
    chi2 = np.zeros((nboot, ncorr, ninter))
    pval = np.zeros((nboot, ncorr, ninter))
    # set fit data
    tlist = np.linspace(0., float(T2), float(T2), endpoint=False)
    # outputfile for the plot
    corrplot = PdfPages("%s/fit_%s_%s_TP%d.pdf" % (path,plotlabel,lattice,d2))
    # check the labels
    if len(label) < 3:
        print("not enough labels, using standard labels.")
        label = ["fit", "time", "C(t)", "", ""]
    if len(label) < 4:
        label.append("data")
        label.append("")
    if len(label) < 5:
        label.append("")
    label_save = label[0]
    for _l in range(ncorr):
        ninter = len(fit_intervalls[_l])
        # setup
        mdata, ddata = af.return_mean_corr(data[:,:,_l])
        for _i in range(ninter):
            lo = fit_intervalls[_l][_i][0]
            up = fit_intervalls[_l][_i][1]
            if verbose:
                print("Intervall [%d, %d]" % (lo, up))
                print("correlator %d" % _l)
            print("Intervall [%d, %d]" % (lo, up))

            # fit the energy and print information
            if verbose:
                print("fitting correlation function")

            res[:,:,_l,_i], chi2[:,_l,_i], pval[:,_l,_i] =fitting(fitfunc, 
                    tlist[lo:up], data[:,lo:up,_l], start_params, verbose=False)
            if verbose:
                print("%d\tres = %lf\t%lf" % (_i, res[0, 0, _l, _i], res[0, 1, _l, _i]))
                print("p-value %.7lf\nChi^2/dof %.7lf" % (pval[0,_l, _i], chi2[0,_l, _i]/(
                      (up - lo) - len(start_params))))

            mres, dres = af.return_mean_corr(res[:,:,_l,_i])

            # set up the plot labels
            fitlabel = "fit %d:%d" % (lo, up-1)
            title="%s, %s, TP %d, pc %d, [%d, %d]" % (label_save, lattice, d2, 
                                                      _l, lo, up)
            label[0] = title
            label[4] = fitlabel

            # plot the data and the fit
            if verbose:
                print("plotting")
            corr_fct_with_fit(tlist, data[0,:,_l], ddata, fitfunc, mres,
                                   [tmin,T2], label, corrplot, True)
    corrplot.close()
    return res, chi2, pval

def corr_fct_with_fit(X, Y, dY, fitfunc, args, plotrange, label, pdfplot,
                      logscale=False, setLimits=False):
    """A function that fits a correlation function.

    This function plots the given data points and the fit to the data. The plot
    is saved to pdfplot. It is assumed that pdfplot is a pdf backend to
    matplotlib so that multiple plots can be saved to the object.

    Args:
        X: The data for the x axis.
        Y: The data for the y axis.
        dY: The error on the y axis data.
        fitfunc: The function to fit to the data.
        args: The parameters of the fit function from the fit.
        plotrange: A list with two entries, the lower and upper range of the
                   plot.
        label: A list with labels for title, x axis, y axis, data and fit.
        pdfplot: A PdfPages object in which to save the plot.
        logscale: Make the y-scale a logscale.

    Returns:
        Nothing.
    """
    # plotting the data
    l = int(plotrange[0])
    u = int(plotrange[1])
    p1 = plt.errorbar(X[l:u], Y[l:u], dY[l:u], fmt='x' + 'b', label = label[3])
    # plotting the fit function
    x1 = np.linspace(l, u, 1000)
    y1 = []
    for i in x1:
        y1.append(fitfunc(args,i))
    y1 = np.asarray(y1)
    p2, = plt.plot(x1, y1, 'r', label = label[4])
    # adjusting the plot style
    plt.grid(True)
    plt.xlabel(label[1])
    plt.ylabel(label[2])
    plt.title(label[0])
    plt.legend()
    if logscale:
        plt.yscale('log')
    # set the yaxis range
    if setLimits:
        plt.ylim(0.25, 1.)
    # save pdf
    pdfplot.savefig()
    plt.clf()

# this can be used to plot the chisquare distribution of the fits
#  x = np.linspace(scipy.stats.chi2.ppf(1e-6, dof), scipy.stats.chi2.ppf(1.-1e-6, dof), 1000)
#  hist, bins = np.histogram(chisquare, 50, density=True)
#  width = 0.7 * (bins[1] - bins[0])
#  center = (bins[:-1] + bins[1:]) / 2
#  plt.xlabel('x')
#  plt.ylabel('chi^2(x)')
#  plt.grid(True)
#  plt.plot(x, scipy.stats.chi2.pdf(x, dof), 'r-', lw=2, alpha=1, label='chi2 pdf')
#  plt.bar(center, hist, align='center', width=width)
#  plt.show()

# compute weights
################################################################################
# Input: corr      -> the correlator
#          params -> contains the p-value for each correlator
# Output: returns the weights or an empty array
def compute_weight(corr, params):
    errors = np.std(corr, axis=1)
    max_err = np.amax(errors)
    if len(params) != 0:
        weights = []
        for i in range(0, params.shape[0]):
            w = (1.-abs(params[i,1]-0.5))*max_err/errors[i]
            weights.append(w**2)
            return weights
    else:
        return []

# compute the weighted quantile
################################################################################
def weighted_quantile(data, weights, quantile):
    """Compute the weighted quantile, where a fixed percentage of the sum of
    all weights lie below.

    Args:
        data: A numpy-array of the data points the quantile is taken from.
        weights: A numpy-array containing the weights for each point in data. 
              Must be of same shape and have same order as data.
        quantile: The percentage of weights to be below the quantile. 
              0.5 is the weighted median
    """

    ind_sorted = np.argsort(data)
    sorted_data = data[ind_sorted]
    sorted_weights = weights[ind_sorted]
    # Compute the auxiliary arrays
    Sn = np.cumsum(sorted_weights)
    Pn = (Sn-0.5*sorted_weights)/np.sum(sorted_weights)
    # Get the value of the weighted median
    interpolated_quant = np.interp(quantile, Pn, sorted_data)

    return interpolated_quant

def plot_histogram(data, data_weight, lattice, d, label, path=".plots/", plotlabel="hist", 
                   verbose=True):

    """plot a weighted histogramm

    Args:
        data: Numpy-array of fit values for mulitple fit intervalls. Will be 
              depicted on x-axis.
        data_weight: The weights corresponding to data. Must have same shape
              and order as data. Their sum per bin is the bin height.
        lattice: The name of the lattice, used for the output file.
        d:    The total momentum of the reaction.
        label: Labels for the title and the axis.
        path: Path to the saving place of the plot.
        plotlabel: Label for the plot file.
        verbose: Amount of information printed to screen.

    Returns:
    """

    d2 = np.dot(d,d)
    ninter = data.shape[0]

    histplot = PdfPages("%s/fit_%s_%s_TP%d.pdf" % (path,plotlabel,lattice,d2))
    # The histogram

    hist, bins = np.histogram(data, 20, \
                              weights=data_weight, \
                              density=True)
    width = 0.7 * (bins[1] - bins[0])
    center = (bins[:-1] + bins[1:]) / 2

    plt.ylabel('weighted distribution of ' + label[2])
    plt.title('fit methods individually with a p-value between 0.01 and 0.99')
    plt.grid(True)
    x = np.linspace(center[0], center[-1], 1000)

#    plt.plot(x, scipy.stats.norm.pdf(x, loc=a_pipi_median_derv[0], \
#             scale=a_pipi_std_derv), 'r-', lw=3, alpha=1, \
#             label='median + stat. error')
    plt.bar(center, hist, align='center', width=width, color='r', alpha=0.5, \
            label='derivative')

    histplot.savefig()

    histplot.close()


