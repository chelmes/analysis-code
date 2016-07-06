import numpy as np
import matplotlib
matplotlib.use('Agg') # has to be imported before the next lines
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_pdf import PdfPages
matplotlib.rcParams['font.size'] = 14
matplotlib.rcParams['axes.labelsize'] = 'large'

import chiral_utils as chut
from fit import FitResult
from statistics import compute_error
from plot_functions import plot_function

"""A class used for chiral analyses of matched results, does fitting and
plotting as well
"""

class ChirAna(object):
  """Class to conduct a chiral analysis in mu_l and mu_s for different
  observables

  The observables are, in the most general case, lists of ndarrays, reflecting the
  degrees of freedom in lattice spacing, mu_l, mu_s, fitting dimensions and bootstrapsamples.
  Thus the shape of classobject is a tuple with 5 entries, the 0th entry is the
  length of the 1st entry, which is a tuple itself. 
  an example of a shape tuple is (3,(5,4,3),3,2,1500)
  The dependent observables usually have
  the same layout
  In addition it is possible to fit the data to a given function
  """
  def __init__(self,proc_id=None,match=False,correlated=True,combined=False):
    """ Initialize Chiral Analysis object

    Parameters
    ----------
    proc_id : String identifying the analysis
    match : Boolean to determine if the data is matched in amu_s
    correlated : Boolean if fit is Correlated
    combined : Boolean to decide if combined fit is done
    
    Datatypes
    ---------
    fitres : A FitResult or a list of FitResults
    """
    self.y_shape = None
    self.x_shape = None
    self.y_data = None
    self.x_data = None
    # Parameters of extrapolation
    self.fitres = None
    # the physical point in the analysis, x and y-value with errors
    self.phys_point_fitres = None
    self.phys_point = None
    self.proc_id = proc_id
    self.match = match
    self.combined = combined
    self.correlated = correlated
    # Result of a matching procedure
    self.amu_matched_to = None

  def create_empty(self, lyt_x, lyt_y, match=None):
    """Initialize a chiral analysis with some start parameters
    
    At the moment the first index is used to label the lattice spacing, the
    second index is a tuple encoding the number of lattices per spacing. the
    third index counts the number of matched results and the last index is the
    number of bootstrapsamples.
    Parameters
    ----------
    lyt_y : tuple, shape of the y data
    lyt_x : tuple, shape of the x data
    match : boolean to state if matched data is to be analysed, default is False
    """
    #print(len(lyt_x),len(lyt_y))
    # save layout for later use
    self.y_shape = lyt_y
    self.x_shape = lyt_x
    
      
    if self.match is True:
      self.amu_matched_to = []
      for a in range(lyt_y[0]):
        if len(lyt_y) == 5:
          tp_mu = (lyt_y[1][a],lyt_y[2],lyt_y[3],lyt_y[4])
        elif len(lyt_y) == 4:
          tp_mu = (lyt_y[1][a],lyt_y[2],lyt_y[3])
        else:
          tp_mu = (lyt_y[1][a],lyt_y[2])
        self.amu_matched_to.append(np.zeros(tp_mu))

    self.y_data = []
    for a in range(lyt_y[0]):
      if len(lyt_y) == 5:
        tp_y = (lyt_y[1][a],lyt_y[2],lyt_y[3],lyt_y[4])
      elif len(lyt_y) == 4:
        tp_y = (lyt_y[1][a],lyt_y[2],lyt_y[3])
      else:
        tp_y = (lyt_y[1][a],lyt_y[2])
      self.y_data.append(np.zeros(tp_y))

    self.x_data = []
    for a in range(lyt_x[0]):
      if len(lyt_x) == 5:
        tp_x = (lyt_x[1][a],lyt_x[2],lyt_x[3],lyt_x[4])
      elif len(lyt_x) == 4:
        tp_x = (lyt_x[1][a],lyt_x[2],lyt_x[3])
      else:
        tp_x = (lyt_x[1][a],lyt_x[2])
      self.x_data.append(np.zeros(tp_x))
      print("x_data tuple for allocation")
      print(tp_x)
    self.phys_point = np.zeros((2,2))
    debug=True
    if debug is True:
      print("Created empty Chiral Analysis object with shapes:")
      print("x-data: length %d" % len(self.x_data))
      for i in self.x_data:
        print(i.shape)

  #def save()
  #
  #@classmethod
  #def read(cls,):

  def extend_data(self,obs=['None',],dim='x'):
    """Extend data in the givene dimension for different values

    The data values in the given dimension are extended with ensemble specific
    observables, like a/r_0. Thus the dimensionality of the data is raised in
    order to enable global fitting.

    Parameters
    ----------
    obs : list of strings, observabls to add to data
    dim : string, x or ydata
    """
    # using data layouts create data for extra dimension
    if dim is 'x':
      _lyt = self.x_shape
      self.x_shape = _lyt+((len(obs)+1),)
    elif dim is 'y':
      _lyt = self.y_shape
      self.y_shape = _lyt+((len(obs)+1),)
    else:
      raise ValueError
      print("Type not known, choose between 'x' or 'y'")
    # extension is the larger array
    extension = []
    for a in range(_lyt[0]):
      if len(_lyt) == 4:
        _tp = (_lyt[1][a],_lyt[2],_lyt[3],len(obs)+1)
      else:
        _tp = (_lyt[1][a],_lyt[2],len(obs)+1)
      extension.append(np.zeros(_tp))
    # copy data over from self
    full_lat_space = ['A','B','D']
    for i,a in enumerate(extension):
      if dim is 'x':
        a[...,0] = self.x_data[i]
        if obs[0] is 'a':
          # initialise bootstrapsampled r0-values
          r0 = chut.prepare_r0(full_lat_space[i],_lyt[2])
          r0_inv_sq = np.square(1./r0)

          # get array into right shape
          if self.match is False:
            r0_inv_sq = np.tile(r0_inv_sq,_lyt[3]).reshape((_lyt[3],_lyt[2]))
            #print("intermeidate shape of a/r0")
            #print(r0_inv_sq.shape)
          r0_ins = np.zeros_like(a[...,0])
          for i in r0_ins:
            i = r0_inv_sq
          #print("shape for insertion")
          #print(r0_ins.shape)
          a[...,1] = r0_ins
      # update original data
      else:
        raise RuntimeError
        print("global fit only for multiple x dimenisons")
    self.x_data = a
    print("control squared a/r0 values:")
    for i in extension:
      print(i[:,:,0,0])
    return extension

  def add_data(self,data,idx,dim=None,op=False):
    """Add x- or y-data at aspecific index

    Parameters
    ----------
    data : ndarray, the data to add, usually bootstrapsamples
    idx : tuple, index as in creation: lattice spacing, ensemble index, strange
          quark mass, fit dimension
    dim : string, is it x- or y-data?
    op : string, should existent data at index and dimension be operated
           with data to add?
    """
    if dim =='x':
      #print("xdata to add has shape")
      #print(data.shape)
      #print("xdata to add to has shape")
      #print(self.x_data[idx[0]].shape)
      if op == 'mult':
        self.x_data[idx[0]][idx[1],idx[2],idx[3]] *= data
      # divide existent x_data by data
      elif op == 'div':
        self.x_data[idx[0]][idx[1],idx[2],idx[3]] /= data
      elif op == 'min':
        self.x_data[idx[0]][idx[1],idx[2],idx[3]] -= data
      else:
        self.x_data[idx[0]][idx[1],idx[2],idx[3]] = data
        #self.x_data[idx[0]][idx[1],:,idx[2]] = data
      #print(self.x_data[idx[0]][idx[1],idx[2],idx[3]][0])
    if dim =='y':
      if op == 'mult':
        self.y_data[idx[0]][idx[1],idx[2],idx[3]] *= data
      elif op == 'div':
        self.y_data[idx[0]][idx[1],idx[2],idx[3]] /= data
      elif op == 'min':
        self.y_data[idx[0]][idx[1],idx[2],idx[3]] -= data
      else:
        self.y_data[idx[0]][idx[1],idx[2],idx[3]] = data
      #print(self.y_data[idx[0]][idx[1],idx[2],idx[3]][0])
    if dim =='mu':
      if op == 'mult':
        self.amu_matched_to[idx[0]][idx[1],idx[2],idx[3]] *= data
      elif op == 'div':
        self.amu_matched_to[idx[0]][idx[1],idx[2],idx[3]] /= data
      elif op == 'min':
        self.amu_matched_to[idx[0]][idx[1],idx[2],idx[3]] -= data
      else:
        self.amu_matched_to[idx[0]][idx[1],idx[2],idx[3]] = data

  def add_extern_data(self,filename,idx,ens,dim=None,square=True,read=None,op=False):
    """ This function adds data from an extern textfile to the analysis object
    
    The data is classified by names, the filename is given and the read in and
    prepared data is placed at the index 

    Parameters
    ---------
    filename : string, the filename of the extern data file
    idx : tuple, index where to place prepared data in analysis
    ens : string, identifier for the ensemble
    dim : string, dimension to place the extern data at
    square : bool, should data be squared?
    read : string, identifier for the data read
    op : string, if operation is given the data is convoluted with existing data
        at that index. if no operation is given data gets overwritten
    """
    if read is None:
      plot, data = np.zeros((self.x_data[0].shape[-1]))

    if read is 'r0_inv':
      _plot,_data = chut.prepare_r0(ens,self.x_data[0].shape[-1])
      plot=1./np.square(_plot)
      data=1./np.square(_data)

    if read is 'r0':
      _plot,_data = chut.prepare_r0(ens,self.x_data[0].shape[-1])
      if square:
        plot=np.square(_plot)
        data=np.square(_data)
      else:
        plot=_plot
        data=_data

    if read is 'a':
      _plot,_data = chut.prepare_a(ens,self.x_data[0].shape[-1])
      if square:
        plot=np.square(_plot)
        data=np.square(_data)
      else:
        plot=_plot
        data=_data

    if read is 'mpi':
      #print("indexto insert extern data:")
      #print(dim,idx)
      ext_help = chut.read_extern(filename,(1,2))
      # take any y data dimension, since bootstrap samplesize shold not differ
      # build r0M_pi
      plot,data = chut.prepare_mpi(ext_help,ens,self.x_data[0].shape[-1],square=square)

    if read is 'mpiL':
      ext_help = chut.read_extern(filename,(1,2))
      plot,data = chut.prepare_mpi(ext_help,ens,self.x_data[0].shape[-1],square=square,r0=False)

    if read is 'fk_unit':
      ext_help = chut.read_extern(filename,(1,2))
      plot,data = chut.prepare_fk(ext_help,ens,self.x_data[0].shape[-1])

    if read is 'mk_unit':
      ext_help = chut.read_extern(filename,(1,2))
      # prepare_fk also does the right for m_k
      # TODO: unify this at some point
      plot,data = chut.prepare_fk(ext_help,ens,self.x_data[0].shape[-1])
    print("extern data added:")
    print("%s: %f " %(read, data[0]))
    self.add_data(data,idx,dim=dim,op=op)

  def get_data(self,idx,dim):
    """return data at agiven index tuple before any reduction"""
    if dim == 'y':
      _data = self.y_data[idx[0]][idx[1],idx[2],idx[3]]
    elif dim == 'x':
      _data = self.x_data[idx[0]][idx[1],idx[2],idx[3]]
    else:
      print("datadimension not known")
    return _data

  def get_data_fit(self,dof,index,v='y'):
    """ Collect the data for the fit from class instance

    Get x- or y-data and choose the data at a given index depending on the fixed
    degree of freedom. Data is reshaped in the end to have only 2 dimensions
    from which the last one is the number of bootstrapsamples
    Parameters
    ----------
    dof : char, the dimension of the data to keep fixed
    index : int, the index of the fixed dimension
    v : char, if it is x or y data to be taken into account
    """ 
    if v == 'y':
      _data = self.y_data
    if v == 'x':
      _data = self.x_data
    # get all data for a distinct lattice spacing
    if dof == 'a':
      tp = index
      data = _data[tp]
    # get all data for a fixed mu_s
    elif dof == 'mu_s':
      data = np.concatenate((_data[0][:,index],_data[1][:,index],_data[2][:,index]))
      _tmp_lyt = data.shape
      data=data.reshape((_tmp_lyt[0]*_tmp_lyt[1],_tmp_lyt[2]))
      #print("chose data")
      #print(data.shape)
    elif dof == 'nboot':
      tp = (slice(None),slice(None),slice(None),index)
      data = _data[tp]
    else:
      raise ValueError("unknown data dimension.")
    return data

  def get_mu_plot(self,dim=0,debug=0):
    """ Returns the data suited for plotting and printing a summary

    The data dimenisons are reduced such that for each datapoint there is an
    array of 4 values.

    Parameters
    ----------
    """
    # Get data for fit (several fit dimensions for x, only one for y)
    dummy,dummy,_mu_data = self.reduction(x_shape_new = (self.x_shape[3],self.x_shape[4]),
                                    y_shape_new = (self.y_shape[3],self.y_shape[4],))
    # initialize plot data
    _mu_plot = np.zeros((_mu_data.shape[0],4))
    # calculate errors and fill
    # Loop over ensembles (eventually including quark mass)
    for e in range(_mu_plot.shape[0]):
      if _mu_data.shape[1] == 2:
        _mu_plot[e][0:2] = compute_error(_mu_data[e,dim])
      else:
        _mu_plot[e][0:2] = compute_error(_mu_data[e])
    if debug > 0:
      print("_mu_data is:")
      print(_mu_data)
      print("get_mu_plot returns:")
      print(_mu_plot)
    return _mu_plot

  def get_data_plot(self,dim=0,debug=0):
    """ Returns the data suited for plotting and printing a summary

    The data dimenisons are reduced such that for each datapoint there is an
    array of 4 values.

    Parameters
    ----------
    """
    # Get data for fit (several fit dimensions for x, only one for y)
    _x_data, _y_data, _mu_data = self.reduction(x_shape_new = (self.x_shape[3],self.x_shape[4]),
                                    y_shape_new = (self.y_shape[3],self.y_shape[4],))
    # initialize plot data
    _x_plot = np.zeros((_x_data.shape[0],_x_data.shape[1],4))
    _y_plot = np.zeros((_y_data.shape[0],4))
    # calculate errors and fill
    # check shapes of x and y
    if _x_plot.shape[0] != _y_plot.shape[0]:
      print("x and y have wrong shapes")
    # Loop over ensembles (eventually including quark mass)
    for e in range(_x_plot.shape[0]):
      # loop over dimensions of x
      for d in range(_x_plot.shape[1]):
        _x_plot[e,d][0:2] = compute_error(_x_data[e,d])
      
      if _y_data.shape[1] == 2:
        _y_plot[e][0:2] = compute_error(_y_data[e,dim])
      else:
        _y_plot[e][0:2] = compute_error(_y_data[e])
    if debug > 0:
      print("get_data_plot returns:")
      print(_x_plot,_y_plot)
    return _x_plot, _y_plot

  def fit(self,fitfunc,dim,index,start=[1.,],x_phys=None,xcut=False,
          plot=True,plotfunc=None,label=None,datadir=None,read=False,ens=None,debug=0,loc=None):
    """fit a chiral analysis instance to a given fitfunction

    This function uses the data of the ChirAna instance to fit the data to the
    fitfunction. Different degrees of freedom are appliccable, an optional plot
    can be made 

    Parameters
    ----------

    fitfunc : callable, the fitfunction to use for fitting and plotting
    dim : string, which dof to fix (a,mu_l,mu_s,nsamp)
    index : int, index to fix dim
    x_phys : x-value for physical point
    xcut: float, optional cut on x-axis
    plot: bool, should the fitresults be plotted?
    label: tuple, x-,y-label for plot
    datadir : string, directory for saving data
    read : bool, read in previous fits
    """

    # Choose the fit data the dimensions of the data are: (a,mu_l,mu_s,nboot)
    # with lattice spacing a, light and strange quark masses mu_l and mu_s and
    # bootstrapsaFalses
    if dim is None:
      # Get data for fit (several fit dimensions for x, only one for y)
      x_data, y_data, mu_data = self.reduction(x_shape_new = (self.x_shape[3],self.x_shape[4]),
                                    y_shape_new = (self.y_shape[4],))

      #print("data used for fit")
      #print("x:shape,data")
      #print(x_data.shape)
      #print(x_data[...,0])
      #print("y:shape,data")
      #print(y_data.shape)
      #print(y_data[...,0])
      if read:
        if xcut:
          self.fitres = FitResult.read(datadir+self.proc_id+'_xcut_%d.npz'%xcut)
        else:
          self.fitres = FitResult.read(datadir+self.proc_id+'.npz')
      else:
        if self.combined is True:
          self.fitres = chut.chiral_fit(x_data,y_data,fitfunc,corrid=self.proc_id,
                                    start=start,xcut=xcut,correlated=self.correlated,
                                    mute=chut.mutilate_cov,debug=debug)
        else:
          self.fitres = chut.chiral_fit(x_data,y_data,fitfunc,corrid=self.proc_id,
                                    start=start,xcut=xcut,correlated=self.correlated,
                                    debug=debug)
      if xcut:
        self.fitres.save(datadir+self.proc_id+'_xcut_%d.npz'%xcut)
      else:
        self.fitres.save(datadir+self.proc_id+'.npz')
      args = self.fitres.data[0]
      # save samples of physical point result as fitresult along with p-values

      self.phys_point_fitres = self.fitres.calc_mk_a0_phys(x_phys,fitfunc)
      print ("physical point from fitresult")
      print(self.phys_point_fitres.data[0],self.phys_point_fitres.pval[0])
      self.phys_point_fitres.calc_error()
      self.phys_point_fitres.print_data()
      self.phys_point_fitres.save(datadir+self.proc_id+'phys_pt.npz')

      self.phys_point = np.zeros((2,2))
      self.phys_point[0] = x_phys[0:2]
      self.phys_point[1] = chut.err_phys_pt(args,x_phys,plotfunc)
      print("Calculated physical point to be:")
      print(self.phys_point)
    # if a dimension is given set up a list of fitresults
    else:
      self.fitres = []
      if dim == 'a':
        #for a in range(self.x_shape[0]):
        # At the moment D has only one Ensemble
        for a in range(2):
          _x_lat = self.get_data_fit('a',a,'x')
          _y_lat = self.get_data_fit('a',a,'y')
          x_data = _x_lat.reshape(_x_lat.shape[0]*_x_lat.shape[1],_x_lat.shape[2],_x_lat.shape[3])
          # Usually y data is 1d in 3rd dimension
          y_data = _y_lat.reshape(_y_lat.shape[0]*_y_lat.shape[1]*_y_lat.shape[2],_y_lat.shape[3])
          self.fitres.append(chut.chiral_fit(x_data,y_data,fitfunc,corrid=self.proc_id+'_lat_spc_%d'%a,
                                    start=start,xcut=xcut,debug=debug))
        self.phys_point = np.zeros((len(self.fitres),2,2))
        for a in range(2):
          args = self.fitres[a].data[0]
          self.phys_point[a,0] = x_phys[0:2]
          self.phys_point[a,1] = chut.err_phys_pt(args,x_phys,fitfunc)
          print("Calculated physical point to be:")
          print(self.phys_point)
    if plot is True:
      label=label
      #print(x_data.shape)
      #print(y_data.shape)
      #if self.glob is True:
      #  self.plot_plain(x_data,y_data,fitfunc,xcut=xcut,ens=ens)
      #  self.plot_glob_func(x_data,y_data,fitfunc,xcut=xcut,ens=ens)
      #else:
      self.plot(x_data,y_data,label,xcut=xcut,ens=ens,plotfunc=plotfunc,
                savedir=datadir,loc=loc)
      # In a combined fit also plot the second plot
      if self.combined:
        label[2]= r'$M_Ka_0$ matched to $m_{s,ren}$'
        self.plot(x_data,y_data,label,xcut=xcut,ens=ens,plotfunc=plotfunc,
                  savedir=datadir,loc=loc,suffix="2",dim=1)

  def print_summary(self,dim,index,lat_space,ens_dict,
                    mu_s_dict=None,xcut=2,head=None):
    """This function should print a summary of the whole chiral analysis,
    preferably in latex format
    """
    # Load data
    _x_summ, _y_summ = self.get_data_plot()
    print("summary data:")
    print(_x_summ.shape)
    if self.match is True:
      _mu_summ = self.get_mu_plot(dim=0,debug=2)
    if head is None:
      header=['Ens','$a\mu_s$','$(r_0M_{\pi})^2$','$(a/r_0)^2$', '$M_Ka_0$']
    else:
      header=head
    chut.print_table_header(header)

    print('\midrule')
    l = 0
    for i,a in enumerate(lat_space):
      #if i > 0:
      #  l = len(ens_dict[lat_space[i-1]])
      #if i > 1:
      #  l = len(ens_dict[lat_space[i-1]])+ len(ens_dict[lat_space[i-2]])
      #else:
      #  l = 0
      # number of ensembles for each lattice spacing
      if i == 0:
        l = 0
      if i == 1:
        l = len(ens_dict[lat_space[i-1]])
      if i == 2:
        l += len(ens_dict[lat_space[i-1]])
      for j,e in enumerate(ens_dict[a]):
        # format for
        if self.match:
            # this is printing two dimensions
            if hasattr(_mu_summ,"__iter__"):
              chut.print_line_latex(e,_x_summ[l+j],_y_summ[l+j],_mu_summ[l+j])
            else:
              chut.print_line_latex(e,_x_summ[l+j],_y_summ[l+j])
        else:
          for k,s in enumerate(mu_s_dict[a]):
              #chut.print_line_latex(e,_x_summ[i*l*3+j*3+k],_y_summ[i*l*3+j*3+k])
              chut.print_line_latex(e,_x_summ[l*3+j*3+k],_y_summ[l*3+j*3+k])
    # TODO: Automate that
    if hasattr(self.fitres,"__iter__"):
      dof =  _x_summ.shape[0] - self.fitres[0].data[0].shape[1]
      if self.combined:
        dof = 2*_x_summ.shape[0] - self.fitres[0].data[0].shape[1]
      print("%10s & $%.1f$ & $%.4f(%1.0f)$ & $%.2f/%d$ & $%.2e $" %
          (self.proc_id, xcut, self.phys_point[0,1,0], self.phys_point[0,1,1]*1e4,
           self.fitres[0].chi2[0][0], dof, self.fitres[0].pval[0][0]))

      #dof =  _x_summ.shape[0] - self.fitres[1].data[0].shape[1]
      #print("%10s & $%.1f$ & $%.4f(%1.0f)$ & $%.2f/%d$ & $%.2e $" %
      #    (self.proc_id, xcut, self.phys_point[1,1,0], self.phys_point[1,1,1]*1e4,
      #     self.fitres[1].chi2[0][0], dof, self.fitres[1].pval[0][0]))
    else:
      dof = _x_summ.shape[0] - self.fitres.data[0].shape[1]
      if self.combined:
        print(_x_summ.shape[0])
        print(self.fitres[0].data[0].shape[1])
        dof = 2*_x_summ.shape[0] - self.fitres[0].data[0].shape[1]
      print("Phsyical point result:")
      if xcut is None:
        xcut = 2.
      print("%10s & $%.1f$ & $%.4f(%1.0f)$ & $%.2f/%d$ & $%.2e $" %
          (self.proc_id, xcut, self.phys_point[1,0], self.phys_point[1,1]*1e4,
           self.fitres.chi2[0][0], dof, self.fitres.pval[0][0]))

  def reduction(self,x_shape_new=None,y_shape_new=None):
    """Function to reduce the dimensionality of the data to a two dimensional
    ndarray that can be handled by the plot function
    The final layout should concatenate the light and strange quark dependence. 

    The x and y data are cast to an 2d ndarray with same shape (apart from bootstrap
    sa#mples)
    """
    # the outgoing data is 2 dimensional
    # new x-data has shape (ens1*ms+ens2*ms+ens3*ms,fitdim,samples)
    # looping over list place data in array
    if x_shape_new is None:
      tmp_x_shape = (self.x_shape[0],self.x_shape[1]*np.asarray(self.x_shape[2]),self.xshape[3],self.x_shape[-1])
    else:
      tmp_x_shape = (self.x_shape[0],self.x_shape[1]*np.asarray(self.x_shape[2]),x_shape_new[0],x_shape_new[1])
    if y_shape_new is None: 
      #tmp_y_shape = (self.y_shape[0],self.y_shape[1]*np.asarray(self.y_shape[2]),self.y_shape[-1])
      tmp_y_shape = (self.y_shape[0],self.y_shape[1]*np.asarray(self.y_shape[2]),self.y_shape[-1])
    else:
      tmp_y_shape = (self.y_shape[0],self.y_shape[1]*np.asarray(self.y_shape[2]),y_shape_new[0])
    #print("New Shapes:")
    #print(tmp_x_shape)
    #print(tmp_y_shape)
    tmp = ChirAna("reduction",match=self.match)
    tmp.create_empty(tmp_x_shape,tmp_y_shape)
    # Loop over lattice spacing
    for i,d in enumerate(self.x_data):
      if x_shape_new is None:
        try:
          new_shape = (d.shape[0]*d.shape[1],d.shape[2],d.shape[3])
        except:
          new_shape = (d.shape[0]*d.shape[1],d.shape[2])
          pass
      else:
        new_shape = (d.shape[0]*d.shape[1],x_shape_new[0],x_shape_new[1])
      #print("reshape to:")
      #print(new_shape)
      tmp.x_data[i] = d.reshape(new_shape)
      #print(tmp.x_data)
    for i,d in enumerate(self.y_data):
      if d.shape[2] == 1:
        new_shape = (d.shape[0]*d.shape[1],d.shape[-1]) 
      else:
        new_shape = (d.shape[0]*d.shape[1],d.shape[2],d.shape[-1])
      tmp.y_data[i] = d.reshape(new_shape)
    if self.match is True:
      for i,d in enumerate(self.amu_matched_to):
        if d.shape[2] == 1:
          new_shape = (d.shape[0]*d.shape[1],d.shape[-1]) 
        else:
          new_shape = (d.shape[0]*d.shape[1],d.shape[2],d.shape[-1])
        tmp.amu_matched_to[i] = d.reshape(new_shape)
    if self.x_shape[0] == 3: 
      x_data = np.concatenate((tmp.x_data[0],tmp.x_data[1],tmp.x_data[2]))
      #print(x_data)
      y_data = np.concatenate((tmp.y_data[0],tmp.y_data[1],tmp.y_data[2]))
      if self.match is True:
        mu_data = np.concatenate((tmp.amu_matched_to[0],tmp.amu_matched_to[1],tmp.amu_matched_to[2]))
      #print(y_data.shape)
      #print(x_data.shape)
        return x_data, y_data, mu_data
      else:
        return x_data, y_data, None
    else:
      return None,None,None

  def calc_plot_ranges(self):
    """ Return the plot ranges for the different lattice spacings
    """
    if self.match is True:
      _a_range = (0,self.x_shape[1][0]*self.x_shape[2])
      _b_range = (_a_range[1],_a_range[1]+self.x_shape[1][1]*self.x_shape[2])
      _d_range = (_b_range[1],_b_range[1]+self.x_shape[1][2]*self.x_shape[2])

    else:
      _a_range = (0,self.x_shape[1][0]*self.x_shape[2])
      _b_range = (_a_range[1],_a_range[1]+self.x_shape[1][1]*self.x_shape[2])
      _d_range = (_b_range[1],_b_range[1]+self.x_shape[1][2]*self.x_shape[2])
    #print(_a_range)
    #print(_b_range)
    #print(_d_range)

    return _a_range, _b_range, _d_range

  def plot_plain(self,x_data,y_data,label,ens,savedir=None,xcut=None):
    x_plot,y_plot = self.get_data_plot()
    pfit = PdfPages("./plots2/pdf/%s.pdf" % self.proc_id)

    #print("\nData used for plot: ")
    #print("x-data:")
    #print(x_plot)
    #print("y-data")
    #print(y_plot)

    if savedir is not None:
      path = savedir
    else:
      path = "./plots2/pdf"
    if xcut:
        pfit = PdfPages(path+"/%s_xcut_%d.pdf" % (self.proc_id,xcut))
    else:
        pfit = PdfPages(path+"/%s.pdf" % self.proc_id)

    #calc xid's
    a_range, b_range, d_range = self.calc_plot_ranges()
    chut.plot_ensemble(x_plot[:,0],y_plot,'^vspho','red',ens['A'],xid = a_range)
    chut.plot_ensemble(x_plot[:,0],y_plot,'^vso','blue',ens['B'],xid = b_range)
    chut.plot_ensemble(x_plot[:,0],y_plot,'^','green',ens['D'],xid = d_range)

    plt.grid(False)
    #plt.xlim(0.,0.5)
    plt.legend(loc='best',numpoints=1, ncol=2,fontsize=12)
    plt.ylabel(label[1])
    plt.xlabel(label[0])
    pfit.savefig()
    pfit.close()
    plt.clf()

  def plot(self,x_data,y_data,label,xcut=False,ens=None,plotfunc=None,
           savedir=None,loc=None,suffix=None,dim=0):
    """Plot the chiral analysis data and the fitted function
       for the fitfunction the arguments are retrieved from the analysis object 
    Parameters
    ---------
    x_data : ndarray, The x_data considered in this plot, atm 2d with
             statistical errors is possible
    y_data : nd_array, The y data for the plot and the fit.
    label : a label for the plot
    xcut : should the data be cut to a smaller x-range?
    ens : label for the ensemble
    plotfunc : The function used for plotting 
    """
    x_plot,y_plot = self.get_data_plot(dim=dim)
    print("\nData used for plot: ")
    print("x-data:")
    print(x_plot)
    print("y-data")
    print(y_plot)
    if savedir is not None:
      path = savedir
    else:
      path = "./plots2/pdf"
    if xcut:
      if suffix is not None:
        pfit = PdfPages(path+"/%s_%s_xcut_%d.pdf" % (self.proc_id,suffix,xcut))
      else:
        pfit = PdfPages(path+"/%s_xcut_%d.pdf" % (self.proc_id,xcut))
    else:
      if suffix is not None:
        pfit = PdfPages(path+"/%s_%s.pdf" % (self.proc_id,suffix))
      else:
        pfit = PdfPages(path+"/%s.pdf" % self.proc_id)

    x = np.linspace(0,np.amax(x_plot),1000)
    #print("arguments for plotting are:")
    #print(args)
    a_range, b_range, d_range = self.calc_plot_ranges()
    #print("x-data for function plot:")
    #print(x_plot[a_range[0]:a_range[1],:,0])
    #print(x_plot[b_range[0]:b_range[1]])
    #print(x_plot[d_range[0]:d_range[1]])

    # check if several fits are made:
    if hasattr(self.fitres,"__iter__"):
      # D-Ensembles not taken into account!
      args = []
      for i in range(2):
        args.append(self.fitres[i].data[0])

      plot_function(plotfunc,x_plot[a_range[0]:a_range[1],:,0],
                    args[0][:,:,0],label=r'NLO-fit A',ploterror=True,col='red')
      chut.plot_ensemble(x_plot[:,0],y_plot,'^vspho','red',ens['A'],
                         xid = a_range,match=self.match)

      plot_function(plotfunc,x_plot[b_range[0]:b_range[1],:,0],
                    args[1][:,:,0],label=r'NLO-fit B',ploterror=True,col='blue')
      chut.plot_ensemble(x_plot[:,0],y_plot,'^vso','blue',ens['B'],
                         xid = b_range,match=self.match)

    else:
      # Convention: if dim is 1 take argument 0,3,2 instead of 0,1,2,
      if dim == 0:
        args = self.fitres.data[0]
      if dim == 1:
        arg_shape = self.fitres.data[0].shape
        args = np.column_stack((self.fitres.data[0][:,0],self.fitres.data[0][:,3],
                         self.fitres.data[0][:,2])).reshape(arg_shape[0],3,arg_shape[-1])
      plot_function(plotfunc,x_plot[a_range[0]:a_range[1],:,0],
                    args[:,:,0],label=r'NLO-fit A',ploterror=True,col='red')
      chut.plot_ensemble(x_plot[:,0],y_plot,'^vspho','red',ens['A'],
                         xid = a_range,match=self.match)

      plot_function(plotfunc,x_plot[b_range[0]:b_range[1],:,0],
                    args[:,:,0],label=r'NLO-fit B',ploterror=True,col='blue')
      chut.plot_ensemble(x_plot[:,0],y_plot,'^vso','blue',ens['B'],
                         xid = b_range,match=self.match)
      plot_function(plotfunc,x_plot[d_range[0]:d_range[1],:,0],
                    args[:,:,0],label=r'NLO-fit D',ploterror=True,col='green')
      chut.plot_ensemble(x_plot[:,0],y_plot,'^','green',ens['D'],
                           xid = d_range,match=self.match)

    if xcut:
      y = plotfunc(args[0,:,0], xcut)
      plt.vlines(xcut, 0.95*y, 1.05*y, colors="k", label="")
      plt.hlines(0.95*y, xcut*0.98, xcut, colors="k", label="")
      plt.hlines(1.05*y, xcut*0.98, xcut, colors="k", label="")
    print("Physical point is:")
    try:
      for a in self.phys_point:
        print("%f +/- %f" %(a[1,0],a[1,1]))
      plt.errorbar(self.phys_point[:,0,0],self.phys_point[:,1,0],self.phys_point[:,1,1], fmt='d', color='darkorange', label='Physical Point')
    except:
      print("%f +/- %f" %(self.phys_point[1,0],self.phys_point[1,1]))
      plt.errorbar(self.phys_point[0,0],self.phys_point[1,0],self.phys_point[1,1], fmt='d', color='darkorange', label='Physical Point')
      pass
    plt.grid(False)
    # get x and y range dynamically
    #x_tmp = np.append(x_plot[:,0],np.full_like(x_plot[:,0],self.phys_point[0,0]),axis=1)
    #x_min = np.amin(x_tmp)
    #x_max = np.amax(x_plot[:,0])
    #x_lim = [x_min-0.05*abs(x_min),x_max+0.05*abs(x_max)]
    #y_min = np.amin(y_plot[:,0])
    #y_max = np.amax(y_plot[:,0])
    #y_lim = [y_min-0.1*abs(y_min),y_max+0.1*abs(y_max)]
    ##plt.xlim(x_lim[0],x_lim[1])
    #plt.xlim(0,x_lim[1])
    #plt.ylim(y_lim[0],y_lim[1])
    plt.xlim(0,50)
    plt.ylim(1.15,2.3)
    #plt.vlines(self.phys_point[0,0],y_lim[0],y_lim[1],color="k",label=label[3])
    if loc==None:
      plt.legend(loc='best',numpoints=1,ncol=2,fontsize=12)
    else:
      plt.legend(loc=loc,numpoints=1,ncol=2,fontsize=12)
    plt.title(label[2])
    plt.ylabel(label[1])
    plt.xlabel(label[0])
    pfit.savefig()
    pfit.close()
    plt.clf()
