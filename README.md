 Incorporated Research Institutions for Seismology (IRIS)
 Data Management Center (DMC)
 Data Products Team
 Noise Toolkit (NTK)

 2020-02-24
 V.2020.055

------------------------------------------------------------------------------------------------------------------------

 DESCRIPTION:

The IRIS DMC Noise Toolkit data product is a collection of three open-source bundles that provide relatively simple 
Python/ObsPy code bundles to:

    - compute power spectral density (PSD) of station waveform data using customized parameters (Noise Toolkit PDF/PSD bundle)
    - compute microseism energy from PSDs at different frequency bands (Noise Toolkit Microseism Energy bundle)
    - perform frequency dependent polarization analysis of the waveform data (Noise Toolkit Polarization Analysis bundle)

**PDF/PSD bundle**

The PDF/PSD bundle provides three highly configurable scripts to calculate waveform spectra in Python/ObsPyP. Although this package takes advantage of FDSN Web service client for ObsPy to retrieve necessary waveform data, but it also allows users to process waveform data from their local files. This package provides PSD file collections similar to popular PQLX package (McNamara and Boaz, 2005) and therefore it is compatible with existing user programs (see the Wiki page). The scripts included in this bundle are:

    - ntk_computePSD.py - a Python script to request waveforms and response data for given station(s) using the ObsPy FDSN client OR to read user's waveform data files (in SAC, MSEED, CSS, etc. format), compute PSDs and populate a file-based PSD database
    - ntk_extractPsdHour.py - a Python script to extract PSDs for a given channel and bounding parameters from the PSD database. The output is similar to PQLX's exPSDhour script
    - ntk_binPsdDay.py - a Python script to bin PSD's to daily files for a given channel and bounding parameters.

**Microseism Energy (ME) bundle**

 Microseism Energy (ME) bundle is a collection of three Python scripts that are configurable and allow users to conveniently calculate and plot microseism energy temporal variations in the period band of interest using the available PSD values. By default, the bundle is configured to to calculate ME over 1-5 s band, targeting smaller local storms for coastal stations, 5-10 s for the secondary microseisms, 11-30 s for the primary microseisms and the 50-200 s band for the Earth hum using PSDs of three-component broadband seismic data (BH channels). The stored microseism energy values will be smoothed using a median sliding time window (e.g. 6 hours, 12 hours, 1 day, 4 days, and 16 days, etc.).
 
 The scripts included in this bundle are:

    - ntk_computePower.py – a Python script to calculate power of each PSD window (by default 1 hour) over selected bin period bands
    - ntk_medianPower.py – a Python script to calculates median power from the PSD powers (by default hourly PSD power) using a sliding window of a given length (e.g., 12 hours)
    - ntk_plotPower.py – a Python script to plot median powers computed from a series of PSD powers

