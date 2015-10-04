"""
The class for fitting.
"""

import numpy as np
import itertools
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from fit import LatticeFit, FitResult
from correlator import Correlators
from statistics import compute_error

class LatticePlot(object):
    def __init__(self, filename):
        """Initialize a plot.

        Parameters
        ----------
        filename : str
            The filename of the plot.
        """
        self.plotfile = PdfPages(filename)
        self.p = []

    def __del__(self):
        #if plt.get_fignums() > 0:
        #    print(plt.get_fignums())
        #    print("saving at last")
        #    self.save()
        self.plotfile.close()

    def save(self):
        if plt.get_fignums() > 0:
            for i in plt.get_fignums():
                self.plotfile.savefig(plt.figure(i))
        plt.clf()

    def set_title(self, title, axis):
        """Set the title and axis labels of the plot.

        Parameters
        ----------
        title : str
            The title of the plot.
        axis : list of strs
            The labels of the axis.
        """
        plt.title(title)
        plt.xlabel(axis[0])
        plt.ylabel(axis[1])

    def plot_data_with_fit(self, X, Y, dY, fitfunc, args, label, plotrange=None,
                       logscale=False, xlim=None, ylim=None, fitrange=None,
                       addpars=None, pval=None):
        """A function that plots data and the fit to the data.

        Parameters
        ----------
        X : ndarray
            The data for the x axis.
        Y : ndarray
            The data for the y axis.
        dY : ndarray
            The error on the y axis data.
        fitfunc : callable
            The function to fit to the data.
        args : ndarray
            The parameters of the fit function from the fit.
        label : list of str
            A list with labels for data and fit.
        plotrange : list of ints, optional
            The lower and upper range of the plot.
        logscale : bool, optional
            Make the y-scale a logscale.
        xlim, ylim : list of ints, optional
            Limits for the x and y axis, respectively
        fitrange : list of ints, optional
            A list with two entries, bounds of the fitted function.
        addpars : bool, optional
            if there are additional parameters for the fitfunction 
                 contained in args, set to true
        pval : float, optional
            write the p-value in the plot if given
        """
        # plot the data
        self.plot_data(X, Y, dY, label[0], plotrange=plotrange, logscale=logscale,
                xlim=xlim, ylim=ylim)

        # plot the function
        self.plot_function(fitfunc, X, args, label[1], addpars, fitrange)

        # adjusting the plot style
        plt.grid(True)
        plt.legend()

        # print label if available
        if pval is not None:
            # x and y position of the label
            x = np.max(X) * 0.7
            y = np.max(Y) * 0.8
            datalabel = "p-val = %.5f" % pval
            try:
                for k, d in enumerate(args[0]):
                    datalabel = "".join((datalabel, "\npar %d = %.4e" % (k, d)))
            except TypeError:
                datalabel = "".join((datalabel, "\npar = %.4e" % (args[0])))
            plt.text(x, y, datalabel)

    def plot_function(self, func, X, args, label, add=None, plotrange=None):
        """A function that plots a function.

        Parameters
        ----------
        func : callable
            The function to plot.
        Y : ndarray
            The data for the y axis.
        args : ndarray
            The arguments to the function.
        label : list of str
            A list with labels for data and fit.
        add : ndarray, optional
            Additional arguments to the fit function.
        plotrange : list of ints, optional
            The lower and upper range of the plot.
        """
        # plotting the fit function, check for seperate range
        if isinstance(plotrange, (np.ndarray, list, tuple)):
            plotrange = np.asarray(plotrange).flatten()
            if plotrange.size < 2:
                raise IndexError("fitrange has not enough indices")
            else:
                lfunc = int(plotrange[0])
                ufunc = int(plotrange[1])
        else:
            lfunc = X[0]
            ufunc = X[-1]
        x1 = np.linspace(lfunc, ufunc, 1000)
        if add is not None:
            y1 = []
            for j, x in enumerate(x1):
                y1.append(func(args, x, add[j]))
            y1 = np.asarray(y1)
        else:
            y1 = []
            for x in x1:
                y1.append(func(args, x))
            y1 = np.asarray(y1)
        plt.plot(x1, y1, "r", label=label)

    def plot_data(self, X, Y, dY, label, plotrange=None, logscale=False,
            xlim=None, ylim=None):
        """A function that plots data.

        Parameters
        ----------
        X : ndarray
            The data for the x axis.
        Y : ndarray
            The data for the y axis.
        dY : ndarray
            The error on the y axis data.
        label : list of str
            A list with labels for data and fit.
        plotrange : list of ints, optional
            The lower and upper range of the plot.
        logscale : bool, optional
            Make the y-scale a logscale.
        xlim, ylim : list of ints, optional
            Limits for the x and y axis, respectively
        """
        # check boundaries for the plot
        if isinstance(plotrange, (np.ndarray, list, tuple)):
            plotrange = np.asarray(plotrange).flatten()
            if plotrange.size < 2:
                raise IndexError("plotrange is too small")
            else:
                l = int(plotrange[0])
                u = int(plotrange[1])
            # plot the data
            self.p.append(plt.errorbar(X[l:u], Y[l:u], dY[l:u], fmt='x' + 'b',
                label = label))
        else:
            # plot the data
            self.p.append(plt.errorbar(X, Y, dY, fmt='x' + 'b', label=label))

        # adjusting the plot style
        plt.grid(True)
        plt.legend()
        if logscale:
            plt.yscale("log")
        # set the axis ranges
        if xlim:
            plt.xlim(xlim)
        if ylim:
            plt.ylim(ylim)

    def plot_histogram(data, data_weight, label, debug=0):
        """Plots histograms for the given data set.
    
        The function plots the weighted distribution of the data, the unweighted
        distribution and a plot containing both the weighted and the unweighted
        distribution.
    
        Parameters
        ----------
        data : ndarray
            Data set for the histogram.
        data_weight : ndarray
            The weights for the data, must have same shape as data.
        label : list of strs
            The title of the plots, the x-axis label and the label of the data.
        debug : int
            The amount of info printed.
        """
        # The histogram
        # generate weighted histogram
        hist, bins = np.histogram(data, 20, weights=data_weight, density=True)
        # generate the unweighted histogram
        uhist, ubins = np.histogram(data, 20, weights=np.ones_like(data_weight),
                                    density=True)
    
        # prepare the plot for the weighted histogram
        width = 0.7 * (bins[1] - bins[0])
        center = (bins[:-1] + bins[1:]) / 2
    
        # set labels for axis
        plt.title(label[0])
        plt.xlabel(label[1])
        plt.ylabel('weighted distribution')
        plt.grid(True)
        # plot
        plt.bar(center, hist, align='center', width=width, color='r', alpha=0.5,
                label=label[2])
        plt.legend()
        # save and clear
        self.save()
    
        # prepare plot for unweighted histogram
        # the center and width stays the same for comparison
        plt.title(label[0])
        plt.xlabel(label[1])
        plt.ylabel('unweighted distribution')
        plt.grid(True)
        # plot
        plt.bar(center, uhist, align='center', width=width, color='b', alpha=0.5,
                label=label[2])
        plt.legend()
        # save and clear
        self.save()
    
        # plot both histograms in same plot
        plt.title(label[0])
        plt.xlabel(label[1])
        plt.ylabel(label[2])
        plt.grid(True)
        # plot
        plt.bar(center, hist, align='center', width=width, color='r', alpha=0.5,
                label='weighted data')
        plt.bar(center, uhist, align='center', width=width, color='b', alpha=0.5,
                label='unweighted data')
        plt.legend()
        # save and clear
        self.save()

    def _genplot_single(self, corr, fitresult, fitfunc, label, add=None,
            debug=0):
        """Plot the data of a Correlators object and a FitResult object
        together.

        Parameters
        ----------
        corr : Correlators
            The correlation function data.
        fitresult : FitResult
            The fit data.
        fitfunc : LatticeFit
            The fit function.
        label : list of strs
            The title of the plot, the x- and y-axis titles, and the data label.
        add : ndarray, optional
            Additional arguments to the fit function. This is stacked along
            the third dimenstion to the oldfit data.
        debug : int, optional
            The amount of info printed.
        """
        if len(label) < 4:
            raise RuntimeError("not enough labels")
        if len(label) < 5:
            label.append("")
        if corr.matrix:
            raise RuntimeError("Cannot plot correlation function matrix")
        # get needed data
        ncorr = corr.shape[-1]
        ranges = fitresult.fit_ranges
        shape = fitresult.fit_ranges_shape
        X = np.linspace(0., float(corr.shape[1]), corr.shape[1], endpoint=False)
        label_save = label[0]

        # iterate over correlation functions
        for n in range(ncorr):
            mdata, ddata = compute_error(corr.data[:,:,n])
            
            # iterate over fit intervals
            for r in range(shape[0][n]):
                fi = ranges[n][r]
                mpar, dpar = compute_error(fitresult.data[n][:,:,r])

                # set up labels
                label[0] = "%s, pc %d" % (label_save, n)
                self.set_title(label[0], label[1:3])
                label[4] = "fit [%d, %d]" % (fi[0], fi[1])

                # plot
                self.plot_data_with_fit(X, corr.data[0,:,n], ddata,
                        fitfunc.fitfunc, mpar, label[3:], logscale=False,
                        plotrange=[1,23], addpars=add)
                self.save()

        label[0] = label_save

    def _genplot_comb(self, corr, fitresult, fitfunc, label, oldfit, add=None,
            oldfitpar=None, debug=0):
        """Plot the data of a Correlators object and a FitResult object
        together.

        Parameters
        ----------
        corr : Correlators
            The correlation function data.
        fitresult : FitResult
            The fit data.
        fitfunc : LatticeFit
            The fit function.
        label : list of strs
            The title of the plot, the x- and y-axis titles, and the data label.
        oldfit : None or FitResult, optional
            Reuse the fit results of an old fit for the new fit.
        add : ndarray, optional
            Additional arguments to the fit function. This is stacked along
        oldfitpar : None, int or sequence of int, optional
            Which parameter of the old fit to use, if there is more than one.
                the third dimenstion to the oldfit data.
        debug : int, optional
            The amount of info printed.
        """
        if len(label) < 4:
            raise RuntimeError("not enough labels")
        if len(label) < 5:
            label.append("")
        if corr.matrix:
            raise RuntimeError("Cannot plot correlation function matrix")
        # get needed data
        ncorrs = fitresult.corr_num
        X = np.linspace(0., float(corr.shape[1]), corr.shape[1], endpoint=False)
        label_save = label[0]
        T = corr.shape[1]
        franges = fitresult.fit_ranges
        fshape = fitresult.fit_ranges_shape

        # iterate over correlation functions
        ncorriter = [[x for x in range(n)] for n in ncorrs]
        for item in itertools.product(*ncorriter):
            if debug > 1:
                print("fitting correlators %s" % str(item))
            n = item[-1]
            mdata, ddata = compute_error(corr.data[:,:,n])
            # create the iterator over the fit ranges
            tmp = [fshape[i][x] for i,x in enumerate(item)]
            rangesiter = [[x for x in range(m)] for m in tmp]
            # iterate over the fit ranges
            for ritem in itertools.product(*rangesiter):
                if debug > 1:
                    print("fitting fit ranges %s" % str(ritem))
                r = ritem[-1]
                # get fit interval
                fi = franges[n][r]
                _par = fitresult.get_data(item + ritem)
                mpar, dpar = compute_error(_par)

                # set up labels
                label[0] = "%s, pc %d (%s)" % (label_save, n, str(item[:-1]))
                self.set_title(label[0], label[1:3])
                label[4] = "fit [%d, %d]" % (fi[0], fi[1])

                # get old data
                add_data = oldfit.get_data(item[:-1] + ritem[:-1]) 
                # get only the wanted parameter if oldfitpar is given
                if oldfitpar is not None:
                    add_data = add_data[:,oldfitpar]
                # if there is additional stuff needed for the fit
                # function add it to the old data
                if add is not None:
                    # get the shape right, atleast_2d adds the dimension
                    # in front, we need it in the end
                    if add.ndim == 1:
                        add.shape = (-1, 1)
                    if add_data.ndim == 1:
                        add_data.shape = (-1, 1)
                    add_data = np.hstack((add_data, add))

                # plot
                self.plot_data_with_fit(X, corr.data[0,:,n], ddata,
                        fitfunc.fitfunc, mpar, label[3:], logscale=False,
                        plotrange=[1,T], addpars=add_data, fitrange=fi)
                self.save()

    def plot(self, corr, fitresult, fitfunc, label, oldfit=None, add=None,
            oldfitpar=None, debug=0):
        """Plot the data of a Correlators object and a FitResult object
        together.

        Parameters
        ----------
        corr : Correlators
            The correlation function data.
        fitresult : FitResult
            The fit data.
        fitfunc : LatticeFit
            The fit function.
        label : list of strs
            The title of the plot, the x- and y-axis titles, and the data label.
        oldfit : None or FitResult, optional
            Reuse the fit results of an old fit for the new fit.
        add : ndarray, optional
            Additional arguments to the fit function. This is stacked along
        oldfitpar : None, int or sequence of int, optional
            Which parameter of the old fit to use, if there is more than one.
                the third dimenstion to the oldfit data.
        debug : int, optional
            The amount of info printed.
        """
        if oldfit is None:
            self._genplot_single(corr, fitresult, fitfunc, label, add=add,
                    debug=debug)
        else:
            self._genplot_comb(corr, fitresult, fitfunc, label, oldfit, add,
                    oldfitpar, debug)

if __name__ == "__main__":
    pass
