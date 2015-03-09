#! /usr/bin/env python

import numpy as np
import pyfits
import matplotlib.pyplot as plt
import argparse
from onedspec import OneDSpec
from scipy.interpolate import griddata
from scipy.constants import c
from matplotlib.ticker import ScalarFormatter

def convert_wavelengths_to_velocity(wavelengths, frequency):
    return [((w / frequency) - 1) * (c / 1000) for w in wavelengths]

parser = argparse.ArgumentParser(description='Make 2D grayscale image from multiple 1D spectra')
parser.add_argument('master', type=str)
parser.add_argument('file', type=str, nargs='+')
parser.add_argument('--cmap', '-c', type=str, default='gist_stern')
parser.add_argument('--title', '-t', type=str, default='')
parser.add_argument('--vmin', type=float)
parser.add_argument('--vmax', type=float)
parser.add_argument('--velocity', type=float,
        help='Specify rest frequency for velocity plot')

args = parser.parse_args()

x = np.array([])
y = np.array([])
z = np.array([])
ticks = []
master = OneDSpec(pyfits.open(args.master))
header = master.hdulist[0].header

length = len(master.data())
wavelengths = master.wavelengths()
if args.velocity:
    wavelengths = convert_wavelengths_to_velocity(wavelengths, args.velocity)
start_jd, _ = divmod(header['JD-MID'], 1)
a = np.empty(length)
ticks.append(header['JD-MID'] - start_jd)
a.fill(header['JD-MID'] - start_jd)
x = np.append(x, wavelengths)
y = np.append(y, a)
z = np.append(z, master.data())
xlabel = header['CUNIT1']
if args.velocity:
    xlabel = 'Velocity (km/s)'

for f in args.file:
  print "Processing %s" % (f)
  s = OneDSpec(pyfits.open(f))
  a = np.empty(length)
  ticks.append(s.hdulist[0].header['JD-MID'] - start_jd)
  a.fill(s.hdulist[0].header['JD-MID'] - start_jd)
  x = np.append(x, wavelengths)
  y = np.append(y, a)
  interp = s.interpolate_to(master)
  if args.velocity:
      convert_wavelengths_to_velocity(interp, args.velocity)
  z = np.append(z, interp)


# define regular grid spatially covering input data
n = length
xg = np.linspace(x.min(),x.max(),len(wavelengths))
yg = np.linspace(y.min(),y.max(),length)

X,Y = np.meshgrid(xg,yg)

# interpolate Z values on defined grid
Z = griddata(np.vstack((x.flatten(),y.flatten())).T, \
          np.vstack(z.flatten()),(X,Y),method='nearest').reshape(X.shape)
# mask nan values, so they will not appear on plot
Zm = np.ma.masked_where(np.isnan(Z),Z)

# plot
fig, ax = plt.subplots()
colormesh_args = {'cmap': args.cmap, 'shading': 'gouraud'}

if args.vmax:
    colormesh_args['vmax'] = args.vmax

if args.vmin:
    colormesh_args['vmin'] = args.vmin

pcm = ax.pcolormesh(X,Y,Zm, **colormesh_args)
fig.colorbar(pcm, ax=ax, use_gridspec=True)
ax.set_title(args.title)
ax.set_xlabel(xlabel)
ax.set_ylabel("JD - %d" % start_jd)
plt.yticks(ticks)

plt.tight_layout()
plt.show()