PSDs of seismic station waveform data needed for computation of the microseism energy are available from IRIS DMC via:

    - Noise Toolkit PDF-PSD bundle — an open-source Python script bundle to compute PSDs
    - PSDs computed by IRIS’s  MUSTANG noise-psd Web Service (http://service.iris.edu/mustang/noise-psd/1/)

**Polarization Attributes (POLAR) bundle**

The Polarization bundle of the Noise Toolkit is based on the eigen-decomposition of the spectra covariance matrix of a sliding window of three-component seismic data, as described by Koper and Hawley (2010). The derived frequency dependent polarization attributes are:

    - degree of polarization (β^2) - a measure of the extent to which noise is organized
    - polarization azimuth (θH) - a horizontal direction parameter representing azimuth of the polarization ellipsoid
    - polarization inclination (θV) - a vertical direction parameter representing inclination of the polarization ellipsoid
    - phase difference between components:
          o phase difference between the vertical and principal horizontal components (Φ VH)
          o phase difference between the horizontal components (Φ HH)

This bundle is composed of three Python scripts:

    - ntk_computePolarization.py – an ObsPy script to calculate polarization parameters for a given station and time window
    - ntk_extractPolarHour.py – a Python script to extract polarization parameters for the given channels and bounding parameters
    - ntk_binPolarDay.py – a Python script to bin polarization attributes to daily files for a given channel tag and bounding parameters
    
 FILES:

    PSD.CHANGES
       - a text file containing the history of changes to the PDF/PSD bundle
    ME.CHANGES
       - a text file containing the history of changes to the ME bundle
    POLAR.CHANGES
       - a text file containing the history of changes to the POLAR bundle

    INSTALL.txt
       - installation notes

    README.md
       - this file

    bin/
       - scripts directory containing:
            + computeStationChannelBaseline.py (described above)
            + computeHVSR.py (described above)
   
    param/
       - parameters directory containing:
            + getStationChannelBaseline_param.py - the configuration parameter file for the computeStationChannelBaseline.py script above
            + computeHVSR_param.py - the configuration parameter file for the computeHVSR.py script above

    lib/
       - bundle library files:
            + fileLib.py - a collection of functions to work with files and directories
            + msgLib.py - a collection of functions to print messages

 INSTALLATION:

    see the INSTALL.txt file


USAGE:
   
getStationChannelBaseline.py net=netName sta=staName loc=locCode chan=chanCode
	start=2007-03-19 end=2008-10-28 plot=[0|1] plotnnm=[0|1]verbose=[0, 1] percentlow=[10] 
	percenthigh=[90] xtype=[period,frequency]

net		station network code
sta		station code
loc		station location code
chan		station channel code (separate multiple channel codes by comma); 
		default: BHZ,BH1,BH2
xtype		X-axis  type; default: period
start		start date of the interval for which station baseline is computed (format YYYY-MM-DD).
		The start day begins at 00:00:00 UTC
end		end date of the interval for which station baseline is computed (format YYYY-MM-DD).
		The end day ends at 23:59:59 UTC

		NOTE: PSD segments will be limited to those starting between start (inclusive) and 
		end (exclusive) except when start and end are the same (in that case, the range will 
		cover start day only).

verbose		Run in verbose mode to provide informative messages [0=no, 1=yes];
		default:0
percentlow	lowest percentile to compute (float); default 5
percenthigh	Highest percentile to compute (float); default 90
plot		plot values [0|1]
plotnnm		plot the New Noise Models [0|1], active if plot=1


computeHVSR.py net=netName sta=staName loc=locCode chan=chanCodes start=2013-01-01 end=2013-01-01
plot=[0, 1] plotbad=[0|1] plotpsd=[0|1] plotpdf=[0|1] plotnnm=[0|1] verbose=[0|1] ymax=[maximum Y value]
xtype=[frequency|period] n=[number of segments] removeoutliers=[0|1] method=[1-6] showplot=[0|1]

net		station network code
sta		station code
loc		station location code
chan	station channel code (separate multiple channel codes by comma); 
		default: BHZ,BHN,BHE
xtype	X-axis  type; default: frequency
start	start date of the interval for which HVSR to be computed (format YYYY-MM-DD).
		The start day begins at 00:00:00 UTC
end		end date of the interval for which station baseline is computed (format YYYY-MM-DD).
		The end day ends at 23:59:59 UTC

		NOTE: PSD segments will be limited to those starting between start (inclusive) and 
		end (exclusive) except when start and end are the same (in that case, the range will 
		cover start day only).

verbose		Run in verbose mode to provide informative messages [0=no, 1=yes];
		    default:1
plotbad		plot rejected PSDs (float) if "plotpsd" option is selected; default 0
plotnnm		plot the New Noise Models [0|1], active if plot=1; default 1
plotpsd		plot PSDs; default 0
plotpdf		plot PSD\DFs; default 1
ymax		maximum Y values; default -50
n		    break start-end interval into 'n' segments; default 1
removeoutliers	remove PSDs that fall outside the station noise baseline; default 1
ymax		mcompute HVSR using method (see above); default 4
showplot	turn plot display on/off default is 1 (plot file is generated for both options)



EXAMPLES:

getStationChannelBaseline.py net=IU sta=ANMO loc=00 chan=BHZ start=2002-11-20 end=2008-11-20 plot=1 plotnnm=1 verbose=1 percentlow=10 percenthigh=90

getStationChannelBaseline.py net=TA sta=TCOL loc=-- chan=BHZ,BHN,BHE start=2013-01-01 end=2014-01-01 plot=1 plotnnm=1 verbose=1 percentlow=10 percenthigh=90

computeHVSR.py net=TA sta=TCOL loc=-- chan=BHZ,BHN,BHE start=2013-01-01 end=2013-01-01 plot=1 plotbad=0 plotpsd=0 plotpdf=1 verbose=1 ymax=5 xtype=frequency n=1 removeoutliers=0 method=4

computeHVSR.py net=TA sta=TCOL loc=-- chan=BHZ,BHN,BHE start=2013-01-01 end=2013-02-01 plot=1 plotbad=0 plotpsd=0 plotpdf=1 verbose=1 ymax=5 xtype=frequency n=1 removeoutliers=1 method=4

computeHVSR.py net=TA sta=M22K loc= chan=BHZ,BHN,BHE start=2017-01-01 end=2017-02-01 plot=1 plotbad=0 plotpsd=0 plotpdf=1 verbose=1 ymax=6 xtype=frequency n=1 removeoutliers=0 method=4

computeHVSR.py net=TA sta=E25K loc= chan=BHZ,BHN,BHE start=2017-01-01 end=2017-02-01 plot=1 plotbad=0 plotpsd=0 plotpdf=1 verbose=1 ymax=5 xtype=frequency n=1 removeoutliers=0 method=4

computeHVSR.py net=TA sta=E25K loc= chan=BHZ,BHN,BHE start=2017-07-01 end=2017-08-01 plot=1 plotbad=0 plotpsd=0 plotpdf=1 verbose=1 ymax=5 xtype=frequency n=1 removeoutliers=0 method=4


CITATION:

To cite the use of this software please cite:

Manochehr Bahavar, Zack J. Spica, Francisco J. Sánchez‐Sesma, Chad Trabant, Arash Zandieh, Gabriel Toro; Horizontal‐to‐Vertical Spectral Ratio (HVSR) IRIS Station Toolbox. Seismological Research Letters doi: https://doi.org/10.1785/0220200047

Or cite the following DOI:
    10.17611/dp/hvsrtool.1

REFERENCES:

Albarello, Dario & Lunedei, Enrico. (2013). Combining horizontal ambient vibration components for H/V 
	spectral ratio estimates. Geophysical Journal International. 194. 936-951. 10.1093/gji/ggt130.

Francisco J Sanchez-Sesma, Francisco & Rodriguez, Miguel & Iturraran-Viveros, Ursula & Luzon, Francisco
	& Campillo, Michel & Margerin, Ludovic & Garcia-Jerez, Antonio & Suarez, Martha & Santoyo, Miguel &

Peterson, J. (1993). Observations and modeling of seismic background noise, U.S. Geological Survey
	open-file report (Vol. 93-322, p. 94). Albuquerque: U.S. Geological Survey.

Rodriguez-Castellanos, A. (2011). A theory for microtremor H/V spectral ratio: Application for a
	layered medium. Geophysical Journal International. 186. 221-225. 10.1111/j.1365-246X.2011.05064.x.

Guidelines for the Implementation of the H/V Spectral Ratio Technique on Ambient Vibrations, December
	2004  Project No. EVG1-CT-2000-00026 SESAME.
		ftp://ftp.geo.uib.no/pub/seismo/SOFTWARE/SESAME/USER-GUIDELINES/SESAME-HV-User-Guidelines.pdf




 HISTORY
    - 2020-02-24 Release R.1.1
    - 2019-07-31  Release R.1.0
    - 2018-07-10: prerelease V.2018.191
    - 2017-11-28: computeHVSR V.2017.332
    - 2017-11-16: initial version V.2017.320
 
 COMMENTS/QUESTIONS:

    Please contact manoch@iris.washington.edu

