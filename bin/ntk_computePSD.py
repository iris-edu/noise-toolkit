version = "R 0.9.5"

################################################################################################
#
# outout usage message
#
################################################################################################
#
def usage():
   print "\n\nUSAGE for version: %s\n\n"%(version)
   print "                  configuration file name           net     sta      loc     startDateTime           endDateTime             x-axis type       0       run with minimum message output"
   print "                                  |                 |       |        |         |                        |                       |           |  plot    run in plot mode"
   print "                                  |                 |       |        |         |                        |                       |           |  time    run in timing mode (to output run time for different segments of the script "
   print "                                  |                 |       |        |         |                        |                       |           |  verbose run in verbose mode"
   print "                                  |                 |       |        |         |                        |                       |           |"
   print "     python ntk_computePSD.py     param=computePSD  net=NM sta=SLM  loc=DASH start=2009-11-01T00:00:00 end=2009-11-05T12:00:00 type=period  mode=0"
   print "     python ntk_computePSD.py     param=computePSD  net=TA sta=959A loc=EP   start=2013-10-01T11:00:00 end=2013-10-01T12:00:00 type=period  mode=1"
   print " "
   print "\n\nOUTPUT:\n\n"
   print " As file and/or plot as indicated by the configuration file. The power output file name is:"
   print " "
   print " net sta loc chan  start                    window length (s)"
   print "   |   |  |   |      |                      |    x-axis type"            
   print "   |   |  |   |      |                      |    |          "  
   print "  NM_SLM_--_BHE_2010-01-01T00:00:00.035645_3600_period.txt"
   print "\n\n\n\n"

################################################################################################
#
# get run arguments
#
################################################################################################
#
def getArgs(argList):
   args = {}
   for i in xrange(1,len(argList)):
      key,value = argList[i].split('=')
      args[key] = value
   return args

################################################################################################
#
# get a run argument for the given key
#
################################################################################################
#
def getParam(args,key,msgLib,value):
   if key in args.keys():
      return args[key]
   elif value is not None:
      return value
   else:
      msgLib.error("missing parameter "+key,1)
      usage()
      sys.exit()

################################################################################################
#
# Main
#
################################################################################################
#
# Name: ntk_computePSD.py - an ObsPy script to calculate the average power 
#       spectral density for a given station 
#
# Copyright (C) 2017  Product Team, IRIS Data Management Center
#
#    This is a free software; you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation; either version 3 of the
#    License, or (at your option) any later version.
#
#    This script is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License (GNU-LGPL) for more details.  The
#    GNU-LGPL and further information can be found here:
#    http://www.gnu.org/
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# HISTORY:
#
#    2017-01-18 Manoch: R 0.9.5 support for reading data and metadata from files only with no Internet requirement
#    2016-11-01 Manoch: R 0.9.0 support for obtaining channel responses from local station XML response files
#    2016-01-25 Manoch: R 0.8.1 support for restricted data, if user and password parameters are provided (see RestrictedData Access under http://service.iris.edu/fdsnws/dataselect/1/)
#    2015-04-07 Manoch: added check for all parameter values to inform user if they are not defined. Corrected the instrument correction for SAC files that would apply
#                       sensitivity in addition to instrument correction
#    2015-04-06 Manoch: addressed the variable maximum period issue that was changing based on the smoothing window length
#    2015-04-02 Manoch: based on feedback from Robert Anthony, in addition to nan values other non-numeric values may exist. The write that contains a flot() conversion
#                       is placed in a try block so we can catch any non-numeric conversion issue and report it as user-defined NAN
#    2015-03-30 Manoch: added a check to number of samples to aviod log of zero (reported by Rob Anthony)
#    2015-03-17 Manoch: added the "waterLevel" parameter to provide user with more control on how the ObsPy module shrinks values under water-level of max spec amplitude
#                       when removing the instrument response.
#    2015-02-24 Manoch: introduced two new parameters (performInstrumentCorrection, applyScale) to allow user avoid instrument correction also now user can turn od decon. filter
#    2014-10-22 Manoch: added support for Windows installation
#    2014-05-20 Manoch: added some informative message about data retrieval
#                       changed format to output each channel to a separate directory and save files
#                       under DOY in preparation for PQLX-type output
#    2014-03-19 Manoch: added option to read waveforms from file
#    2014-01-29 Manoch: created as part of the Noise Toolkit product
#
################################################################################################
#

