import math, os
import common

#
# how file naming is donet
#
namingConvention = common.namingConvention

#
# initialize a few parametrs
#
VERBOSE       = 0         # thurn the verbose mode on or off
userAgent     = "product_pub_noise-toolkit_psd" # userAgent is used to identify the data requester, please change
plot          = 0         # turn plotting on or off
plotTraces    = 0         # plot trace?
plotSpectra   = 1         # plot spectra?
plotSmooth    = 1         # plot the smoothed spectra?
outputValues  = 1         # output smooth values
colorSpectra  = "blue"    # spectra plot color
colorTrace    = "blue"    # timeseries plot color
colorSmooth   = "orange"     # smooth plot color orange

#
# smoothing
#
# smoothing window width in octave 
# for test against PQLX use 1 octave width
#
octaveWindowWidth    = float(1.0/2.0)   # smoothing window width : float(1.0/1.0)= 1 octave smoothing; float(1.0/4.0) 1/4 octave smoothing, etc
octaveWindowShift    = float(1.0/8.0)   # smoothing window shift : float(1.0/4.0)= 1/4 octave shift; float(1.0/8.0) 1/8 octave shift, etc

ntkDirectory   = common.ntkDirectory
workDir        = common.workDir
dataDirectory  = common.dataDirectory
respDirectory   = common.respDirectory
psdDbDirectory = common.psdDbDirectory # PSD database directory where individual PSD files are stored

xType          = ["period","frequency"]
xStart         = ["Nyquist","Nyquist"] # smoothing starting ferqueny/period reference (Nyquist= Nyquist frequency, 1= 1Hz/1Sec)
xlabel         = {"period":"Period (s)", "frequency":"Frequency (Hz)"}
maxT           = 200
windowLength   = 3600    # seconds, subwindows of the above window for processing
windowShift    = int(windowLength * 0.5) # 50% overlap
channel        = "BH?"
#channel        = "BDF"

#
# plot parameters
#
ylimLow        = {"BHZ":-170,"BHN":-170,"BHE":-170,"BH1":-200,"BH2":-200,"BDF":-80}
ylimHigh       = {"BHZ":-100,"BHN":-100,"BHE":-100,"BH1":-50,"BH2":-50,"BDF":50}
xlimMin        = {"BHZ":[0.1,0.005], "BHN":[0.1,0.005],"BHE":[0.1,0.005],"BH1":[0.1,0.005],"BH2":[0.1,0.005], "BDF":[0.1,0.05]}
xlimMax        = {"BHZ":[200.0,10.0], "BHN":[200.0,10.0],"BHE":[200.0,10.0],"BH1":[200.0,10.0],"BH2":[200.0,10.0],"BDF":[200.0,10.0]}

#
# decon filter frequency bands, Hz
# define a filter band to prevent amplifying noise during the deconvolution
#
performInstrumentCorrection = True
applyScale   = True # True will scale the waveform by the stage-zero gain, not used if performInstrumentCorrection above is set to True
waterLevel   = 120  # set water-level in db to use it when inverting spectrum. The ObsPy module shrinks values under 
                    # water-level of max spec amplitude. In other wortds, water-level represents a clipping of the inverse spectrum and 
                    # limits amplification to a certain maximum cut-off value
                    # see: http://docs.obspy.org/master/_modules/obspy/core/trace.html#Trace.remove_response
                    #

deconFilter1 = 0.001 # you may set ALL deconFilter parameter values to <= 0 to bypass this filter
deconFilter2 = 0.005
deconFilter3 = 8.0
deconFilter4 = 10.0

#
# normalization factor to be included while converting power to PSD
# set to 1.0 if extra factor is not needed
#
#normFactor = 1.0
normFactor = 2.0


##################################################################################
#
# requestClient to call to get the waveforms from (FDSN, IRIS or FILES). 
#
# most waveforms should be requested using FDSN
#
# for restricted data access, you need user and password information
# for information on how to access restricted data see:
# http://service.iris.edu/irisws/timeseries/1/
#
requestClient = "FDSN"

user          = None
password      = None
user          = 'nobody@iris.edu' # anonymous access user
password      = 'anonymous'       # anonymous access password

#
# For polynomial response (infrasound) call IRIS
#
#requestClient = "IRIS"

#
# you can read files from local disk (using filTag to point to them)
# and get the response from IRIS DMCX
#
#requestClient = "FILES"
fromFileOnly  = True # get responses from local files only. If False, will go to IRIS to get the missing responses
fileTag       = os.path.join(dataDirectory,"SAC","*.SAC")
#
##################################################################################

#
# sub-window parameters
#
nSegments      = 15  # total number of segments to calculate FFT for a window
percentOverlap = 50  # percent segment overlap
nSegWindow     = int((nSegments-1)*(1.0-float(percentOverlap)/100.0)) + 1   # number of side-by-side segments for the above nSegments and percent Overlap
                                                                       # There are (nSegments -1) non-overlaping segments and 1 full segment

#
# trace scaling for display
#
scaling = 1

#
# Units to return response in ('DIS', 'VEL' or ACC)
#
unit              = "ACC"
unitLabel         = "m/s/s"

#
# if instrument response correction is not requested, then units must be provided by user
# under generic label of "SEIS" for seismic and "INF" for infrasound
#
powerUnits        = {"M/S":"Power[10 log10(m**2/s**4/Hz)](dB)","PA":"Power[10 log10(Pascals**2/Hz)](dB)"} if performInstrumentCorrection else {"SEIS":"Power[10 log10(m**2/s**2/Hz)](dB)","INF":"Power[10 log10(Pascals**2/Hz)](dB)"}

