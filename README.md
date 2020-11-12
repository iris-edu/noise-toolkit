 Incorporated Research Institutions for Seismology (IRIS)\
 Data Management Center (DMC)\
 Data Products Team\
 Noise Toolkit (NTK)

 2020-11-16\
 V.2.0 for Python 3

------------------------------------------------------------------------------------------------------------------------

**NOTES:**
 
This repository is the new home for the IRIS DMC Noise Toolkit data product packages (previously hosted on seiscode.iris.washington.edu):

    https://github.com/iris-edu/noise-toolkit/releases/tag/V.2.0:
    - The latest release under Python 3 that includes:
       - use of IRIS Fedcatalog to access station data across FDSN data centers 
         (http://service.iris.edu/irisws/fedcatalog/1/)
       - use matplotlib.mlab csd to compute  spectral density
       - adoption of PEP 8 style guide
    
    https://github.com/iris-edu/noise-toolkit/releases/tag/V.1.0:
    Original release under Python 2.7 that was hosted on seiscode:
    - IRIS_NTK_PSD_scripts_0.9.5.tar.gz
    - IRIS_NTK_ME_scripts_0.6.0.tar.gz
    - IRIS_NTK_POLAR_scripts_0.6.5.tar.gz
    
    
**DESCRIPTION:**

The IRIS DMC Noise Toolkit data product is a collection of three open-source packages that provide relatively simple 
Python 3 /ObsPy scripts to:

    - compute power spectral density (PSD) of station waveform data using customized parameters (Noise Toolkit 
      PDF/PSD package)
    - compute microseism energy from PSDs at different frequency bands (Noise Toolkit Microseism Energy package)
    - perform frequency dependent polarization analysis of the waveform data (Noise Toolkit Polarization 
      Analysis package)

**PDF/PSD package** (Wiki page, https://github.com/iris-edu/noise-toolkit/wiki/Noise-Toolkit-PDF-PSD-package-2)

The PDF/PSD package provides three highly configurable Python 3 scripts to calculate waveform spectra. This package takes advantage of FDSN Web service client for ObsPy to retrieve necessary waveform data, and it also allows users to process waveform data from their local files. This package provides PSD file collections similar to popular PQLX package (McNamara and Boaz, 2005, https://www.usgs.gov/software/pqlx-a-software-tool-evaluate-seismic-station-performance). The scripts included in this package are:

    - ntk_computePSD.py - request waveforms and response data for given station(s) using the ObsPy FDSN client OR to 
      read user's waveform data files (in SAC, MSEED, CSS, etc. format), and compute PSDs and populate a file-based 
      PSD database
      NOTE: *ntk_computePSD.py first identifies the appropriate FDSN data provider for the requested station using the 
      Fedcatalog service from IRIS (https://service.iris.edu/irisws/fedcatalog/1/) and then requests waveform/response 
      data for that station using ObsPy's FDSN client*
    - ntk_extractPsdHour.py - extract PSDs for a given channel and bounding parameters from the PSD database
      (the output is similar to PQLX's exPSDhour script, https://pubs.usgs.gov/of/2010/1292/)
    - ntk_binPsdDay.py - bins PSD's to daily files for a given channel and bounding parameters.

**Microseism Energy (ME) package** (Wiki page, https://github.com/iris-edu/noise-toolkit/wiki/Noise-Toolkit-Microseism-Energy-(ME)-package-2)

 Microseism Energy (ME) package is a collection of three Python 3 scripts that are configurable and allow users to conveniently calculate and plot microseism energy temporal variations in the period band of interest using the available PSD values. By default, the package is configured to to calculate ME over 1-5 s band, targeting smaller local storms for coastal stations, 5-10 s for the secondary microseisms, 11-30 s for the primary microseisms and the 50-200 s band for the Earth hum using PSDs of three-component broadband seismic data (BH channels). The stored microseism energy values will be smoothed using a median sliding time window (e.g. 6 hours, 12 hours, 1 day, 4 days, and 16 days, etc.).
 
 The scripts included in this package are:

    - ntk_computePower.py – calculates power in each PSD window (by default 1 hour) over selected bin period bands
    - ntk_medianPower.py – calculates median power from the PSD powers (by default hourly PSD power) using a sliding 
      window of a given length (for example 12 hours)
    - ntk_plotPower.py – plots median powers computed from a series of PSD powers

PSDs of seismic station waveform data needed for computation of the microseism energy are available from IRIS DMC via:

    - the PDF-PSD package above
    - PSDs computed by IRIS’s  MUSTANG noise-psd Web Service (http://service.iris.edu/mustang/noise-psd/1/)

**Polarization Attributes (POLAR) package** (Wiki page, https://github.com/iris-edu/noise-toolkit/wiki/Noise-Toolkit-Polarization-Attributes-package-2)

The Polarization package of the Noise Toolkit is based on the eigen-decomposition of the spectra covariance matrix of a sliding window of three-component seismic data, as described by Koper and Hawley (2010). The derived frequency dependent polarization attributes are:

    - degree of polarization (β^2) - a measure of the extent to which noise is organized
    - polarization azimuth (θH) - a horizontal direction parameter representing azimuth of the polarization ellipsoid
    - polarization inclination (θV) - a vertical direction parameter representing inclination of the polarization 
      ellipsoid
    - phase difference between components:
          o phase difference between the vertical and principal horizontal components (Φ VH)
          o phase difference between the horizontal components (Φ HH)

This package is composed of three scripts:

    - ntk_computePolarization.py – calculates polarization parameters for a given station and time window
    - ntk_extractPolarHour.py – tracts polarization parameters for the given channels and bounding parameters
    - ntk_binPolarDay.py – bins polarization attributes to daily files for a given channel tag and bounding parameters
    
**CHANGES:**

    PSD.CHANGES - history of changes to the PDF/PSD package
    ME.CHANGES - history of changes to the ME package
    POLAR.CHANGES - history of changes to the POLAR package

**MORE INFORMATION:**

see IRIS Noise Toolkit data product page https://ds.iris.edu/ds/products/noise-toolkit/
see the Wiki pages at https://github.com/iris-edu/noise-toolkit/wiki
 
 COMMENTS/QUESTIONS:

    Please contact manoch@iris.washington.edu