#
# PACKAGES:
#
import os,sys,math,copy

#
# import the Noise Toolkit libraries
#
libraryPath      = os.path.join(os.path.dirname(__file__), '..', 'lib')
sys.path.append(libraryPath)

import msgLib  as msgLib
import fileLib as fileLib
import staLib  as staLib
import sfLib as SFL
import tsLib as TSL

args = getArgs(sys.argv)

#
# see if user has provided the run arguments
#

if len(args) < 8:
   msgLib.error("missing argument(s)",1)
   usage()
   sys.exit()

script = sys.argv[0]

#
# import the user-provided parameter file
#
# os.path.dirname(__file__) gives the current directory
#

paramFile      =  getParam(args,'param',msgLib,None)
import importlib
paramPath      = os.path.join(os.path.dirname(__file__), '..', 'param')

#
# check to see if param file exists
#
if os.path.isfile(os.path.join(paramPath,paramFile+".py")):
   sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'param'))
   param = importlib.import_module(paramFile)
else:
   msgLib.error("bad parameter file name ["+paramFile+"]",2)
   usage()
   sys.exit()

doPlot       = msgLib.param(param,'plot').plot            # display plots if requested
VERBOSE      = msgLib.param(param,'VERBOSE').VERBOSE           

#
# flag to run in verbose mode
# verbose run will take place if:
#    - VERBOSE > 0
#    OR
#    -  len(sys.argv) > 8
#
TIMING   = 0
doPlot   = 0
VERBOSE  = 0
arg = getParam(args,'mode',msgLib,'verbose')
print "MODE",arg
if arg == 'plot':
      msgLib.message("PLOT RUN")
      doPlot = 1
elif arg == 'time':
      msgLib.message("TIMING RUN")
      TIMING = 1
elif arg == 'verbose':
      msgLib.message("VERBOSE RUN")
      VERBOSE        = 1

if VERBOSE >0 :
   print "\n\n[INFO] script: %s" % script
   print "[INFO] ARG#",len(sys.argv)
   print "[INFO] ARGS",sys.argv

import matplotlib 

#
# turn off the display requirement if running without the plot option
#
if (doPlot <= 0):
   matplotlib.use('agg')

from   obspy.core import UTCDateTime, read
from   obspy.core import utcdatetime
from   datetime   import datetime
from   numpy import hanning

fromFileOnly  = msgLib.param(param,'fromFileOnly').fromFileOnly
requestClient = msgLib.param(param,'requestClient').requestClient
noInternet    = requestClient == 'FILES' and fromFileOnly
if not noInternet:
   from   obspy.clients.fdsn import Client

   #
   # IRIS Client is used for infrasound data requests
   # calling IRIS client will result in a  Deprecation Warning and should be ignored
   #
   from   obspy.clients.iris import Client as IrisClient 

from   time import time
import matplotlib.pyplot as plt
import numpy as np
import os
import scipy

#
# R 0.9.5 support for no Internet connection when fromFileOnly flag is set
#
irisClient   = None
client       = None
user         = None
password     = None
if not noInternet:
   #
   # WS clients
   #
   # if user and password parameters are provided, use them
   # R 0.8.1 support for restricted data
   #
   irisClient = IrisClient(user_agent=msgLib.param(param,'userAgent').userAgent)
   if 'user' in dir(param) and 'password' in  dir(param):
       user     = param.user
       password = param.password

   if user is None or password is None:
      print "[INFO] accessing no logon client"
      client = Client(user_agent=msgLib.param(param,'userAgent').userAgent)
   else:
      print "[INFO] accessing logon client as",user
      client = Client(user_agent=msgLib.param(param,'userAgent').userAgent,user=user,password=password)
else:
   print "[INFO] data and metadata from files"



action = "" # keep track of what you are doing

#
# RUN ARGUMENTS:
#
t0             = time()
t1 = fileLib.timeIt("START",t0)
print "\n"
msgLib.message("START")


inNetwork      = getParam(args,'net',msgLib,None)
inStation      = getParam(args,'sta',msgLib,None)
inLocation     = staLib.getLocation(getParam(args,'loc',msgLib,None))
inChannel      = getParam(args,'chan',msgLib,msgLib.param(param,'channel').channel)

