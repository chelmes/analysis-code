#!/hadron/knippsch/Enthought/Canopy_64bit/User/bin/python
##!/usr/bin/python
################################################################################
#
# Author: Christopher Helmes (helmes@hiskp.uni-bonn.de)
# Date:   Februar 2016
#
# Copyright (C) 2016 Christopher Helmes
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
# Function: Fits of interpolated a_KK * m_K for different strange quark
# masses amu_s 
#
# For informations on input parameters see the description of the function.
#
################################################################################

# system imports
import sys
from scipy import stats
from scipy import interpolate as ip
import numpy as np
from numpy.polynomial import polynomial as P
import math
import matplotlib
matplotlib.use('Agg') # has to be imported before the next lines
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_pdf import PdfPages

# Christian's packages
import analysis2 as ana

def lo_chipt(p,x):
  """
  Chiral perturbation formula for mk_akk in dependence of M_pi at leading order
  
  Parameters:
  ----------
  p : array
      Fit parameters (p[0]: B_0*m_s, p[1]: C/(f^2*B_0), p[2]: f^2, p[3]: C_1^2
      p[4]: general parameter (should equal -1/(8*pi)))
  x : scalar
      The value of the pion mass in GeV
  renorm : Renormalization scale for the chiral log in (GeV)^2,
  """
  return p[0]+p[1]*x

def err_phys_pt(pardata,x,func):
  _y = []
  # evaluate all parameters at one point
  if pardata.shape > 2:
    for i in range(pardata.shape[0]):
      for j in range(pardata.shape[-1]):
        tmp_par = pardata[i,:,j]
        _y.append(func(tmp_par,x))
  else:
    raise ValueError("Parameters do not have the right shape")
  y=np.asarray(_y)
  return ana.compute_error(y)

#def lo_chipt(p,x):
#  """
#  Chiral perturbation formula for mk_akk in dependence of M_pi at leading order
#  
#  Parameters:
#  ----------
#  p : array
#      Fit parameters (p[0]: B_0*m_s, p[1]: C/(f^2*B_0), p[2]: f^2, p[3]: C_1^2
#      p[4]: general parameter (should equal -1/(8*pi)))
#  x : scalar
#      The value of the pion mass in GeV
#  renorm : Renormalization scale for the chiral log in (GeV)^2,
#  """
#  renorm=0.26
#  a = x**2+p[0]
#  b = p[3]*(1.+p[1]/2.*x**2-3./(64.*np.pi**2*p[2]*x**2*np.log(x**2/renorm)))
#  return p[4]*a/b**2

def read_extern(filename):
  """ Read external data with identifiers into a dicitonary
  ATM the tags are written in the first column and the data in the second and
  third.
  TODO: Rewrite that to be more dynamic
  """
  tags = np.loadtxt(filename,dtype='str', usecols=(0,))
  values = np.loadtxt(filename, usecols=(1,2))
  # build a dicitonary from the arrays
  data_dict = {}
  for i,a in enumerate(tags):
      data_dict[a] = values[i]
  return data_dict

