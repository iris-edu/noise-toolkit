 Incorporated Research Institutions for Seismology (IRIS)\
 Data Management Center (DMC)\
 Data Products Team\
 Noise Toolkit (NTK)

 2020-10-28\
 R.1.0 for Python 2.7

------------------------------------------------------------------------------------------------------------------------

**NOTES:**
 
This repository is the new home for the following IRIS DMC Noise Toolkit data product bundles (previously hosted on seiscode.iris.washington.edu):

    - IRIS_NTK_PSD_scripts_0.9.5.tar.gz
    - IRIS_NTK_ME_scripts_0.6.0.tar.gz
    - IRIS_NTK_POLAR_scripts_0.6.5.tar.gz
    
    
**DESCRIPTION:**

The IRIS DMC Noise Toolkit data product is a collection of three open-source bundles that provide relatively simple 
Python 2.7 /ObsPy code bundles to:

    - compute power spectral density (PSD) of station waveform data using customized parameters (Noise Toolkit 
      PDF/PSD bundle)
    - compute microseism energy from PSDs at different frequency bands (Noise Toolkit Microseism Energy bundle)
    - perform frequency dependent polarization analysis of the waveform data (Noise Toolkit Polarization 
      Analysis bundle)

**PDF/PSD bundle**

The PDF/PSD bundle provides three highly configurable Python 2.7 scripts to calculate waveform spectra in Python/ObsPyP. Although this package takes advantage of FDSN Web service client for ObsPy to retrieve necessary waveform data, but it also allows users to process waveform data from their local files. This package provides PSD file collections similar to popular PQLX package (McNamara and Boaz, 2005) and therefore it is compatible with existing user programs (see the Wiki page). The scripts included in this bundle are:

    - ntk_computePSD.py - a Python 2.7 script to request waveforms and response data for given station(s) using the 
      ObsPy FDSN client OR to read user's waveform data files (in SAC, MSEED, CSS, etc. format), compute PSDs and 
      populate a file-based PSD database
    - ntk_extractPsdHour.py - a Python 2.7 script to extract PSDs for a given channel and bounding parameters from the 
      PSD database. The output is similar to PQLX's exPSDhour script
    - ntk_binPsdDay.py - a Python 2.7 script to bin PSD's to daily files for a given channel and bounding parameters.

**Microseism Energy (ME) bundle**

 Microseism Energy (ME) bundle is a collection of three Python 2.7 scripts that are configurable and allow users to conveniently calculate and plot microseism energy temporal variations in the period band of interest using the available PSD values. By default, the bundle is configured to to calculate ME over 1-5 s band, targeting smaller local storms for coastal stations, 5-10 s for the secondary microseisms, 11-30 s for the primary microseisms and the 50-200 s band for the Earth hum using PSDs of three-component broadband seismic data (BH channels). The stored microseism energy values will be smoothed using a median sliding time window (e.g. 6 hours, 12 hours, 1 day, 4 days, and 16 days, etc.).
 
 The scripts included in this bundle are:

    - ntk_computePower.py – a Python 2.7 script to calculate power of each PSD window (by default 1 hour) over selected 
      bin period bands
    - ntk_medianPower.py – a Python 2.7 script to calculates median power from the PSD powers (by default hourly PSD 
      power) using a sliding window of a given length (e.g., 12 hours)
    - ntk_plotPower.py – a Python 2.7 script to plot median powers computed from a series of PSD powers

PSDs of seismic station waveform data needed for computation of the microseism energy are available from IRIS DMC via:

    - Noise Toolkit PDF-PSD bundle — an open-source Python 2.7 script bundle to compute PSDs
    - PSDs computed by IRIS’s  MUSTANG noise-psd Web Service (http://service.iris.edu/mustang/noise-psd/1/)

**Polarization Attributes (POLAR) bundle**

The Polarization bundle of the Noise Toolkit is based on the eigen-decomposition of the spectra covariance matrix of a sliding window of three-component seismic data, as described by Koper and Hawley (2010). The derived frequency dependent polarization attributes are:

    - degree of polarization (β^2) - a measure of the extent to which noise is organized
    - polarization azimuth (θH) - a horizontal direction parameter representing azimuth of the polarization ellipsoid
    - polarization inclination (θV) - a vertical direction parameter representing inclination of the polarization 
      ellipsoid
    - phase difference between components:
          o phase difference between the vertical and principal horizontal components (Φ VH)
          o phase difference between the horizontal components (Φ HH)

This bundle is composed of three Python 2.7 scripts:

    - ntk_computePolarization.py – an Python 2.7 script to calculate polarization parameters for a given station and 
      time window
    - ntk_extractPolarHour.py – a Python 2.7 script to extract polarization parameters for the given channels and 
      bounding parameters
    - ntk_binPolarDay.py – a Python 2.7 script to bin polarization attributes to daily files for a given channel tag 
      and bounding parameters
    
**CHANGES:**

    PSD.CHANGES - history of changes to the PDF/PSD bundle
    ME.CHANGES - history of changes to the ME bundle
    POLAR.CHANGES - history of changes to the POLAR bundle

**MORE INFORMATION:**

See the Wiki pages at https://github.com/iris-edu/noise-toolkit/wiki
 
 COMMENTS/QUESTIONS:

    Please contact manoch@iris.washington.edu


