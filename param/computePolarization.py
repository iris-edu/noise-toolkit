import shared
import os

# How file naming is done?
namingConvention = shared.namingConvention

# Verbose mode on/off (1/0).
verbose = 0

# Timing mode on/off (1/0).
timing = 0

# UserAgent is used to identify the data requester, please change.
userAgent = "product_pub_noise-toolkit_polarization"

# Turn plotting on or off (0/1).
plot = 0

# Image size (width, height).
figureSize = 18.0, 12.0

# Plot trace?
plotTraces = 0

# Plot spectra?
plotSpectra = 1

# Plot the smoothed spectra?
plotSmooth = 1

# Plot Peterson's New LNM and HNM.
plotNm = 1

# Output smoothed values?
outputValues = 1

# Trace scaling for display
scaling = 1

# Plot colors.
# Spectra plot color
colorSpectra = "blue"

# Timeseries plot color
colorTrace = "blue"

# Smooth plot color orange
colorSmooth = "red"

# Smoothing
#
# Smoothing window width in octave
# for test against PQLX use 1 octave width
doSmoothing = 1

# Smoothing window width:
# float(1.0/1.0)= 1 octave smoothing
# float(1.0/4.0) 1/4 octave smoothing, etc
octaveWindowWidth = float(1.0/4.0)

# Smoothing window shift :
# float(1.0/4.0)= 1/4 octave shift
# float(1.0/8.0) 1/8 octave shift, etc
octaveWindowShift = float(1.0/8.0)

# Directory info from shared file
ntkDirectory = shared.ntkDirectory
workDir = shared.workDir
dataDirectory = shared.dataDirectory
respDirectory = shared.respDirectory
polarDbDirectory = shared.polarDbDirectory

# Possible x-axis types.
xType = shared.xType

# Smoothing starting frequency/period reference (Nyquist= "Nyquist frequency",  1= 1Hz/1Sec)
xStart = ['Nyquist', 'Nyquist']
xlabel = {"period": "Period (s)", "frequency": "Frequency (Hz)"}
header = {"period": "     Period   PowerUD  powerEW     powerNS      Lambda      Beta^2      "
                    "ThetaH      ThetaV       PhiVH       PhiHH",
          "frequency": "   Frequency  PowerUD     powerEW     powerNS      Lambda      Beta^2      "
                       "ThetaH      ThetaV       PhiVH       PhiHH"}

# Turn header on/off (1/0)
showHeader = 1

maxT = 100
# Seconds, sub-windows of the above window for processing
windowLength = 3600
# Overlap as percent (0.5 = 50%).
windowShift = int(windowLength * 0.5)

#  NOTE: make sure that components in each group are in the CORRECT order (BHZ, BHE, BHN)
channel = "BH?"
channelGroups = [["BHZ", "BHE", "BHN"], ["BHZ", "BH2", "BH1"], ["LHZ", "LHE", "LHN"], ["LHZ", "LH2", "LH1"],
                 ["HHZ", "HHE", "HHN"], ["HHZ", "HH2", "HH1"]]

performInstrumentCorrection = True
demean = True

# True will scale the waveform by the stage-zero gain,
# not used if performInstrumentCorrection above is set to True
applyScale = True

# set water-level in db to use it when inverting spectrum. The ObsPy module shrinks values under
# water-level of max spec amplitude. In other words, water-level represents a clipping of the inverse spectrum and
# limits amplification to a certain maximum cut-off value
# see: http://docs.obspy.org/master/_modules/obspy/core/trace.html#Trace.remove_response
waterLevel = 120

# Decon filter
# define a filter band to prevent amplifying noise during the deconvolution.
# Set ALL deconFilter parameter values to <= 0 to bypass this filter.
deconFilter1 = 0.001
deconFilter2 = 0.005
deconFilter3 = 8.0
deconFilter4 = 10.0

deconFilter = (deconFilter1, deconFilter2, deconFilter3, deconFilter4)

# Units to return response in ('DIS', 'VEL' or ACC)
unit = "ACC"
unitLabel = "m/s/s"

# If instrument response correction is not requested, then units must be provided by user
# under generic label of "SEIS" for seismic and "INF" for infrasound
powerUnits = {"M/S": "Power[10 log10(m**2/s**4/Hz)](dB)", "PA": "Power[10 log10(Pascals**2/Hz)](dB)"}

# Plot parameters
ylimLow = dict()
ylimHigh = dict()
xlimMin = dict()
xlimMax = dict()

# Variables to compute.
variables = ["powerUD", "powerEW", "powerNS", "powerLambda", "betaSquare", "thetaH", "thetaV", "phiVH", "phiHH"]

periodMin = 0.1
periodMax = 200
for var in variables:
    xlimMin.update({var: {"period": periodMin, "frequency": 1.0/periodMax}})
    xlimMax.update({var: {"period": periodMax, "frequency": 1.0/periodMin}})

ylimLow = {"powerUD": -200,
           "powerEW": -200,
           "powerNS": -200,
           "powerLambda": -200,
           "betaSquare": 0,
           "thetaH": 0,
           "thetaV": 0,
           "phiVH": -90,
           "phiHH": -180}

ylimHigh = {"powerUD": -70,
            "powerEW": -70,
            "powerNS": -70,
            "powerLambda": -70,
            "betaSquare": 1,
            "thetaH": 360,
            "thetaV": 90,
            "phiVH": 90,
            "phiHH": 180
            }

subplot = {"powerUD": 331,
           "powerEW": 334,
           "powerNS": 337,
           "powerLambda": 332,
           "betaSquare": 335,
           "thetaH": 338,
           "thetaV": 333,
           "phiVH": 336,
           "phiHH": 339}

yLabel = {"powerUD": "UD " + powerUnits['M/S'],
          "powerEW": "EW " + powerUnits['M/S'],
          "powerNS": "NS " + powerUnits['M/S'],
          "powerLambda": "Lambda power/dB",
          "betaSquare": "degree of polarization (Beta^2)",
          "thetaH": "Polarization azimuth (Theta H)",
          "thetaV": "Polarization inclination (Theta V)",
          "phiVH": "V-H phase difference (Phi VH)",
          "phiHH": "H-H phase difference (Phi H-H)"
          }

"""
  requestClient to call to get the waveforms from (FDSN OR FILES). 
 
  most waveforms should be requested using FDSN
  for restricted data access, you need user and password information
  for information on how to access restricted data see:
  http://service.iris.edu/irisws/timeseries/1/
  
  set requestClient = "FILES" to read files from local disk (using fileTag to point to them)
"""
requestClient = "FDSN"

# Get responses from local files only. If False, will go to IRIS to get the missing responses
fromFileOnly = True
fileTag = os.path.join(dataDirectory, "SAC", "*.SAC")

user = None
password = None

# Total number of segments to calculate FFT for a window.
nSegments = 15

# Percent segment overlap
percentOverlap = 50

# Number of side-by-side segments for the above nSegments and percent Overlap.
# There are (nSegments -1) non-overlapping segments and 1 full segment.
nSegWindow = int((nSegments - 1) * (1.0 - float(percentOverlap) / 100.0)) + 1