def main():
# Parse the input
  if len(sys.argv) < 2:
      ens = ana.LatticeEnsemble.parse("A40.24.ini")
  else:
      ens = ana.LatticeEnsemble.parse(sys.argv[1])

  # get data from input file
  lat = ens.name()
  latA = ens.get_data("namea")
  latB = ens.get_data("nameb")
  latD = ens.get_data("named")
  strangeA = ens.get_data("strangea")
  strangeB = ens.get_data("strangeb")
  strangeD = ens.get_data("stranged")
  AB = latA+latB
  print(AB)
  #quark = ens.get_data("quark")
  datadir = ens.get_data("datadir") 
  plotdir = ens.get_data("plotdir") 
  resdir = ens.get_data("resultdir") 
  nboot = ens.get_data("nboot")
  
  #readchipt = True 
  readchipt = False 
  xcut = False

  # Firstly, read in all interpolated data into one array for which the
  # fits are conducted and append them to an array
  fk_unit = read_extern('./plots2/data/fk_unitary.dat')
  mpi_ext = read_extern('./plots2/data/mpi.dat')
  print(mpi_ext)
  # Initialize a result array for the Ydata
  #nb_ens=len(latA)+len(latB)
  nb_ens=len(latA)+len(latB)+len(latD)
  # arrays for x and y data
  mk_akk = np.zeros((nb_ens,nboot))
  res_ma0 = np.zeros((nb_ens,4))
  mk_fk = np.zeros_like((mk_akk))
  #mpi = np.zeros_like((mk_akk))
  mpi = np.zeros((nb_ens))
  for j,a in enumerate(AB):
      y_obs = ana.FitResult.read("%s%s/match_mk_akk_%s.npz" % (datadir, a, a))
      y_obs.calc_error()
      print y_obs.data[0].shape
      data_shape=y_obs.data[0].shape
      y_obs.data[0]=y_obs.data[0].reshape((data_shape[0],1,data_shape[-1]))
  # Each array is the weighted median over the fit ranges
      res, res_std, res_sys, data_weight = ana.sys_error(y_obs.data,y_obs.pval)
      mk_akk[j] = res[0]
      res_ma0[j] = y_obs.data_for_plot()

      x_obs = ana.FitResult.read("%s%s/match_k_%s.npz" % (datadir, a, a))
      x_obs.calc_error()
      data_shape=x_obs.data[0].shape
      x_obs.data[0]=x_obs.data[0].reshape((data_shape[0],1,data_shape[-1]))
  # Each array is the weighted median over the fit ranges
      res, res_std, res_sys, data_weight = ana.sys_error(x_obs.data,x_obs.pval)
      #fk_sq = ana.draw_gauss_distributed(fk_unit[a][0],fk_unit[a][1],(1,nboot))**2
      #mpi_dist = ana.draw_gauss_distributed(mpi_ext[a][0],mpi_ext[a][1],(nboot,))
      # 0th entry is original data
      #mpi_dist[0] = mpi_ext[a][0]
      #print(mpi_dist.shape)
      # For tree level chipt the square is needed
      #mk_fk[j] = np.divide(res[0],fk_sq)
      #mpi[j] = ana.r0_mass(mpi_dist,a[0])**2
      mpi[j] = ana.r0_mass(mpi_ext[a][0],a[0])**2
      print(mpi[j],a)

  ens_AB=len(latA)+len(latB)
  for j,a in enumerate(latD):
      y_obs = ana.FitResult.read("%s%s/%s/mk_akk_%s.npz" % (datadir, a, strangeD[j], a))
      y_obs.calc_error()
      print y_obs.data[0].shape
      data_shape=y_obs.data[0].shape
      #y_obs.data[0]=y_obs.data[0].reshape((data_shape[0],1,data_shape[-1]))
      y_obs.pval[0] =y_obs.pval[0].reshape((nboot,y_obs.pval[0].shape[-1]))
  # Each array is the weighted median over the fit ranges
      res, res_std, res_sys, data_weight = ana.sys_error(y_obs.data,y_obs.pval)
      mk_akk[ens_AB+j] = res[0]
      res_ma0[ens_AB+j] = y_obs.data_for_plot()
  
      x_obs = ana.FitResult.read("%s%s/%s/fit_k_%s.npz" % (datadir, a, strangeD[j], a))
      x_obs.calc_error(1)
      data_shape=x_obs.data[0].shape
  # Each array is the weighted median over the fit ranges
      x_obs.pval[0] =x_obs.pval[0].reshape((nboot,x_obs.pval[0].shape[-1]))
      res, res_std, res_sys, data_weight = ana.sys_error(x_obs.data,x_obs.pval,par=1)
      #fk = ana.draw_gauss_distributed(fk_unit[a][0],fk_unit[a][1],(1,nboot))
      #mpi_dist = ana.draw_gauss_distributed(mpi_ext[a][0],mpi_ext[a][1],(nboot,))
      # 0th entry is original data
      #mpi_dist[0] = mpi_ext[a][0]
      # For tree level chipt the square is needed
      #mk_fk[ens_AB+j] = np.divide(res[0],fk)**2
      #mpi[ens_AB+j] = ana.r0_mass(mpi_dist,a[0])**2
      mpi[ens_AB+j] = ana.r0_mass(mpi_ext[a][0],a[0])**2
      print(mpi[ens_AB+j],a)
  # Secondly, fit a chiral function to the data
  #define a lambda fit function

  if readchipt:
      if xcut:
          chiral_extra=ana.FitResult.read(resdir+"chiptfit_orig_mpi_xcut_%d.npz" % xcut)
      else:
          chiral_extra=ana.FitResult.read(resdir+'chiptfit_orig_mpi.npz')
  else:
      if xcut:
          chipt = ana.LatticeFit(lo_chipt,dt_i=1, dt_f=1)
          p=[1.,1.]
          chiral_extra = chipt.chiral_fit(mpi,mk_akk,corrid="MA-ChiPT",start=p,xcut=xcut)
          chiral_extra.save(resdir+"chiptfit_orig_mpi_xcut_%d.npz" % xcut)
      else:
          chipt = ana.LatticeFit(lo_chipt,dt_i=1, dt_f=1)
          p=[1.,1.]
          mpi = mpi.reshape((nb_ens,1))
          print(mpi.shape)
          print(mk_akk.shape)
          chiral_extra = chipt.chiral_fit(mpi,mk_akk,corrid="MA-ChiPT",start=p)
          chiral_extra.save(resdir+'chiptfit_orig_mpi.npz')
  chiral_extra.print_data()
  chiral_extra.print_data(par=1)
  print(chiral_extra.data[0].shape)
  print("m a0 has shape:")
  print(mk_akk.shape)
  #res_ma0 = np.asarray([ana.compute_error(i,mean=i[0]) for i in mk_akk],dtype=float).reshape((nb_ens,2))
  res_mpi = np.asarray([ana.compute_error(i,mean=i[0]) for i in mpi],dtype=float).reshape((nb_ens,2))
  # generate fitfunction points and physical point
  #error for physical point
  phys_pt_x = 0.1124
  mk_a0_fin = err_phys_pt(chiral_extra.data[0],phys_pt_x,lo_chipt)
  if xcut:
      b=res_mpi[:,0] < xcut
      ndof = res_mpi[b].shape[0]
  else:
      ndof = nb_ens-chiral_extra.data[0].shape[1]
  print("chi_sq/ndof = %f" % (chiral_extra.chi2[0][0,0]/ndof))
  print("M_Ka_0 at physical point is: %e +/- %e" % (mk_a0_fin[0], mk_a0_fin[1]))
  x = np.linspace(0,np.amax(res_mpi),1000)
  y = np.asarray([lo_chipt(chiral_extra.data[0][0,:,0],_x) for _x in x])
  ## Lastly, plot the fitted function and the data
  ## Open pdf
  if xcut:
      pfit = PdfPages("./plots2/pdf/LOChiPT_matchD_xcut_%d.pdf" % xcut)
  else:
      pfit = PdfPages("./plots2/pdf/LOChiPT_matchD_new.pdf")

  # plot systematic errors on top
  args = chiral_extra.data[0]
  ana.plot_function(lo_chipt,x,args,label=r'LO-$\chi$-PT',ploterror=True)
  plt.errorbar(res_mpi[0:6,0],res_ma0[0:6,0],
              yerr=[res_ma0[0:6,1]+res_ma0[0:6,2],
               res_ma0[0:6,1]+res_ma0[0:6,3]],
               fmt='s', color='red')
  plt.errorbar(res_mpi[6:10,0],res_ma0[6:10,0],
              yerr=[res_ma0[6:10,1]+res_ma0[6:10,2],
               res_ma0[6:10,1]+res_ma0[6:10,3]],
               fmt='^', color='blue')
  plt.errorbar(res_mpi[10,0],res_ma0[10,0],
              yerr =[[res_ma0[10,1]+res_ma0[10,2]],
               [res_ma0[10,1]+res_ma0[10,3]]],
               fmt='o', color='green')
  plt.errorbar(res_mpi[0:6,0],res_ma0[0:6,0],res_ma0[0:6,1],
               fmt='s', color='red', label='A Ensembles')
  plt.errorbar(res_mpi[6:10,0],res_ma0[6:10,0],res_ma0[6:10,1],
               fmt='^', color='blue', label='B Ensembles')
  plt.errorbar(res_mpi[10,0],res_ma0[10,0],res_ma0[10,1],
               fmt='o', color='green', label='D Ensembles')
  #plt.plot(x,y,color='black',label=r'LO $\chi$-PT')
  if xcut:
    y = lo_chipt(chiral_extra.data[0][0,:,0], xcut)
    plt.vlines(xcut, 0.95*y, 1.05*y, colors="k", label="")
    plt.hlines(0.95*y, xcut*0.98, xcut, colors="k", label="")
    plt.hlines(1.05*y, xcut*0.98, xcut, colors="k", label="")
  #plt.errorbar(phys_pt_x,mk_a0_fin[0],mk_a0_fin[1], fmt='d', color='darkorange', label='Physical Point')
  plt.errorbar(phys_pt_x,mk_a0_fin[0], fmt='d', color='darkorange', label='Physical Point')
  plt.grid(False)
  plt.legend(loc='best',numpoints=1)
  plt.ylim(-0.45,-0.25)
  plt.ylabel(r'$M_Ka_0^{I=1}$')
  plt.xlabel(r'$(r_0M_{\pi})^2$')
  pfit.savefig()
  pfit.close()
  