maxPeriod      = msgLib.param(param,'maxT').maxT * pow(2,msgLib.param(param,'octaveWindowWidth').octaveWindowWidth/2.0)    # maximum period needed to compute value at maxT period point
minFrequency   = 1.0/float(maxPeriod)                               # minimum frequency  needed to compute value at 1.0/maxT frequency point
if TIMING >0 :
   t0 = fileLib.timeIt("ARTGS",t0)

if VERBOSE >0 :
   print "[INFO] MAX PERIOD: "+str(msgLib.param(param,'maxT').maxT)
   print "[INFO] CALL: "+str(sys.argv)

inventory = None
respDir   = None
respDir   = msgLib.param(param,'respDirectory').respDirectory

#
# less than 3 characters station name triggers wildcard
#

if(len(inStation) <= 2):
   if requestClient == "IRIS":
      msgLib.error("invalid station name (for IRIS client, wildcards are not accepted. Please use full station name)",2)
      sys.exit()
      
   inStation = "*" + inStation + "*"

#
# specific start and end date and times from user
#
requestStartDateTime = getParam(args,'start',msgLib,None)
requestEndDateTime   = getParam(args,'end',msgLib,None)
   
if TIMING >0 :
   t0 = fileLib.timeIt('requet info',t0)

print "\n[INFO] requesting "+inNetwork+"."+inLocation+"."+inStation+"."+inChannel+" "+requestStartDateTime+"  to  "+requestEndDateTime

#
# processing parameters
#
xType   = getParam(args,'type',msgLib,msgLib.param(param,'xType').xType[0])   # what the x-axis should represent
try:
   plotIndex = msgLib.param(param,'xType').xType.index(xType)
except Exception, e:
   print str(e)
   msgLib.error("invalid plot type ("+xType+")",2)
   usage()
   sys.exit()

if TIMING >0 :
   t0 = fileLib.timeIt('parameters',t0)

if VERBOSE >0 :
   print "[INFO] Window From - To: "+str(utcdatetime.UTCDateTime(requestStartDateTime))+" - "+str(utcdatetime.UTCDateTime(requestEndDateTime))+"\n"

#
# window duration
#
try:
   duration = int(utcdatetime.UTCDateTime(requestEndDateTime) - utcdatetime.UTCDateTime(requestStartDateTime)) 
except Exception, e:
   print str(e)
   msgLib.error("invalid date-time ["+requestStartDateTime+"-"+requestEndDateTime+"]",1)
   usage()
   sys.exit()

if TIMING >0 :
   t0 = fileLib.timeIt('window info',t0)

if VERBOSE >0 :
   print "PLOTINDEX:",plotIndex
   print "[INFO] Window Duration: "+str(duration)+"\n"
   print "[PAR] XLABEL:",msgLib.param(param,'xlabel').xlabel[xType]
   print "[PAR] XLIM(",msgLib.param(param,'xlimMin').xlimMin,",",msgLib.param(param,'xlimMax').xlimMax,")"
   print "[PAR] YLIM(",msgLib.param(param,'ylimLow').ylimLow,",",msgLib.param(param,'ylimHigh').ylimHigh,")"

#
# request date information
#
try:
   year, week , weekday = utcdatetime.UTCDateTime(requestStartDateTime).isocalendar()
except Exception, e:
   print str(e)
   msgLib. error("invalid start date-time ["+requestStartDateTime+"]",1)
   usage()
   sys.exit()


############################################## CODE ##############################################
#
# get the data
#
requestNetwork    = copy.copy(inNetwork)
requestStation    = copy.copy(inStation)
requestLocation   = copy.copy(inLocation)
requestChannel    = copy.copy(inChannel)

#
# start processing time segments
#
startDateTime = copy.copy(requestStartDateTime)
endDateTime   = copy.copy(requestEndDateTime)

