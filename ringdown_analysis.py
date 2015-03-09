#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
This is a manual computation of Fourier transform, to verify that the numpy.fft's or scipy's built-in Fast Fourier Transform
behaves as expected also in terms of accumulated power etc.

The curves obtained using the 
    1) frequency `f'
    2) angular frequency `omega'
are obviously different: when the _angular_ frequency `omega' is used, its axis dilates by 2pi, and 
accordingly, the values have to be divided by sqrt(2pi) (NB this is due to the Fourier-Plancherel theorem, 
which is tested below)

The frequency `f' approach is used by numpy.fft, and it can be shown that it gives data nearly identical to the manually computed FT.

Public domain, 2014 F. Dominec
"""

## Import common moduli
import matplotlib, sys, os, time
import matplotlib.pyplot as plt
import numpy as np
from scipy.constants import c, hbar, pi

## == User settings ==
analytic_input =      1
harmonic_inversion  = 1
analytic_lorentzian = 1  # Knowing the oscillator parametres, we can compare to the analytic solution
plot_absolute_value = 1
plot_ylog =           1
test_kramers_kronig = 1  # Compare data to their Hilbert transform (warning - short time record makes the KKR data ugly)

convention = 'f'            
#convention = 'omega'

FDMtrunc = (.35, 1.)         # Harminv (also known as FDM) may work better when it is supplied a shorter time record
                            # and it requires clipping the initial timespan when the source is operating

frequency_zoom = .05         # higher value = broader scope
frequency_full_axis = 0     # if enabled, does not clip the plotted range

# The following adds a Dirac-delta function at zero time, emulating e.g. the vacuum permittivty
# (note: Plancherel theorem is not valid for delta function in numerical computation)
add_delta_function =  0

## == /User settings ==

## Prepare plot, optionally use LaTeX
#matplotlib.rc('text', usetex=True)
#matplotlib.rc('font', size=12)
#matplotlib.rc('text.latex', preamble = '\usepackage{amsmath}, \usepackage{yfonts}, \usepackage{txfonts}, \usepackage{lmodern},')
#matplotlib.rc('font',**{'family':'serif','serif':['Computer Modern Roman, Times']})  ## select fonts
plt.figure(figsize=(20,10))


## == Time domain ==
plt.subplot(121)

if len(sys.argv) <= 1: 
    ## Generate time-domain data
    x, omega0, gamma, ampli = np.linspace(0., 10e-12, 4000), 2*np.pi*5e12, 2*np.pi*3e11, 1. ## note: everything should work for any frequency scale
    #x, omega0, gamma, ampli = np.linspace(0, 25, 3000), 2*np.pi*2, 2*np.pi*.3, 1.

    y = ampli * (np.sign(x)/2+.5) * np.sin(x*omega0) * np.exp(-x*gamma/2)           ## damped oscillator
    if add_delta_function:
        if convention == 'f':
            y[int(len(x)*(-x[0]/(x[-1]-x[0])))] +=         1 / (x[1]-x[0])  ## delta function suitable for f-convention 
        elif convention == 'omega':
            print "Warning: Delta function unclear how to be implemented in omega convention"
            y[int(len(x)*(-x[0]/(x[-1]-x[0])))] +=         1 / (x[1]-x[0])  ## delta function suitable for omega-convention 
    analytic_input = True
else:
    ## Load time-domain data
    try:
        data = np.loadtxt(sys.argv[1], unpack=True)
        if len(data) == 3:
            x, Eabs, Ephase = data
            y = Eabs * np.exp(1j*Ephase) # TODO harminv fails to find heavily damped oscillators;   to test out, add something like: * np.exp(-x/1e-12)
        else:
            x, y = data
        analytic_input = False
    except IndexError:
        print "Error: if a timedomain file is provided, it must have 2 or 3 columns: time, amplitude, [phase]"; quit()

maxplotf = frequency_zoom / (x[1]-x[0])

## Plot time-domain
plt.plot(x, y.real, c='#aa0088', label="Real part")
plt.plot(x, y.imag, c='#aa0088', label="Imaginary part", ls='--')
plt.grid(); plt.yscale('linear'); 
plt.legend(prop={'size':10}, loc='upper right'); plt.xlabel(u"time $t$"); plt.ylabel(u"response"); plt.title(u"a) Time domain")
Wt = np.trapz(y=np.abs(y)**2, x=x); print 'Plancherel theorem test: Energy in timedomain              :', Wt


## == Frequency domain ==
plt.subplot(122)

## An exact curve for the analytic solution of a damped oscillator
def lorentz(omega, omega0, gamma, ampli):
    return ampli / (omega0**2 - omega**2 + 1j*omega*gamma) 

def naive_hilbert_transform(x, y, new_x): ## or, just a discrete convolution with the 1/t function
    old_x_grid, new_x_grid = np.meshgrid(x, new_x)
    sharpness = 5000         # with ideally dense-sampled data, this should converge to infinity; reduce it to avoid ringing 
    return -1j * np.sum(y * np.arctan(1/(new_x_grid - old_x_grid)/sharpness)*sharpness, axis=1) / len(x) / (2*pi)

def plot_complex(x, y, **kwargs):
    if plot_absolute_value:
        plt.plot(x, np.abs(y), **kwargs)
    else:
        kwargsr = kwargs.copy(); kwargsr['label']+=' (real)'; plt.plot(x, y.real, **kwargsr)
        kwargsi = kwargs.copy(); kwargsi['label']+=' (imag)'; plt.plot(x, y.imag, ls='--', **kwargsi)

## Scipy's  implementation of Fast Fourier transform
freq    = np.fft.fftfreq(len(x), d=(x[1]-x[0]))                 # calculate the frequency axis with proper spacing
yf2     = np.fft.fft(y, axis=0) * (x[1]-x[0])                   # calculate FFT values (maintaining the Plancherel theorem)
freq    = np.fft.fftshift(freq)                                 # reorders data to ensure the frequency axis is a growing function
yf2     = np.fft.fftshift(yf2) / np.exp(1j*2*pi*freq * x[0])    # dtto, and corrects the phase for the case when x[0] != 0
truncated = np.logical_and(freq>-maxplotf, freq<maxplotf)         # (optional) get the frequency range
(yf2, freq) = map(lambda x: x[truncated], (yf2, freq))    # (optional) truncate the data points
plot_complex(freq, yf2, c='#eedd00', label='ScipyFFT in $f$', lw=1, alpha=.8)
Ws = np.trapz(y=np.abs(yf2)**2, x=freq); print 'Plancherel theorem test: Energy in freqdomain f (by Scipy) :', Ws 

## Own implementation of slow Fourier transform - in f
f = np.linspace(-maxplotf, maxplotf, 1000)
yf = np.sum(y * np.exp(-1j*2*pi*np.outer(f,x)), axis=1) * (x[1]-x[0])
plot_complex(f, yf, c='#ff4400', label='Manual FT in $f$', lw=1, alpha=.8)
Wm = np.trapz(y=np.abs(yf)**2, x=f); print 'Plancherel theorem test: Energy in freqdomain f (manual)   :', Wm

if test_kramers_kronig:
    ## Test the Kramers-Kronig relations - in f
    new_f = np.linspace(-maxplotf, maxplotf, 1000)
    conv = naive_hilbert_transform(f, yf, new_f)
    plot_complex(new_f, conv, c='k', alpha=1, lw=.5, label='KKR in $f$') 

if analytic_input and analytic_lorentzian:
    lor = lorentz(omega=f*2*pi, omega0=omega0, gamma=gamma, ampli=ampli*omega0)
    plot_complex(f, lor, c='b', alpha=.8, lw=1.5,  label='Exact Lorentzian in $f$') 
    Wa = np.trapz(y=np.abs(lor)**2, x=f); print 'Plancherel theorem test: Energy in analytic osc (f)        :', Wa 
    print 'Analytic    oscillators frequency, decay and amplitude:\n', np.vstack([omega0/2/np.pi, gamma/2/np.pi, ampli])

if harmonic_inversion:
    import harminv_wrapper
    tscale = 1.0     ## harminv output may have to be tuned by changing this value
    x = x[int(len(x)*FDMtrunc[0]):int(len(x)*FDMtrunc[1])]*tscale
    y = y[int(len(y)*FDMtrunc[0]):int(len(y)*FDMtrunc[1])]
    hi = harminv_wrapper.harminv(x, y, amplitude_prescaling=None)
    hi['frequency'] *= tscale 
    hi['decay'] *= 2/np.pi * tscale

    oscillator_count = len(hi['frequency'])
    freq_fine = np.linspace(-maxplotf, maxplotf, 2000)
    sumosc = np.zeros_like(freq_fine)*1j
    for osc in range(oscillator_count):
        #osc_y = lorentz(omega=freq_fine*2*pi,   omega0=hi['frequency'][osc]*2*pi, gamma=hi['decay'][osc]*4, ampli=hi['amplitude'][osc]*pi**2)
        osc_y = lorentz(omega=freq_fine*2*pi,   
                omega0=hi['frequency'][osc]*2*pi, 
                gamma=hi['decay'][osc]*2*pi, 
                ampli=hi['amplitude'][osc] * np.abs(hi['frequency'][osc]) * 4*np.pi )   #  * np.abs(hi['decay'][osc])
        sumosc += osc_y 
    plot_complex(freq_fine, sumosc, color="#00aa00", label=u"Harminv modes sum")      # (optional) plot amplitude
    Wh = np.trapz(y=np.abs(sumosc)**2, x=freq_fine); print 'Plancherel theorem test: Energy in Harminv f               :', Wh, '(i.e. %.5g of timedomain)' % (Wh/Wt)
    print 'All harminv oscillators (frequency, decay and amplitude):\n', np.vstack([hi['frequency'], hi['decay'], hi['amplitude']])

elif convention == 'omega':
    # Own implementation of slow Fourier transform - in omega XXX
    omega = np.linspace(-maxplotf*2*pi, maxplotf*2*pi, 3000)  # (note: if only positive frequencies are used, the energy will be half of that in time-domain)
    yomega = np.sum(y * np.exp(-1j*        np.outer(omega,x)), axis=1) * (x[1]-x[0])  / np.sqrt(2*pi)
    plot_complex(omega, yomega, c='#440088', label='Real part') # , label='FT in $\\omega$-convention'
    print 'Plancherel theorem test: Energy in freqdomain omega :', np.trapz(y=np.abs(yomega)**2, x=omega)

    if test_kramers_kronig:
        ## Test the Kramers-Kronig relations - in omega
        new_omega = np.linspace(5, 8, 500)
        conv = naive_hilbert_transform(omega, yomega, new_omega)
        plot_complex(new_omega, conv, ls='-', c='k', alpha=1, lw=.5, label='KKR in $f$', ms=3, marker='o') 

    if analytic_lorentzian:
        lor = lorentz(omega=omega, omega0=omega0, gamma=gamma, ampli=ampli) / (2*pi)**.5
        plot_complex(omega, lor, ls='-',  c='r', alpha=1, lw=.5,  label='Osc in $f$') 

## Finish the frequency-domain plot + save 
if not frequency_full_axis: plt.xlim(left=0, right=maxplotf)
plt.xscale('linear')
#plt.ylim((-16,16)); 
if plot_ylog:
    plt.yscale('log')
else:
    plt.yscale('linear')

if convention == 'f':
    plt.xlabel(u"frequency $f$"); 
elif convention == 'omega': 
    plt.xlabel(u"angular frequency $\\omega$"); 
plt.ylabel(u"local permittivity $\\varepsilon^{\\rm(Loc)}(\\omega)$"); 
plt.title(u"b) Frequency domain")
plt.grid()

plt.legend(prop={'size':10}, loc='upper right')
plt.savefig("oscillator_spectrum.png", bbox_inches='tight')