# make this script importable, according to the Google Python Style Guide
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard Interrupt")

  #plt.errorbar(res_mpi[0:6,0],res_ma0[0:6,0],res_ma0[0:6,1],res_mpi[0:6,1],
  #             fmt='s', color='red', label='A Ensembles')
  #plt.errorbar(res_mpi[6:9,0],res_ma0[6:9,0],res_ma0[6:9,1],res_mpi[6:9,1],
  #             fmt='^', color='blue', label='B Ensembles')
  #plt.errorbar(res_mpi[9,0],res_ma0[9,0],res_ma0[9,1],res_mpi[9,1],
  #             fmt='o', color='green', label='D Ensembles')
        
  ## Lastly, plot the fitted function and the data
  ## Open pdf
  #print(res_mpi[0:6,0]**2,res_ma0[0:6,0],res_ma0[0:6,1],res_mk_fk[0:6,1])
  #pfit = PdfPages('./plots2/pdf/LOChiPT_matchD.pdf')
  #plt.errorbar(res_mk_fk[0:6,0],res_ma0[0:6,0],res_ma0[0:6,1],res_mk_fk[0:6,1],
  #             fmt='s', color='red', label='A Ensembles')
  #plt.errorbar(res_mk_fk[6:9,0],res_ma0[6:9,0],res_ma0[6:9,1],res_mk_fk[6:9,1],
  #             fmt='^', color='blue', label='B Ensembles')
  ##plt.errorbar(res_mk_fk[9,0],res_ma0[9,0],res_ma0[9,1],res_mk_fk[9,1],
  ##             fmt='o', color='green', label='D Ensembles')
  #plt.plot(x,y,color='black',label=r'LO $\Chi$-PT')
  #plt.grid(False)
  #plt.ylabel(r'$M_Ka_0^{I=1}$')
  #plt.xlabel(r'$M_K/f_K$')
  #pfit.savefig()
  #pfit.close()