#
# work on each window duration (1-hour)
#
# LOOP: WINDOW
#
for tStep in xrange(0,duration,msgLib.param(param,'windowShift').windowShift):

   if TIMING:
      t0 = fileLib.timeIt('start WINDOW',t0)

   tStart            = UTCDateTime(requestStartDateTime)+tStep
   tEnd              = tStart + msgLib.param(param,'windowLength').windowLength
   segmentStart      = tStart.strftime("%Y-%m-%d %H:%M:%S.0")
   segmentStartYear  = tStart.strftime("%Y")
   segmentStartDOY   = tStart.strftime("%j")
   segmentEnd        = tEnd.strftime("%Y-%m-%d %H:%M:%S.0")

   if requestClient == "FILES":
      print "[INFO] reading " + fileLib.getTag(".",[requestNetwork, requestStation, requestLocation, requestChannel]) + " from " + segmentStart + " to " + segmentEnd + " from " + msgLib.param(param,'requestClient').requestClient
   else:
      print "[INFO] requesting " + fileLib.getTag(".",[requestNetwork, requestStation, requestLocation, requestChannel]) + " from " + segmentStart + " to " + segmentEnd + " from " + msgLib.param(param,'requestClient').requestClient

   #
   # get channel stream + detrend
   # TSL.getChannelWaveform removes the linear trend from trace
   #
   try:
      #
      # request via IRIS WS -- often done for non-standard instrument correction
      #
      if TIMING:
         t0 = fileLib.timeIt('requesting WAVEFORM',t0)

      if requestClient == "IRIS":
         stream = TSL.getIrisChannelWaveform (requestNetwork, requestStation, requestLocation, requestChannel,
                     segmentStart,segmentEnd,1,msgLib.param(param,'performInstrumentCorrection').performInstrumentCorrection,msgLib.param(param,'applyScale').applyScale,
                     msgLib.param(param,'deconFilter1').deconFilter1, msgLib.param(param,'deconFilter2').deconFilter2, msgLib.param(param,'deconFilter3').deconFilter3, 
                     msgLib.param(param,'deconFilter4').deconFilter4, msgLib.param(param,'unit').unit,irisClient)
      #
      # read from files but request response via Files and/or WS
      #
      elif requestClient == "FILES":
         useClient = client
         if noInternet:
            useClient = None
         inventory,stream = TSL.getChannelWaveformFiles (requestNetwork, requestStation, requestLocation, requestChannel,
                     segmentStart,segmentEnd,1,msgLib.param(param,'performInstrumentCorrection').performInstrumentCorrection,msgLib.param(param,'applyScale').applyScale,
                     msgLib.param(param,'deconFilter1').deconFilter1, msgLib.param(param,'deconFilter2').deconFilter2, msgLib.param(param,'deconFilter3').deconFilter3,
                     msgLib.param(param,'deconFilter4').deconFilter4, msgLib.param(param,'waterLevel').waterLevel, msgLib.param(param,'unit').unit,useClient,msgLib.param(param,'fileTag').fileTag, respdir = respDir, inventory = inventory)

      #
      # request via FDSN WS 
      #
      else:
         stream = TSL.getChannelWaveform (requestNetwork, requestStation, requestLocation, requestChannel,
                     segmentStart,segmentEnd,1,msgLib.param(param,'performInstrumentCorrection').performInstrumentCorrection,msgLib.param(param,'applyScale').applyScale,
                     msgLib.param(param,'deconFilter1').deconFilter1, msgLib.param(param,'deconFilter2').deconFilter2, msgLib.param(param,'deconFilter3').deconFilter3, 
                     msgLib.param(param,'deconFilter4').deconFilter4, msgLib.param(param,'waterLevel').waterLevel, msgLib.param(param,'unit').unit,client)

      if stream is None or len(stream) <= 0:
         msgLib.warning('Channel Waveform','No data available for '+ '.'.join([requestNetwork,requestStation,requestLocation,requestChannel]))
         continue
   except Exception, e:
      print str(e)
      print "[INFO] waveform request failed\n"
      continue
  
   traceKeyList = []
   for streamIndex in xrange(len(stream)):
     frequency   = []
     period      = []
     power       = []
     stChannel = None

     trChannel  = stream[streamIndex] 
     network    = trChannel.stats.network
     station    = trChannel.stats.station
     location   = staLib.getLocation(trChannel.stats.location)
     channel    = trChannel.stats.channel
     if VERBOSE:
        print "[INFO] response: ",trChannel.stats
     if channel == "BDF":
        powerUnits = msgLib.param(param,'powerUnits').powerUnits["PA"]
     else: 
        if msgLib.param(param,'performInstrumentCorrection').performInstrumentCorrection:
            powerUnits = msgLib.param(param,'powerUnits').powerUnits[trChannel.stats.response.instrument_sensitivity.input_units]
        else:
            powerUnits = msgLib.param(param,'powerUnits').powerUnits["SEIS"]
     xUnits     = msgLib.param(param,'xlabel').xlabel[xType.lower()]
     traceKey = fileLib.getTag(".",[network,station,location,channel])

     #
     # if there is a gap, we only proicess the first segment
     #
     if traceKey in traceKeyList:
         continue
     else:
         traceKeyList.append(traceKey)

     if TIMING:
        t0 = fileLib.timeIt('got WAVEFORM',t0)

     if VERBOSE:
        print "[INFO] processing" ,traceKey,"\n"

     #
     # parameters
     #
     nPoints = trChannel.stats.npts
     samplingFrequency = trChannel.stats.sampling_rate
     delta = float(trChannel.stats.delta)

     #
     # construct the time array
     #
     traceTime = np.arange(nPoints) / samplingFrequency

     if TIMING:
        t0 = fileLib.timeIt('build trace timr',t0)

     if VERBOSE:
        print "[INFO] got number of points as " + str(nPoints) + "\n"
        print "[INFO] got sampling frequency as " + str(samplingFrequency) + "\n"
        print "[INFO] got sampling interval as " + str(delta) + "\n"
        print "[INFO] got time as " + str(traceTime) + "\n"
  
     #
     # calculate FFT parameters
     #
     # number of samples per window is obtained by dividing the total number of samples
     # by the number of side-by-side time windows along the trace 
     #

     #
     # first calculate the number of points needed based on the run parameters
     #
     thisNSamp = int((float(msgLib.param(param,'windowLength').windowLength) / delta +1)/msgLib.param(param,'nSegWindow').nSegWindow)
     nSampNeeded  = 2**int(math.log(thisNSamp, 2)) # make sure it is power of 2
     if VERBOSE:
        print "nSamp Needed:",nSampNeeded

     #
     # next calculate the number of points needed based on the trace parameters
     #
     thisNSamp = int(nPoints/msgLib.param(param,'nSegWindow').nSegWindow)
     
     #
     # avoid log of bad numbers
     #
     if thisNSamp <= 0:
        msgLib.warning("FFT","needed "+str(nSampNeeded)+" smples but no samples are available, will skip this trace")
        continue
     nSamp  = 2**int(math.log(thisNSamp, 2)) # make sure it is power of 2
     if VERBOSE:
        print "nSamp Available:",nSamp

     if nSamp < nSampNeeded:
        msgLib.warning("FFT","needed "+str(nSampNeeded)+" smples but only "+str(nSamp)+" samples are available, will skip this trace")
        continue

     nShift = int(nSamp * (1.0 - float(msgLib.param(param,'percentOverlap').percentOverlap) / 100.0))

     if VERBOSE:
        print "[INFO] FFT msgLib.param(param,'nSegWindow').nSegWindow,nSamp,nShift: ",msgLib.param(param,'nSegWindow').nSegWindow,nSamp,nShift

     #
     # initialize the spectra 
     # The size of m11 is half of the mSamp, as data are real and
     # and we only need the positive frequency portion
     #
     action = "initialize the spectra"
     m11 = np.zeros((nSamp/2)+1,dtype=np.complex)

     #
     # build the tapering window
     #
     action = "taper"
     taperWindow = np.hanning(nSamp)

     #
     # loop through windows and calculate the spectra
     #
     action = "loop"
     startIndex = 0
     endIndex   = 0

     #
     # go through segment
     #
     if VERBOSE:
        print "nSamp",nSamp
        print "DELTA:",delta,"\n\n"

     nSegCount = 0
     for n in xrange(0,msgLib.param(param,'nSegments').nSegments):
        if TIMING:
           t0 = fileLib.timeIt('segment '+str(n),t0)

        #
        # each segment srats at startIndex and ends at endIndex-1
        #
        endIndex       = startIndex + nSamp

        if VERBOSE:
           print "STARTINDEX",startIndex
           print "ENDINDEX",endIndex

        timeSegment    = []
        channelSegment = []
 
        #
        # extract the segments
        # using Welch's method. Segments are length nSamp with each segment
        # int(nSamp * (1.0-(param.percentOverlap / 100))) units apart
        #
        action = "extract the segments"
        try:
           #
           # load startIndex through endIndex - 1
           #
           if VERBOSE:
              print "TIME SEGMENT",startIndex,endIndex,traceTime[startIndex],traceTime[endIndex]
           timeSegment    = traceTime[startIndex:endIndex]

           if VERBOSE:
              print "CHANNEL SEGMENT",startIndex,endIndex
           channelSegment = trChannel.data[startIndex:endIndex]
	   nSegCount += 1

           #if VERBOSE:
           #   SI = int(((timeSegment[0]-traceTime[0])/delta)+0.5)
           #   print "startIndex,SI:",startIndex,SI
        except Exception, e:
           print str(e)
           msgLib. error("failed to extract segment from location "+str(startIndex)+" to "+str(endIndex)+"\n",0)
           sys.exit()

        #
        # remove the mean
        #
        action         = "remove mean"
        channelSegment = channelSegment - np.mean(channelSegment)

        #
        # apply the taper
        #
        action         = "apply the taper"
        if VERBOSE:
           print action,len(channelSegment),len(taperWindow)
        channelSegment = channelSegment * taperWindow

        #
        # FFT
        # data values are real, so the output of FFT is Hermitian symmetric, 
        # i.e. the negative frequency terms are just the complex conjugates of 
        # the corresponding positive-frequency terms
        # We only need the frist half, so doing np.fft.rfft is more efficient
        #
             
        if TIMING:
           t0 = fileLib.timeIt('start FFT ',t0)

        action     = "FFT"
        FFT        = np.zeros((nSamp/2)+1, dtype=np.complex)
        FFT        = np.fft.rfft(channelSegment)

        #
        # power
        #
        action = "power"
        m11 += FFT[0:(nSamp/2)+1] * np.conjugate(FFT[0:(nSamp/2)+1])

        if TIMING:
           t0 = fileLib.timeIt('got POWER ',t0)
          
        #
        # shift the start index for the next segment with overlap
        #
        action = "shift the start index"
        startIndex += nShift

        #
        ######## Plot the waveform and the selected segment ########
        #
        if msgLib.param(param,'plotTraces').plotTraces > 0 and doPlot > 0:
           action = "Plot"
           plt.subplot(111)
           plt.plot(traceTime, trChannel.data, msgLib.param(param,'colorTrace').colorTrace)
           plt.plot(timeSegment, channelSegment, msgLib.param(param,'colorSmooth').colorSmooth)
           plt.ylabel(channel+' ['+msgLib.param(param,'unitLabel').unitLabel[channel]+']')
           plt.xlim(0,msgLib.param(param,'windowLength').windowLength)
           plt.xlabel('Time [s]')
           plt.show()

     #
     # END LOOP SEGMENT, segments are done
     #

     #
     # average the spectra matrix over the subwindows
     #
     action = "average the spectra matrix"

     #
     # to convert FFT to PSD
     #
     # The power based on the FFT values (X) 
     # This power is calculated over Nyquist 1/(2*dt) and we have N equispaced frequency samples. Therefore:
     # PSD = (X^2)/ [1/(2*dt)] / N
     # PSD = (X^2 * 2 * dt / N) 
     #
     norm  = 2.0 * delta /  float(nSamp)
     norm *= msgLib.param(param,'normFactor').normFactor
     if VERBOSE:
        print "\n\nDELTA:",delta
        print "NSAMP:",nSamp
        print "NORM:",norm

     if VERBOSE:
        print "DELTA: "+str(delta)+"\n"
        print "nSegCount: "+str(nSegCount)+"\n\n"

     #
     # average
     #
     m11      /= float(nSegCount)
     power     = norm * np.abs(m11[0:(nSamp/2)+1])

     #
     # if power is not populated, skip LOOP WINDOW or this 1 -hour window
     #
     if len(power) <= 0:
        continue
 
             
     smoothX    = []
     smoothPSD  = []

     #
     # smoothing
     #
     if TIMING:
        t0 = fileLib.timeIt('start SMOOTHING ',t0)

     print "[INFO] SMOOTHING window "+str(msgLib.param(param,'octaveWindowWidth').octaveWindowWidth)+" shift "+str(msgLib.param(param,'octaveWindowShift').octaveWindowShift)
     if xType == "period":
        #
        # 10.0*maxT to avoid 1.0/0.0 at zero frequency
        #
        period    = np.append([10.0*msgLib.param(param,'maxT').maxT],1.0/(np.arange(1.0,(nSamp/2)+1)/float(nSamp * delta)))
        if str(msgLib.param(param,'xStart').xStart[plotIndex]) == 'Nyquist':
           smoothX,smoothPSD       = SFL.smoothNyquist(xType,period,power,samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT)
        else:
           smoothX,smoothPSD       = SFL.smoothT(period,power,samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,float(msgLib.param(param,'xStart').xStart[plotIndex]))
     else:
        frequency = np.array( np.arange(0,(nSamp/2)+1)/float(nSamp * delta))

        if str(msgLib.param(param,'xStart').xStart[plotIndex]) == 'Nyquist':
           smoothX,smoothPSD       = SFL.smoothNyquist(xType,frequency,power,samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency)
        else:
           smoothX,smoothPSD       = SFL.smoothF(frequency,power,samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,float(msgLib.param(param,'xStart').xStart[plotIndex]))

     if TIMING:
        t0 = fileLib.timeIt("SMOOTHING window "+str(msgLib.param(param,"octaveWindowWidth").octaveWindowWidth)+" shift "+str(msgLib.param(param,"octaveWindowShift").octaveWindowShift)+" DONE",t0)

     #
     # convert to dB
     #
     power     = 10.0 * np.log10(power[0:(nSamp/2)+1])
     smoothPSD = 10.0 * np.log10(smoothPSD)

     #
     # create output paths if they do not exist
     #
     if msgLib.param(param,'outputValues').outputValues > 0:
        filePath, psdFileTag = fileLib.getDir(msgLib.param(param,'dataDirectory').dataDirectory,msgLib.param(param,'psdDbDirectory').psdDbDirectory,network,station,location,channel)
        filePath = os.path.join(filePath,segmentStartYear,segmentStartDOY)
        fileLib.makePath(filePath)

        #
        # output is based on the xType
        #
        if VERBOSE:
           print "trChannel.stats:",str(trChannel.stats)
           print "REQUEST:",segmentStart
           print "TRACE:",str(trChannel.stats.starttime).replace("Z","")
           print "DELTA:",trChannel.stats.delta
           print "SAMPLES:",int(float(msgLib.param(param,'windowLength').windowLength)/float(trChannel.stats.delta) +1)

        tagList = [psdFileTag,str(trChannel.stats.starttime).replace("Z",""),str(msgLib.param(param,'windowLength').windowLength),xType]
        with open(fileLib.getFileName(msgLib.param(param,'namingConvention').namingConvention,filePath,tagList), "w") as file:

           #
           # Header
           #
           file.write("%s %s\n" % (xUnits,powerUnits))

           #
           # data
           #
           for i in xrange(0,len(smoothX)):
               file.write("%11.6f %11.4f\n" % (float(smoothX[i]),float(smoothPSD[i])))

        file.closed

     #
     ######## Plot ########
     #
     if (msgLib.param(param,'plotSpectra').plotSpectra > 0 or msgLib.param(param,'plotSmooth').plotSmooth>0) and doPlot>0:
        action = "Plot 2"

        if TIMING:
           t0 = fileLib.timeIt('start PLOT ',t0)

        if VERBOSE:
           print "POWER: "+str(len(power))+"\n"

        fig = plt.figure()
        fig.subplots_adjust(hspace=.2)
        fig.subplots_adjust(wspace=.2)
        fig.set_facecolor('w')

        ax311 = plt.subplot(111)
        ax311.set_xscale('log')

        #
        # period for the x-axis
        #
        if xType == "period":
           if msgLib.param(param,'plotSpectra').plotSpectra:
              plt.plot(period, power, msgLib.param(param,'colorSpectra').colorSpectra)
           if msgLib.param(param,'plotSmooth').plotSmooth:
              plt.plot(smoothX, smoothPSD, color=msgLib.param(param,'colorSmooth').colorSmooth, lw=3)

        #
        # frequency for the x-axis
        #
        else:
           if msgLib.param(param,'plotSpectra').plotSpectra:
              plt.plot(frequency, power, msgLib.param(param,'colorSpectra').colorSpectra)
           if msgLib.param(param,'plotSmooth').plotSmooth:
              plt.plot(smoothX, smoothPSD, color=msgLib.param(param,'colorSmooth').colorSmooth, lw=3)

        plt.xlabel(xUnits)
        plt.xlim(msgLib.param(param,'xlimMin').xlimMin[channel][plotIndex],msgLib.param(param,'xlimMax').xlimMax[channel][plotIndex])
        plt.ylabel(channel + " " + powerUnits)
        plt.ylim([msgLib.param(param,'ylimLow').ylimLow[channel],msgLib.param(param,'ylimHigh').ylimHigh[channel]])
        plt.title(station+" from "+segmentStart+" to "+segmentEnd)

        if TIMING:
           t0 = fileLib.timeIt('show PLOT ',t0)

        plt.show()
t0 = t1
print " "
t0 = fileLib.timeIt("END",t0)
print " "
