import os
import shared

# PSD database directory where individual PSD files are stored.
psdDbDirectory = shared.psdDbDirectory

# Directory paths for data and responses.
dataDirectory = shared.dataDirectory
respDirectory = shared.respDirectory

# UserAgent is used to collect statistics on data requests, please change if desired.
userAgent = 'product_pub_noise-toolkit_psd'

# How the file naming is done ('WINDOWS' or 'PQLX').
namingConvention = shared.namingConvention

# Initialize a few parameters (0/1).
verbose = 0

# Run in the timing mode (0/1, 1: to output run times for different segments of the script).
timing = 0

# Turn plotting on or off (1/0).
plot = 0

# Plot spectra (0/1)?
plotSpectra = 1

# Plot Peterson's New LNM and HNM.
plotNm = 1

# Spectra plot color.
colorSpectra = 'tab:blue'

# Plot the smoothed spectra (0/1)?
plotSmooth = 1

# smoothed spectra color.
colorSmooth = 'tab:red'

# Output the smoothed values.
outputValues = 1

# Smoothing window width in octave.
# For test against PQLX use 1 octave width.

# Smoothing window width : float(1.0/1.0)= 1 octave smoothing;
# float(1.0/4.0) 1/4 octave smoothing, etc.
octaveWindowWidth = 1.0/4.0

# Smoothing window shift : float(1.0/4.0)= 1/4 octave shift;
# float(1.0/8.0) 1/8 octave shift, etc.
octaveWindowShift = 1.0/8.0

# Plot x-axis type.
xtype = ['period', 'frequency']

# Smoothing starting frequency/period reference (Nyquist= Nyquist frequency, 1= 1Hz/1Sec).
xStart = ['Nyquist', 'Nyquist']

# Plot x-axis label.
xlabel = {'period': 'Period (s)', 'frequency': 'Frequency (Hz)'}

# Plot maximum period.
maxT = 200

# Plot the New Low Noise Model.
# For information on New High/Low Noise Model see [Peterson, 1993]
plotnnm = 1

# Seconds, sub-windows of the above window for processing.
windowLength = 3600

# Only process segments that start at the beginning of the window.
enforceWindowStart = False

# Window shift as a percent of the window length (0.5 = 50% overlap).
windowShift = int(windowLength * 0.5)

# Channels to process.
channel = 'BH?'
# channel = 'BDF'

# Plot parameters for xtype ['period', 'frequency'].
ylimLow = {'LHZ': -200, 'LHN': -200, 'LHE': -200,
           'LH1': -200, 'LH2': -200, 
           'BHZ': -200, 'BHN': -200, 'BHE': -200, 
           'BH1': -200, 'BH2': -200,
           'HHZ': -200, 'HHN': -200, 'HHE': -200,
           'HH1': -200, 'HH2': -200,
           'BDF': -80}
ylimHigh = {'LHZ': -100, 'LHN': -100, 'LHE': -100, 'LH1': -50, 'LH2': -50,
            'BHZ': -100, 'BHN': -100, 'BHE': -100, 'BH1': -50, 'BH2': -50,
            'HHZ': -100, 'HHN': -100, 'HHE': -100, 'HH1': -50, 'HH2': -50, 
            'BDF': 50}
xlimMin = {'LHZ': [5.0, 0.01], 'LHN': [5.0, 0.01], 'LHE': [5.0, 0.01], 'LH1': [5.0, 0.01], 'LH2': [5.0, 0.01],
           'BHZ': [0.05, 0.01], 'BHN': [0.05, 0.01], 'BHE': [0.05, 0.01], 'BH1': [0.05, 0.01], 'BH2': [0.05, 0.01],
           'HHZ': [1.0, 0.01], 'HHN': [1.0, 0.01], 'HHE': [1.0, 0.01], 'HH1': [1.0, 0.01], 'HH2': [1.0, 0.01],
           'BDF': [0.05, 0.01]}
xlimMax = {'LHZ': [100.0, 1.0], 'LHN': [100.0, 1.0], 'LHE': [100.0, 1.0], 'LH1': [100.0, 1.0],
           'BHZ': [100.0, 20.0], 'BHN': [100.0, 20.0], 'BHE': [100.0, 20.0], 'BH1': [100.0, 20.0], 'BH2': [100.0, 20.0],
           'HHZ': [100.0, 20.0], 'HHN': [100.0, 20.0], 'HHE': [100.0, 20.0], 'HH1': [100.0, 20.0], 'HH2': [100.0, 20.0],
           'BDF': [100.0, 20.0]}

""" The requestClient to call to get the waveforms from (FDSN, IRIS or FILES). 
For the restricted data access, you need user and password information. For information on how to access 
restricted data see:
     http://service.iris.edu/irisws/timeseries/1/
"""
user = 'nobody@iris.edu'  # anonymous access user
password = 'anonymous'  # anonymous access password

"""  You can also read files from local disk (using filTag to point to them)
and get the response from IRIS DMC.
"""
# 'FDSN' or 'FILES'
requestClient = 'FDSN'
fromFileOnly = False  # get responses from local files only. If False, will go to IRIS to get the missing responses
fileTag = os.path.join(dataDirectory, 'SAC', '*.SAC')

# The sub-window parameters.
nSegments = 15  # total number of segments to calculate FFT for a window
percentOverlap = 50  # percent segment overlap

# The number of side-by-side segments for the above nSegments and percent Overlap
# There are (nSegments -1) non-overlapping segments and 1 full segment.
nSegWindow = int((nSegments - 1) * (1.0 - float(percentOverlap) / 100.0)) + 1

# Trace scaling for display.
scaling = 1

# Units to return response in ('DIS', 'VEL' or ACC).
unit = 'ACC'

# If instrument response correction is not requested, then units must be provided by user
# under generic label of 'SEIS' for seismic and 'INF' for infrasound.
powerUnits = {'M/S': 'Power[10 log10(m**2/s**4/Hz)](dB)', 'm/s': 'Power[10 log10(m**2/s**4/Hz)](dB)',
              'PA': 'Power[10 log10(Pascals**2/Hz)](dB)'}
