version = "R 0.6.5"

################################################################################################
#
# outout usage message
#
################################################################################################
#
def usage():
   print "\n\nUSAGE for version: %s\n\n"%(version)
   print "                                         configuration file name           net     sta      loc     startDateTime           endDateTime             x-axis type       0       run with minimum message output"
   print "                                                         |                 |       |        |         |                        |                       |           |  plot    run in plot mode"
   print "                                                         |                 |       |        |         |                        |                       |           |  time    run in timing mode (to output run time for different segments of the script "
   print "                                                         |                 |       |        |         |                        |                       |           |  verbose run in verbose mode"
   print "                                                         |                 |       |        |         |                        |                       |           |"
   print "     python ntk_computePolarization.py     param=computePolarization  net=NM sta=SLM  loc=DASH start=2009-11-01T00:00:00 end=2009-11-05T12:00:00 type=period  mode=0"
   print " "
   print "\n\nOUTPUT:\n\n"
   print " As file and/or plot as indicated by the configuration file. The polarization output file name is:"
   print " "
   print " net sta loc chan  start                window length (s)"
   print "   |   |  |   |      |                  |    x-axis type"            
   print "   |   |  |   |      |                  |    |          "  
   print "  NM.SLM.--.2010-01-01T00:00:00.035645.3600.period.txt if namingConvention parameter = 'PQLX' "
   print "  NM.SLM.--.2010-01-01T00_00_00.035645.3600.period.txt if namingConvention parameter = 'WINDOWS' "
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
# Name: ntk_computePolarization.py - an ObsPy script to calculate polarization parameters
#       for a given station 
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
#    2017-01-18 Manoch: R 0.6.5 support for reading data and metadata from files only with no Internet requirement
#    2016-11-01 Manoch: R 0.6.0 support for obtaining channel responses from local station XML response files
#    2016-01-25 Manoch: R 0.5.1 added support for accessing restricted data via user and password
#    2015-09-02 Manoch: R0.5 ready for release
#    2015-06-16 Manoch: updated based on the latest ntk_computePSD.py
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
from numpy import linalg as eigen

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
import polarLib as PL

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
if arg == 'plot':
      doPlot = 1
elif arg == 'time':
      TIMING = 1
elif arg == 'verbose':
      VERBOSE        = 1
else:
     arg = 'normal'
print "\n[INFO] MODE:",arg

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
from   time import time
import matplotlib.pyplot as plt
import numpy as np
import os
import scipy

#
# WS clients
#
# if user and password parameters are provided, use them
# R 0.5.1 support for restricted data
# R 0.6.5 support for no Internet connection when fromFileOnly flag is set
#
user     = None
password = None
client   = None

fromFileOnly  = msgLib.param(param,'fromFileOnly').fromFileOnly
requestClient = msgLib.param(param,'requestClient').requestClient
noInternet    = requestClient == 'FILES' and fromFileOnly
if not noInternet:
   from   obspy.clients.fdsn import Client
   if 'user' in dir(param) and 'password' in  dir(param):
       user     = param.user
       password = param.password

   if user is None or password is None:
      print "[INFO] accessing no logon client"
      client = Client(user_agent=msgLib.param(param,'userAgent').userAgent)
   else:
      print "[INFO] accessing logon client using",user
      client = Client(user_agent=msgLib.param(param,'userAgent').userAgent, user=user, password=password)
else:
   print "[INFO] reading data and metadata from files"

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
inChannel      = getParam(args,'channel',msgLib,msgLib.param(param,'channel').channel)
#channelItems   = inChannel.split(',')
#if len(channelItems) != 3:
#    msgLib.error("invalid channel list ('+inChannel+') must be Z,N,E",1)
#    sys.exit()

inventory = None
respDir   = None
respDir   = msgLib.param(param,'respDirectory').respDirectory
#
# get a sorted list of valid channels to be used for stream QC later
#
try:
   sortedChannelList = [] 
   for i in xrange(len(param.channelGroups)):
      sortedChannelList.append(sorted(param.channelGroups[i]))
except Exception, e:
   print str(e)
   msgLib.error("check the channelGroups parameter in the parameter file",2)
   sys.exit()

maxPeriod      = msgLib.param(param,'maxT').maxT * pow(2,msgLib.param(param,'octaveWindowWidth').octaveWindowWidth/2.0)    # maximum period needed to compute value at maxT period point
minFrequency   = 1.0/float(maxPeriod)                               # minimum frequency  needed to compute value at 1.0/maxT frequency point
if TIMING >0 :
   t0 = fileLib.timeIt("ARTGS",t0)

