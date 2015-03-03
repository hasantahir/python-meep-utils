#!/usr/bin/env python
#-*- coding: utf-8 -*-

import numpy as np
## Harminv
def harminv(x, y, d=100, f=30, amplitude_prescaling=None):
    """
    suggested visualisation:
    hi = harminv(x,y)
    c = plt.scatter(hi['frequency'], hi['amplitude'], c=hi['phase'], s=np.abs(hi['quality'])/20 + 2, cmap=plt.cm.hsv, alpha=.3)
    """

    if amplitude_prescaling == None:
        amplitude_prescaling = 1000./np.max(np.abs(y))

    with open('/tmp/hitest.dat', 'w') as outfile: 
        outfile.write("#t[s]\t E(t)\n")
        np.savetxt(outfile, zip(x/2, np.real(y) * amplitude_prescaling), fmt="%.8e")
    import subprocess
    dt = x[1]-x[0]
    #subprocess.Popen('harminv 0-1000 -t %g -d %g -f %g < hitest.dat > hiout.dat' % (dt, d, f), shell=True, stdout=subprocess.PIPE).stdout.read().strip()
    #subprocess.Popen('harminv 0-%f -t %g -d %g -f %g < /tmp/hitest.dat > /tmp/hiout.dat' % (1/dt/10, dt, d, f), shell=True, stdout=subprocess.PIPE).stdout.read().strip()
    subprocess.Popen('harminv %f-%f -t %g   < /tmp/hitest.dat > /tmp/hiout.dat' % (0, 1./dt/10., dt*1.), shell=True, stdout=subprocess.PIPE).stdout.read().strip()
    try:
        (mf, md, mQ, mA, mp, merr) = np.loadtxt('/tmp/hiout.dat', usecols=list(range(6)), unpack=True, delimiter=', ', skiprows=1)
    except:
        print "\nWARNING: Harminv detected no resonances.\n\n"
        (mf, md, mQ, mA, mp, merr) = [np.array([]) for _ in range(6)]

    if type(mf) == np.float64:
        (mf, md, mQ, mA, mp, merr) = [np.array([val]) for val in (mf, md, mQ, mA, mp, merr)]

    return {'frequency':mf*2, 'decay':md, 'quality':mQ, 'amplitude':mA / amplitude_prescaling, 'phase':mp, 'error':merr}
