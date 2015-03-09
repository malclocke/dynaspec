#! /usr/bin/env python

import numpy as np
import pyfits
import matplotlib.pyplot as plt
import argparse
from onedspec import OneDSpec
from scipy.interpolate import griddata
from matplotlib.ticker import ScalarFormatter
from mpl_toolkits.mplot3d import axes3d
from matplotlib import cm

parser = argparse.ArgumentParser(description='Make 2D grayscale image from multiple 1D spectra')
parser.add_argument('master', type=str)
parser.add_argument('file', type=str, nargs='+')
parser.add_argument('--cmap', '-c', type=str, default='gist_stern')
parser.add_argument('--title', '-t', type=str, default='')
parser.add_argument('--alpha', '-a', type=float, default=0.8,
        help='Surface transparency. 0 for transparent, 1 for opaque.')
parser.add_argument('--vmin', type=float)
parser.add_argument('--vmax', type=float)
parser.add_argument('--nocontour', action='store_true',
        help='Hide contour on bottom of plot')
parser.add_argument('--contour-offset', type=float, default=0.9)

args = parser.parse_args()

x = np.array([])
y = np.array([])
z = np.array([])
ticks = []
master = OneDSpec(pyfits.open(args.master))
header = master.hdulist[0].header

length = len(master.data())
wavelengths = master.wavelengths()
start_jd, _ = divmod(header['JD-MID'], 1)
a = np.empty(length)
ticks.append(header['JD-MID'] - start_jd)
a.fill(header['JD-MID'] - start_jd)
x = np.append(x, wavelengths)
y = np.append(y, a)
z = np.append(z, master.data())
xlabel = header['CUNIT1']

for f in args.file:
  print "Processing %s" % (f)
  s = OneDSpec(pyfits.open(f))
  a = np.empty(length)
  ticks.append(s.hdulist[0].header['JD-MID'] - start_jd)
  a.fill(s.hdulist[0].header['JD-MID'] - start_jd)
  x = np.append(x, wavelengths)
  y = np.append(y, a)
  z = np.append(z, s.interpolate_to(master))


# define regular grid spatially covering input data
n = length
xg = np.linspace(x.min(),x.max(),n)
yg = np.linspace(y.min(),y.max(),40)

X,Y = np.meshgrid(xg,yg)

# interpolate Z values on defined grid
Z = griddata(np.vstack((x.flatten(),y.flatten())).T, \
          np.vstack(z.flatten()),(X,Y),method='nearest').reshape(X.shape)
# mask nan values, so they will not appear on plot
Zm = np.ma.masked_where(np.isnan(Z),Z)


fig = plt.figure()
ax = fig.gca(projection='3d')
ax.plot_surface(X, Y, Zm, rstride=3, cstride=10, alpha=args.alpha, cmap=cm.gist_stern)
if not args.nocontour:
    cset = ax.contourf(X, Y, Zm, zdir='z', offset=Zm.min()*args.contour_offset, cmap=cm.gist_stern)
    ax.set_zlim(Zm.min()*args.contour_offset, Zm.max())

ax.set_title(args.title)
ax.set_xlabel('Angstrom')
ax.set_ylabel("JD - %d" % start_jd)
ax.set_zlabel('Intensity')

plt.show()