if VERBOSE >0 :
   print "[INFO] MAX PERIOD:",msgLib.param(param,'maxT').maxT,' s'
   print "[INFO] CALL: ",sys.argv

#
# less than 3 characters station name triggers wildcard
#

if(len(inStation) <= 2):
   inStation = "*" + inStation + "*"

#
# specific start and end date and times from user
#
requestStartDateTime = getParam(args,'start',msgLib,None)
requestEndDateTime   = getParam(args,'end',msgLib,None)
   
if TIMING >0 :
   t0 = fileLib.timeIt('requet info',t0)

print "\n[INFO]",'network:',inNetwork,"station:",inStation,"location:",inLocation,"channel:",inChannel,"start:",requestStartDateTime,"end:",requestEndDateTime

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
   print "[INFO] Window Duration:",duration,"s\n"
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

   title = " ".join([fileLib.getTag(".",[requestNetwork, requestStation, requestLocation]),requestChannel,"from",segmentStart," to",segmentEnd ])
   if msgLib.param(param,'requestClient').requestClient == "FILES":
      print "[INFO] reading", fileLib.getTag(".",[requestNetwork, requestStation, requestLocation]), requestChannel, " from", segmentStart , "to", segmentEnd, "from", msgLib.param(param,'requestClient').requestClient
   else:
      print "\n[INFO] requesting", fileLib.getTag(".",[requestNetwork, requestStation, requestLocation]), requestChannel, segmentStart, "to", segmentEnd , "from" , msgLib.param(param,'requestClient').requestClient

   #
   # get channel stream + detrend
   # TSL.getChannelWaveform removes the linear trend from trace
   #
   try:
      if TIMING:
         t0 = fileLib.timeIt('requesting WAVEFORM',t0)

      #
      # read from files but request response via Files and/or WS
      #
      if requestClient == "FILES":
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

      #
      # did we manage to get the data?
      #
      if stream is None or len(stream) <= 0:
         msgLib.warning('Channel Waveform','No data available for '+ '.'.join([requestNetwork,requestStation,requestLocation,requestChannel]))
         continue
      else:
         qcRecords = TSL.qc3Stream(stream,param.windowLength,msgLib.param(param,'nSegWindow').nSegWindow,sortedChannelList,param.channelGroups,VERBOSE)
         if VERBOSE:
            print "[INFO] stream length: ",len(stream),'s'
            print "[INFO] QC-passed records:",qcRecords

   except Exception, e:
      print str(e)
      print "[WARN] waveform request failed\n"
      continue
  
   traceKeyList = []
   traceChannel = [None,None,None]
   channel      = [None,None,None]
   nPoints      = [None,None,None]
   for streamIndex in qcRecords:
     if VERBOSE:
        print "[INFO] processing records:",streamIndex

     frequency   = []
     period      = []
     stChannel   = None

     #
     # get traces for the 3 channels
     #
     trChannel1  = stream[streamIndex[0]]
     channel1    = trChannel1.stats.channel
     trChannel2  = stream[streamIndex[1]]
     channel2    = trChannel2.stats.channel
     trChannel3  = stream[streamIndex[2]]
     channel3    = trChannel3.stats.channel

     #
     # net, sta, loc should be the same, get them from the 1st channel
     #
     network    = trChannel1.stats.network
     station    = trChannel1.stats.station
     location   = staLib.getLocation(trChannel1.stats.location)

     if VERBOSE:
        print "[INFO] received: \nCHANNEL 1\n",trChannel1.stats
        print "[INFO] received: \nCHANNEL 2\n",trChannel2.stats
        print "[INFO] received: \nCHANNEL 3\n",trChannel3.stats

     if msgLib.param(param,'performInstrumentCorrection').performInstrumentCorrection:
         powerUnits = msgLib.param(param,'powerUnits').powerUnits[trChannel1.stats.response.instrument_sensitivity.input_units]
     else:
         powerUnits = msgLib.param(param,'powerUnits').powerUnits["SEIS"]

     xUnits     = msgLib.param(param,'xlabel').xlabel[xType.lower()]
     header     = msgLib.param(param,'header').header[xType.lower()]

     #
     # create a or each channel
     #
     traceKey1  = fileLib.getTag(".",[network,station,location,channel1])
     traceKey2  = fileLib.getTag(".",[network,station,location,channel2])
     traceKey3  = fileLib.getTag(".",[network,station,location,channel3])
     channelTag = '_'.join([channel1,channel2,channel3])

     if VERBOSE:
        print "\n[INFO] processing" ,traceKey1,traceKey2,traceKey3,"\n"

     if TIMING:
        t0 = fileLib.timeIt('got WAVEFORM',t0)

     #
     # get the shortest trace length
     #
     nPoints = np.min([trChannel1.stats.npts,trChannel2.stats.npts,trChannel3.stats.npts])

     #
     # sampling should be the same, get it from the 1st channel
     #
     samplingFrequency     = trChannel1.stats.sampling_rate
     delta                 = float(trChannel1.stats.delta)

     #
     # construct the time array
     #
     traceTime = np.arange(nPoints) / samplingFrequency

     if TIMING:
        t0 = fileLib.timeIt('build trace timr',t0)

     if VERBOSE:
        print "[INFO] got number of points as", nPoints, "\n"
        print "[INFO] got sampling frequency as", samplingFrequency, "\n"
        print "[INFO] got sampling interval as ", delta, "\n"
        print "[INFO] got time as ", traceTime, "\n"
  
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
     print "[INFO] nSamp Needed:",nSampNeeded

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
     print "[INFO] nSamp Available:",nSamp

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
     m12 = np.zeros((nSamp/2)+1,dtype=np.complex)
     m13 = np.zeros((nSamp/2)+1,dtype=np.complex)
     m22 = np.zeros((nSamp/2)+1,dtype=np.complex)
     m23 = np.zeros((nSamp/2)+1,dtype=np.complex)
     m33 = np.zeros((nSamp/2)+1,dtype=np.complex)

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
           channelSegment1 = trChannel1.data[startIndex:endIndex]
           channelSegment2 = trChannel2.data[startIndex:endIndex]
           channelSegment3 = trChannel3.data[startIndex:endIndex]
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
        channelSegment1 = channelSegment1 - np.mean(channelSegment1)
        channelSegment2 = channelSegment2 - np.mean(channelSegment2)
        channelSegment3 = channelSegment3 - np.mean(channelSegment3)

        #
        # apply the taper
        #
        action         = "apply the taper"
        if VERBOSE:
           print action,len(channelSegment1),len(taperWindow)
           print action,len(channelSegment2),len(taperWindow)
           print action,len(channelSegment3),len(taperWindow)
        channelSegment1 = channelSegment1 * taperWindow
        channelSegment2 = channelSegment2 * taperWindow
        channelSegment3 = channelSegment3 * taperWindow

        #
        # FFT
        # data values are real, so the output of FFT is Hermitian symmetric, 
        # i.e. the negative frequency terms are just the complex conjugates of 
        # the corresponding positive-frequency terms
        # We only need the frist half, so doing np.fft.rfft is more efficient
        #
             
        if TIMING:
           t0 = fileLib.timeIt('start FFT ',t0)

        action      = "FFT"
        FFT1        = np.zeros((nSamp/2)+1, dtype=np.complex)
        FFT2        = np.zeros((nSamp/2)+1, dtype=np.complex)
        FFT3        = np.zeros((nSamp/2)+1, dtype=np.complex)

        FFT1        = np.fft.rfft(channelSegment1)
        FFT2        = np.fft.rfft(channelSegment2)
        FFT3        = np.fft.rfft(channelSegment3)

        #
        # matrix
        #
        action = "matrix"
        m11 += FFT1[0:(nSamp/2)+1] * np.conjugate(FFT1[0:(nSamp/2)+1])
        m12 += FFT2[0:(nSamp/2)+1] * np.conjugate(FFT1[0:(nSamp/2)+1])
        m13 += FFT3[0:(nSamp/2)+1] * np.conjugate(FFT1[0:(nSamp/2)+1])
        m22 += FFT2[0:(nSamp/2)+1] * np.conjugate(FFT2[0:(nSamp/2)+1])
        m23 += FFT3[0:(nSamp/2)+1] * np.conjugate(FFT2[0:(nSamp/2)+1])
        m33 += FFT3[0:(nSamp/2)+1] * np.conjugate(FFT3[0:(nSamp/2)+1])

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
           plt.subplot(311)
           plt.plot(traceTime, trChannel1.data, msgLib.param(param,'colorTrace').colorTrace)
           plt.plot(timeSegment, channelSegment, msgLib.param(param,'colorSmooth').colorSmooth)
           plt.ylabel(channel+' ['+msgLib.param(param,'unitLabel').unitLabel[channel]+']')
           plt.xlim(0,msgLib.param(param,'windowLength').windowLength)
           plt.xlabel('Time [s]')

           plt.subplot(312)
           plt.plot(traceTime, trChannel2.data, msgLib.param(param,'colorTrace').colorTrace)
           plt.plot(timeSegment, channelSegment2, msgLib.param(param,'colorSmooth').colorSmooth)
           plt.ylabel(channel2+' ['+msgLib.param(param,'unitLabel').unitLabel[channel]+']')
           plt.xlim(0,msgLib.param(param,'windowLength').windowLength)
           plt.xlabel('Time [s]')

           plt.subplot(313)
           plt.plot(traceTime, trChannel3.data, msgLib.param(param,'colorTrace').colorTrace)
           plt.plot(timeSegment, channelSegment3, msgLib.param(param,'colorSmooth').colorSmooth)
           plt.ylabel(channel3+' ['+msgLib.param(param,'unitLabel').unitLabel[channel]+']')
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
     # to convert FFT to  average spectral covariance matrix
     #
     norm  = 2.0 * delta /  float(nSamp)
     norm *= msgLib.param(param,'normFactor').normFactor
     if VERBOSE:
        print "\n\nDELTA:",delta
        print "NSAMP:",nSamp
        print "NORM:",norm

     print "[INFO] DELTA: "+str(delta)
     print "[INFO] nSegCount: "+str(nSegCount)

     #
     # average
     #
     m11      /= float(nSegCount)
     m12      /= float(nSegCount)
     m13      /= float(nSegCount)
     m22      /= float(nSegCount)
     m23      /= float(nSegCount)
     m33      /= float(nSegCount)

     #
     # if power is not populated, skip LOOP WINDOW or this 1 -hour window
     #
     if len(m11) <= 0:
        continue
 
     variable    = {}
     for var in param.variables:
        variable[var] = []

     for ii in xrange(0,(nSamp/2)+1):
        #
        # form the average spectral covariance matrix, it is a complex  hermitian matrix
        #
        spectraMatrix = []
        spectraMatrix = np.array([[m11[ii],m12[ii],m13[ii]],
                                  [m12[ii].conjugate(),m22[ii],m23[ii]],
                                  [m13[ii].conjugate(),m23[ii].conjugate(),m33[ii]]])

        action        = "eigen.eigenvalues"

        #
        #  Return the eigenvalues and eigenvectors of a Hermitian or symmetric matrix.
        #
        #    This function computes the eigenvalues and eigenvectors of the complex
        #    hermitian matrix A.The imaginary parts of the diagonal are assumed to be
        #    zero and are not referenced. The eigenvalues are stored in the vector
        #    eval and are unordered. The corresponding complex eigenvectors are
        #    stored in the columns of the matrix evec. For example, the eigenvector
        #    in the first column corresponds to the first eigenvalue. The
        #    eigenvectors are guaranteed to be mutually orthogonal and normalised to
        #    unit magnitude.
        #
        (eigValues, eigVectors)    = eigen.eigh(spectraMatrix)
        
        #
        # using maxEigValueIndex in above, we know that maxEigValueIndex = 1
        #
        maxEigValueIndex           = 0
        maxEigValue                = float(eigValues[maxEigValueIndex])
        for i in xrange(1,len(eigValues)):
           if (float(eigValues[i]) > maxEigValue):
              maxEigValue = float(eigValues[i])
              maxEigValueIndex = i
        #
        # eigenvectors of the maximum eigenvalue
        # The corresponding complex eigenvectors are
        # stored in the columns of the matrixDA. evec.
        #
        z1, z2, z3 = eigVectors[:,maxEigValueIndex]
        (thetah,phihh,thetav,phivh) = PL.polarizationAngles(z1,z2,z3)

        #
        # print results
        #
        action = "print values"
        variable["powerUD"] = np.append(variable["powerUD"], norm*abs(m11[ii]))
        variable["powerEW"] = np.append(variable["powerEW"], norm*abs(m22[ii]))
        variable["powerNS"] = np.append(variable["powerNS"], norm*abs(m33[ii]))

        #
        # power spectrum of the primary eigenvalue (Lambda).
        # Variation of this spectrum is very similar to that of
        # the individual components
        #
        variable["powerLambda"] = np.append(variable["powerLambda"], norm*maxEigValue)
        variable["betaSquare"]  = np.append(variable["betaSquare"], PL.polarizationDegree(m11[ii],m12[ii],m13[ii],m22[ii],m23[ii],m33[ii]))
        variable["thetaH"]      = np.append(variable["thetaH"], thetah)
        variable["phiHH"]       = np.append(variable["phiHH"], phihh)
        variable["thetaV"]      = np.append(variable["thetaV"], thetav)
        variable["phiVH"]       = np.append(variable["phiVH"], phivh)

     #
     # END LOOP SEGMENT, segments are done
     #

             
     smoothX    = []
     smooth     = {}
     for var in param.variables:
        smooth[var] = []

     #
     # smoothing
     #
     if TIMING:
        t0 = fileLib.timeIt('start SMOOTHING ',t0)

     if param.doSmoothing:
        print "[INFO] SMOOTHING window:",msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,"octave  shift:",msgLib.param(param,'octaveWindowShift').octaveWindowShift,"octave"
     else:
        print "[INFO] SMOOTHING is off"

     if xType == "period":
        #
        # 10.0*maxT to avoid 1.0/0.0 at zero frequency
        #
        period    = np.append([10.0*msgLib.param(param,'maxT').maxT],1.0/(np.arange(1.0,(nSamp/2)+1)/float(nSamp * delta)))
        if param.doSmoothing:
           if str(msgLib.param(param,'xStart').xStart[plotIndex]) == 'Nyquist':
              #
              # regular smoothing with no angles involved
              #
              smoothX,smooth["powerUD"]       = SFL.smoothNyquist(xType,period,variable["powerUD"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT)
              smoothX,smooth["powerEW"]       = SFL.smoothNyquist(xType,period,variable["powerEW"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT)
              smoothX,smooth["powerNS"]       = SFL.smoothNyquist(xType,period,variable["powerNS"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT)
              smoothX,smooth["powerLambda"]   = SFL.smoothNyquist(xType,period,variable["powerLambda"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT)
              smoothX,smooth["betaSquare"]    = SFL.smoothNyquist(xType,period,variable["betaSquare"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT)

              #
              # smoothing of angular quantities
              #
              smoothX,smooth["thetaH"] = SFL.smoothAngleNyquist(xType,period,variable["thetaH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,0.0)
              for ii in xrange(0,len(smooth["thetaH"])):
                 if(smooth["thetaH"][ii] < 0.0):
                    smooth["thetaH"][ii] += 360.0

              smoothX,smooth["thetaV"] = SFL.smoothAngleNyquist(xType,period,variable["thetaV"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,90.0)

              smoothX,smooth["phiVH"] = SFL.smoothAngleNyquist(xType,period,variable["phiVH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,90.0)
              for ii in xrange(0,len(smooth["phiVH"])):
                 if smooth["phiVH"][ii] > 90.0:
                    smooth["phiVH"][ii] -= 180.0
                 elif smooth["phiVH"][ii] < -90.0:
                    smooth["phiVH"][ii] += 180.0

              smoothX,smooth["phiHH"] = SFL.smoothAngleNyquist(xType,period,variable["phiHH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,90.0)
              for ii in xrange(0,len(smooth["phiHH"])):
                 if smooth["phiHH"][ii] > 180.0:
                    smooth["phiHH"][ii] -= 360.0
                 elif smooth["phiHH"][ii] < -180.0:
                    smooth["phiHH"][ii] += 360.0

           else:
              smoothX,smooth["powerUD"]       = SFL.smoothT(period,variable["powerUD"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,float(msgLib.param(param,'xStart').xStart[plotIndex]))
              smoothX,smooth["powerEW"]       = SFL.smoothT(period,variable["powerEW"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,float(msgLib.param(param,'xStart').xStart[plotIndex]))
              smoothX,smooth["powerNS"]       = SFL.smoothT(period,variable["powerNS"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,float(msgLib.param(param,'xStart').xStart[plotIndex]))
              smoothX,smooth["powerLambda"]   = SFL.smoothT(period,variable["powerLambda"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,float(msgLib.param(param,'xStart').xStart[plotIndex]))
              smoothX,smooth["betaSquare"]    = SFL.smoothT(period,variable["betaSquare"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,float(msgLib.param(param,'xStart').xStart[plotIndex]))
              #
              # smoothing of angular quantities
              #
              smoothX,smooth["thetaH"] = SFL.smoothAngleT(period,variable["thetaH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,float(msgLib.param(param,'xStart').xStart[plotIndex]),0.0)
              for ii in xrange(0,len(smooth["thetaH"])):
                 if(smooth["thetaH"][ii] < 0.0):
                    smooth["thetaH"][ii] += 360.0

              smoothX,smooth["thetaV"] = SFL.smoothAngleT(period,variable["thetaV"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,float(msgLib.param(param,'xStart').xStart[plotIndex]),90.0)

              smoothX,smooth["phiVH"] = SFL.smoothAngleNyquist(xType,period,variable["phiVH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,90.0)
              for ii in xrange(0,len(smooth["phiVH"])):
                 if smooth["phiVH"][ii] > 90.0:
                    smooth["phiVH"][ii] -= 180.0
                 elif smooth["phiVH"][ii] < -90.0:
                    smooth["phiVH"][ii] += 180.0

              smoothX,smooth["phiHH"] = SFL.smoothAngleNyquist(xType,period,variable["phiHH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, msgLib.param(param,'maxT').maxT,90.0)
              for ii in xrange(0,len(smooth["phiHH"])):
                 if smooth["phiHH"][ii] > 180.0:
                    smooth["phiHH"][ii] -= 360.0
                 elif smooth["phiHH"][ii] < -180.0:
                    smooth["phiHH"][ii] += 360.0
        else:
           smoothX               = period
           smooth["powerUD"]     = variable["powerUD"]
           smooth["powerEW"]     = variable["powerEW"]
           smooth["powerNS"]     = variable["powerNS"]
           smooth["powerLambda"] = variable["powerLambda"]
           smooth["betaSquare"]  = variable["betaSquare"]
           smooth["thetaH"]      = variable["thetaH"]
           smooth["thetaV"]      = variable["thetaV"]
           smooth["phiVH"]       = variable["phiVH"]
           smooth["phiHH"]       = variable["phiHH"]
     else:
        frequency = np.array( np.arange(0,(nSamp/2)+1)/float(nSamp * delta))

        if param.doSmoothing:
           if str(msgLib.param(param,'xStart').xStart[plotIndex]) == 'Nyquist':
              smoothX,smooth["powerUD"]       = SFL.smoothNyquist(xType,frequency,variable["powerUD"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency)
              smoothX,smooth["powerEW"]       = SFL.smoothNyquist(xType,frequency,variable["powerEW"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency)
              smoothX,smooth["powerNS"]       = SFL.smoothNyquist(xType,frequency,variable["powerNS"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency)
              smoothX,smooth["powerLambda"]   = SFL.smoothNyquist(xType,frequency,variable["powerLambda"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency)
              smoothX,smooth["betaSquare"]    = SFL.smoothNyquist(xType,frequency,variable["betaSquare"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency)
              #
              # smoothing of angular quantities
              #
              smoothX,smooth["thetaH"] = SFL.smoothAngleNyquist(xType,frequency,variable["thetaH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,0.0)
              for ii in xrange(0,len(smooth["thetaH"])):
                 if(smooth["thetaH"][ii] < 0.0):
                    smooth["thetaH"][ii] += 360.0

              smoothX,smooth["thetaV"] = SFL.smoothAngleNyquist(xType,frequency,variable["thetaV"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,90.0)

              smoothX,smooth["phiVH"] = SFL.smoothAngleNyquist(xType,frequency,variable["phiVH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,90.0)
              for ii in xrange(0,len(smooth["phiVH"])):
                 if smooth["phiVH"][ii] > 90.0:
                    smooth["phiVH"][ii] -= 180.0
                 elif smooth["phiVH"][ii] < -90.0:
                    smooth["phiVH"][ii] += 180.0
   
              smoothX,smooth["phiHH"] = SFL.smoothAngleNyquist(xType,frequency,variable["phiHH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,90.0)
              for ii in xrange(0,len(smooth["phiHH"])):
                 if smooth["phiHH"][ii] > 180.0:
                    smooth["phiHH"][ii] -= 360.0
                 elif smooth["phiHH"][ii] < -180.0:
                    smooth["phiHH"][ii] += 360.0

           else:
              smoothX,smooth["powerUD"]       = SFL.smoothF(frequency,variable["powerUD"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,float(msgLib.param(param,'xStart').xStart[plotIndex]))
              smoothX,smooth["powerEW"]       = SFL.smoothF(frequency,variable["powerEW"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,float(msgLib.param(param,'xStart').xStart[plotIndex]))
              smoothX,smooth["powerNS"]       = SFL.smoothF(frequency,variable["powerNS"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,float(msgLib.param(param,'xStart').xStart[plotIndex]))
              smoothX,smooth["powerLambda"]   = SFL.smoothF(frequency,variable["powerLambda"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,float(msgLib.param(param,'xStart').xStart[plotIndex]))
              smoothX,smooth["betaSquare"]    = SFL.smoothF(frequency,variable["betaSquare"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth, 
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,float(msgLib.param(param,'xStart').xStart[plotIndex]))
              #
              # smoothing of angular quantities
              #
              smoothX,smooth["thetaH"] = SFL.smoothAngleF(frequency,variable["thetaH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,float(msgLib.param(param,'xStart').xStart[plotIndex]),0.0)
              for ii in xrange(0,len(smooth["thetaH"])):
                 if(smooth["thetaH"][ii] < 0.0):
                    smooth["thetaH"][ii] += 360.0

              smoothX,smooth["thetaV"] = SFL.smoothAngleF(frequency,variable["thetaV"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,float(msgLib.param(param,'xStart').xStart[plotIndex]), 90.0)

              smoothX,smooth["phiVH"] = SFL.smoothAngleF(frequency,variable["phiVH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,float(msgLib.param(param,'xStart').xStart[plotIndex]),90.0)
              for ii in xrange(0,len(smooth["phiVH"])):
                 if smooth["phiVH"][ii] > 90.0:
                    smooth["phiVH"][ii] -= 180.0
                 elif smooth["phiVH"][ii] < -90.0:
                    smooth["phiVH"][ii] += 180.0

              smoothX,smooth["phiHH"] = SFL.smoothAngleF(frequency,variable["phiHH"],samplingFrequency, msgLib.param(param,'octaveWindowWidth').octaveWindowWidth,
                                     msgLib.param(param,'octaveWindowShift').octaveWindowShift, minFrequency,float(msgLib.param(param,'xStart').xStart[plotIndex]), 90.0)
              for ii in xrange(0,len(smooth["phiHH"])):
                 if smooth["phiHH"][ii] > 180.0:
                    smooth["phiHH"][ii] -= 360.0
                 elif smooth["phiHH"][ii] < -180.0:
                    smooth["phiHH"][ii] += 360.0
        else:
           smoothX               = frequency
           smooth["powerUD"]     = variable["powerUD"]
           smooth["powerEW"]     = variable["powerEW"]
           smooth["powerNS"]     = variable["powerNS"]
           smooth["powerLambda"] = variable["powerLambda"]
           smooth["betaSquare"]  = variable["betaSquare"]
           smooth["thetaH"]      = variable["thetaH"]
           smooth["thetaV"]      = variable["thetaV"]
           smooth["phiVH"]       = variable["phiVH"]
           smooth["phiHH"]       = variable["phiHH"]
     if TIMING:
        t0 = fileLib.timeIt("SMOOTHING window "+str(msgLib.param(param,"octaveWindowWidth").octaveWindowWidth)+" shift "+str(msgLib.param(param,"octaveWindowShift").octaveWindowShift)+" DONE",t0)

     #
     # convert to dB
     #
     variable["powerUD"]      = 10.0 * np.log10(variable["powerUD"][0:(nSamp/2)+1])
     variable["powerEW"]      = 10.0 * np.log10(variable["powerEW"][0:(nSamp/2)+1])
     variable["powerNS"]      = 10.0 * np.log10(variable["powerNS"][0:(nSamp/2)+1])
     variable["powerLambda"]  = 10.0 * np.log10(variable["powerLambda"][0:(nSamp/2)+1])

     smooth["powerUD"]        = 10.0 * np.log10(smooth["powerUD"][0:(nSamp/2)+1])
     smooth["powerEW"]        = 10.0 * np.log10(smooth["powerEW"][0:(nSamp/2)+1])
     smooth["powerNS"]        = 10.0 * np.log10(smooth["powerNS"][0:(nSamp/2)+1])
     smooth["powerLambda"]    = 10.0 * np.log10(smooth["powerLambda"][0:(nSamp/2)+1])

     #
     # create output paths if they do not exist
     #
     if msgLib.param(param,'outputValues').outputValues > 0:
        filePath, psdFileTag = fileLib.getDir(msgLib.param(param,'dataDirectory').dataDirectory,msgLib.param(param,'polarDbDirectory').polarDbDirectory,network,station,location,channelTag)
        filePath = os.path.join(filePath,segmentStartYear,segmentStartDOY)
        fileLib.makePath(filePath)
        #
        # output is based on the xType
        #
        if VERBOSE:
           print "trChannel.stats:",str(trChannel1.stats)
           print "REQUEST:",segmentStart
           print "TRACE:",str(trChannel1.stats.starttime).replace("Z","")
           print "DELTA:",trChannel1.stats.delta
           print "SAMPLES:",int(float(msgLib.param(param,'windowLength').windowLength)/float(trChannel1.stats.delta) +1)

        tagList = [psdFileTag,str(trChannel1.stats.starttime).replace("Z",""),str(msgLib.param(param,'windowLength').windowLength),xType]
        try:
           with open(fileLib.getFileName(msgLib.param(param,'namingConvention').namingConvention,filePath,tagList), "w") as file:

              #
              # Header
              #
              file.write("%s %s\n" % (xUnits,powerUnits))
              file.write("%s\n" % (header))

              #
              # data
              #
              for i in xrange(0,len(smoothX)):
                  file.write("%11.6f %11.4f %11.4f %11.4f %11.4f %11.4f %11.4f %11.4f %11.4f %11.4f\n" % (float(smoothX[i]),float(smooth["powerUD"][i]),float(smooth["powerEW"][i]),float(smooth["powerNS"][i]),float(smooth["powerLambda"][i]),float(smooth["betaSquare"][i]),float(smooth["thetaH"][i]),float(smooth["thetaV"][i]),float(smooth["phiVH"][i]),float(smooth["phiHH"][i])))

           file.closed
        except:
           msgLib. error("failed to open "+fileLib.getFileName(msgLib.param(param,'namingConvention').namingConvention,filePath,tagList)+"\nis 'namingConvention' "+msgLib.param(param,'namingConvention').namingConvention+" set correctly?" +"\n",0)
           sys.exit()

     #
     ######## Plot ########
     #
     if (msgLib.param(param,'plotSpectra').plotSpectra > 0 or msgLib.param(param,'plotSmooth').plotSmooth>0) and doPlot>0:
        action = "Plot 2"

        if TIMING:
           t0 = fileLib.timeIt('start PLOT ',t0)

        fig = plt.figure(figsize=param.figureSize)
        fig.subplots_adjust(hspace=.2)
        fig.subplots_adjust(wspace=.2)
        fig.set_facecolor('w')

        ax ={}
        plotCount = 0
        for var in param.variables:
           plotCount +=1
           ax[var] = plt.subplot(param.subplot[var])
           ax[var].set_xscale('log')

           #
           # period for the x-axis
           #
           if xType == "period":
              if msgLib.param(param,'plotSpectra').plotSpectra:
                 plt.plot(period, variable[var],  msgLib.param(param,'colorSpectra').colorSpectra,lw=0.8)
              if msgLib.param(param,'plotSmooth').plotSmooth:
                 plt.plot(smoothX, smooth[var], color=msgLib.param(param,'colorSmooth').colorSmooth, lw=1)

           #
           # frequency for the x-axis
           #
           else:
              if msgLib.param(param,'plotSpectra').plotSpectra:
                 plt.plot(frequency, variable[var], msgLib.param(param,'colorSpectra').colorSpectra,lw=0.8)
              if msgLib.param(param,'plotSmooth').plotSmooth:
                 plt.plot(smoothX, smooth[var], color=msgLib.param(param,'colorSmooth').colorSmooth, lw=1)

           plt.xlabel(xUnits)
           plt.xlim(msgLib.param(param,'xlimMin').xlimMin[var][xType],msgLib.param(param,'xlimMax').xlimMax[var][xType])
           plt.ylabel(msgLib.param(param,'yLabel').yLabel[var])
           plt.ylim([msgLib.param(param,'ylimLow').ylimLow[var],msgLib.param(param,'ylimHigh').ylimHigh[var]])
           
           if plotCount == 0:
              plt.title(station+" from "+segmentStart+" to "+segmentEnd)

        if TIMING:
           t0 = fileLib.timeIt('show PLOT ',t0)

        plt.suptitle(title)
        plt.show()
t0 = t1
print " "
t0 = fileLib.timeIt("END",t0)
print " "
