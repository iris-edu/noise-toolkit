from   obspy.core import UTCDateTime, read, Stream
from   obspy.core.util import NamedTemporaryFile
import os, math
import numpy as np
import staLib  as staLib
from   obspy.core import utcdatetime


###########################################################
# getChannelWaveform gets data from the FDSN client.
# for the requested network/station/location/channel
# and time
#
# the output is the corresponding data stream 
#
# HISTORY:
#    2015-03-17 Manoch: added the "waterLevel" parameter to provide user with more control on how the ObsPy module shrinks values under water-level of max spec amplitude
#                       when removing the instrument response.
#    2015-02-24 Manoch: introduced two new parameters (performInstrumentCorrection, applyScale) to allow user avoid instrument correction also now user can turn od decon. filter
#    2014-02-07 Manoch: created
#
###########################################################
# 
def getChannelWaveform (network, station, location,channel,start,end,removeTrend,performInstrumentCorrection,applyScale,deconFilter1, deconFilter2, deconFilter3, deconFilter4,waterLevel,unit,client):

   #
   # stream
   #
   try:
      stream         = client.get_waveforms(network, station, location, channel, start, end, attach_response=True)

      #
      # print stream Gap information
      #
      # print "\n\nSTREAM GAP INFORMATION:\n"
      #stream.printGaps()

      if(removeTrend > 0):
         stream.detrend("demean")

      #
      # remove the instrument response 
      #
      if performInstrumentCorrection:
         print "[INFO] PERFORM INSTRUMENT CORRECTION"
         if deconFilter1<=0 and deconFilter2<=0 and deconFilter3<=0 and deconFilter4<=0:
            print "[INFO] NO DECON FILTER APPLIED"
            stream.remove_response(output=unit,pre_filt=None,taper=False,zero_mean=False,water_level=waterLevel)
         else:
            print "[INFO] DECON FILTER APPLIED"
            stream.remove_response(output=unit,pre_filt=[deconFilter1,deconFilter2,deconFilter3,deconFilter4],taper=False,zero_mean=False,water_level=waterLevel)
      #
      # do not remove the instrument response but apply the sensitivity
      #
      elif applyScale:
         print "[INFO] NO INSTRUMENT CORRECTION, APPLY SENSITIVITY",stream[0].stats.response.instrument_sensitivity.value
         for i in xrange(len(stream)):
            stream[i].data = stream[i].data / float(stream[i].stats.response.instrument_sensitivity.value)
  
   except Exception, e:
      print str(e)
      print "[ERROR] client.get_waveforms",network, station, location, channel, start, end
      return(None)

   return(stream)

###########################################################
# getChannelWaveform gets data from the IRIS client.
# for the requested network/station/location/channel
# and time
#
# the output is the corresponding data stream 
#
# This function will enable non-standard instrument corrections
# such as polynomials for the TA infrasound channels
#
# HISTORY:
#    2015-02-24 Manoch: introduced two new parameters (performInstrumentCorrection, applyScale) to allow user avoid instrument correction also now user can turn od decon. filter
#    2014-02-07 Manoch: created
#
###########################################################
# 
def getIrisChannelWaveform (network, station, location,channel,start,end,removeTrend,performInstrumentCorrection,applyScale,deconFilter1, deconFilter2, deconFilter3, deconFilter4,unit,client):

   supportedUnits = ['DIS', 'VEL', 'ACC' , 'DEF']
   demean = "false"
   if removeTrend:
      demean = "true"
   #
   # stream
   #
   try:
      #
      # detrend
      #
      if removeTrend > 0:
         #
         # the requested unit is supported
         #
         if unit in supportedUnits:
            #
            # remove instrument response
            #
            if performInstrumentCorrection:
               print "[INFO] PERFORM INSTRUMENT CORRECTION"
               if deconFilter1<=0 and deconFilter2<=0 and deconFilter3<=0 and deconFilter4<=0:
                  print "[INFO] NO DECON FILTER APPLIED"
                  stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),demean=demean,correct="true",units=unit)
               else:
                  stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),freqlimits=",".join([str(deconFilter1),str(deconFilter2),str(deconFilter3),str(deconFilter4)]),demean=demean,correct="true",units=unit)
            #
            # apply stage-zero gain only
            #
            elif applyScale:
               stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),demean=demean,scale="AUTO")
            #
            # no scaling
            #
            else:
               stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),demean=demean)
         #
         # the requested unit is NOT supported
         #
         else:
            #
            # remove instrument response
            #
            if performInstrumentCorrection:
               print "[INFO] PERFORM INSTRUMENT CORRECTION"
               if deconFilter1<=0 and deconFilter2<=0 and deconFilter3<=0 and deconFilter4<=0:
                  print "[INFO] NO DECON FILTER APPLIED"
                  stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),demean=demean,correct="true")
               else:
                  stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),freqlimits=",".join([str(deconFilter1),str(deconFilter2),str(deconFilter3),str(deconFilter4)]),demean=demean,correct="true")
            #
            # apply stage-zero gain only
            #
            elif applyScale:
               stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),demean=demean,scale="AUTO")
            #
            # no scaling
            #
            else:
               stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),demean=demean)
      #
      # do not remove trend
      #
      else:
         #
         # the requested unit is supported
         #
         if unit in supportedUnits:
            #
            # remove instrument response
            #
            if performInstrumentCorrection:
               print "[INFO] PERFORM INSTRUMENT CORRECTION"
               if deconFilter1<=0 and deconFilter2<=0 and deconFilter3<=0 and deconFilter4<=0:
                  print "[INFO] NO DECON FILTER APPLIED"
                  stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),correct="true",units=unit)
               else:
                  stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),freqlimits=",".join([str(deconFilter1),str(deconFilter2),str(deconFilter3),str(deconFilter4)]),correct="true",units=unit)
            #
            # apply stage-zero gain only
            #
            elif applyScale:
               stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),scale="AUTO")
            else:
               stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"))
         #
         # the requested unit is NOT supported
         #
         else:
            if performInstrumentCorrection:
               print "[INFO] PERFORM INSTRUMENT CORRECTION"
               if deconFilter1<=0 and deconFilter2<=0 and deconFilter3<=0 and deconFilter4<=0:
                  print "[INFO] NO DECON FILTER APPLIED"
                  stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),correct="true")
               else:
                  stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),freqlimits=",".join([str(deconFilter1),str(deconFilter2),str(deconFilter3),str(deconFilter4)]),correct="true")
            else:
               if applyScale:
                  stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"),scale="AUTO")
               else:
                  stream = client.timeseries(network=network, station=station, channel=channel, location=location, starttime=start.replace(" ","T"),endtime=end.replace(" ","T"))

      #
      # print stream Gap information
      #
      # print "\n\nSTREAM GAP INFORMATION:\n"
      #stream.printGaps()

   except Exception, e:
      print str(e)
      print "[ERROR] client.get_waveforms",network, station, location, channel, start.replace(" ","T"), end.replace(" ","T"),",".join([str(deconFilter1),str(deconFilter2),str(deconFilter3),str(deconFilter4)])
      return(None)

   return(stream)

###########################################################
# getChannelWaveformFiles gets data from files and
# the response form the FDSN client. for the requested 
# network/station/location/channel and time
#
# the output is the corresponding data stream 
# fileTag should be in such a way to guide the function in 
# selecting waveform files like
# 
# {this Path}/*.SAC
# 
# channel may have the last one or two letters wildcarded (e.g. channel="EH*") 
# to select all components with a common band/instrument code.
#
# All other selection criteria that accept strings (network, station, location) 
# may also contain Unix style wildcards (*, ?, ...).
# 
# HISTORY:
#    2015-03-17 Manoch: added the "waterLevel" parameter to provide user with more control on how the ObsPy module shrinks values under water-level of max spec amplitude
#                       when removing the instrument response.
#    2015-02-24 Manoch: introduced two new parameters (performInstrumentCorrection, applyScale) to allow user avoid instrument correction also now user can turn od decon. filter
#
#    2014-03-15 Manoch: created
#
###########################################################
# 
def getChannelWaveformFiles (network, station, location, channel, starttime, endtime, removeTrend, performInstrumentCorrection,applyScale,deconFilter1, deconFilter2, deconFilter3, deconFilter4, waterLevel, unit, client, fileTag):

   #
   # stream holds the final stream
   #
   thisStartTime = UTCDateTime(starttime)
   thisEndTime   = UTCDateTime(endtime)
   stream   = Stream()
   streamIn = Stream()
   try:
      #
      # read in the files to a stream
      #
      print "[INFO] checking:",fileTag
      if performInstrumentCorrection:
         streamIn       = read(fileTag, starttime=thisStartTime, endtime=thisEndTime, nearest_sample=True, apply_calib=False )
      else:
         print "[INFO] Apply scaling"
         streamIn       = read(fileTag, starttime=thisStartTime, endtime=thisEndTime, nearest_sample=True, apply_calib=applyScale )
      #print "STREAM IN",fileTag, starttime, endtime

   except Exception, e:
      print str(e)
      print "[ERROR] client.get_waveforms",network, station, location, channel, starttime, endtime
      return(None)

   try:

      #
      # select the desire streams only
      #
      if location == "--":
         streamOut        = streamIn.select(network=network, station=station, location="*", channel=channel)
      else:
         streamOut        = streamIn.select(network=network, station=station, location=location, channel=channel)

      for i in xrange(len(streamOut)):
         if performInstrumentCorrection: 
            # 
            # get the network, station, location and channel information
            # 
            (thisNSLC,thisTime,junk) = str(streamOut[i]).split('|')
            (net,sta,loc,chan) = thisNSLC.strip().split('.')
            if len(loc) == 0:
               loc = "--"

            #
            # The FDSN webservices return StationXML metadata.
            #
            (start,end) = thisTime.split(' - ')
            try:
               thisStarttime = UTCDateTime(start.strip())
               thisEndtime   = UTCDateTime(end.strip())
               inv = client.get_stations(network=net,station=sta,location=loc,channel=chan,starttime=thisStarttime,endtime=thisEndtime,level="response")
               streamOut[i].attach_response(inv)
               stream += streamOut[i]
            except Exception, e:
               print str(e)
               print "NO RESPONSE:",net,sta,loc,chan,thisStarttime,thisEndtime
               continue
         else:
            stream += streamOut[i]

      #
      # print stream Gap information
      #
      # print "\n\nSTREAM GAP INFORMATION:\n"
      #stream.printGaps()

      if(removeTrend > 0):
         stream.detrend("demean")

      #
      # remove the instrument response 
      #
      if performInstrumentCorrection:
         print "[INFO] PERFORM INSTRUMENT CORRECTION",unit
         if deconFilter1<=0 and deconFilter2<=0 and deconFilter3<=0 and deconFilter4<=0:
            print "[INFO] NO DECON FILTER APPLIED"
            stream.remove_response(output=unit,pre_filt=None, zero_mean=False, taper=False,water_level=waterLevel)
         else:
            stream.remove_response(output=unit,pre_filt=[deconFilter1,deconFilter2,deconFilter3,deconFilter4], zero_mean=False, taper=False,water_level=waterLevel)

   except Exception, e:
      print str(e)
      print "[ERROR] client.get_waveforms",network, station, location, channel, starttime, endtime
      return(None)

   return(stream)


###########################################################
# qc3Stream performs a QC on a 3-C stream by making sure
# all channels are present, traces are the same
# length and have same start and end timeo# mostly needed for polarization analysis
#
# the output is an array of trace record numbers in the stream that passed
# the QC
# 
# HISTORY:
#    2014-04-21 Manoch: created
###########################################################
#
def qc3Stream(stream,segmentLength,window,sortedChannelList,channelGroups,VERBOSE):
   streamList = str(stream)
   if VERBOSE:
      print  "[QC3-INFO] there are ",streamList,"\n\n"
   streamArray= streamList.split("\n")
   streamContent = []
   for i in xrange(1,len(streamArray)): # first line is title
      streamContent.append(streamArray[i]+ "|" + str(i))

   #
   # sort to make sure related records are one after another
   #
   streamContent =  sorted(streamContent)

   #
   # extract the list, one recrd (line) at a time and group them
   #
   qcRecordList       = []
   previousGroupName  = ""
   groupCount         = -1
   groupChannels      = []
   groupRecords       = []
   groupNames         = []
   staInfoList        = []
   timeInfoList       = []
   chanInfoList       = []
   recordInfoList     = [] 

   for i in xrange(len(streamContent)):
      #
      # reset the list for each record (line)
      #
      thisStaInfoList        = []
      thisTimeInfoList       = []
      thisChanInfoList       = []
      thisRecordInfoList     = []

      #
      # RECORD: NM.SIUC..BHE | 2009-11-01T11:00:00.019537Z - 2009-11-01T11:59:59.994537Z | 40.0 Hz, 144000 samples|1
      #             |                                      |                                         |             |
      #            staInfo                               timeInfo                                 chanInfo         recInfo
      #
      # from each record extract parts
      #
      staInfo,timeInfo,chanInfo,recInfo = streamContent[i].split("|")

      #
      # from each part extract list
      #
      #                     0   1   2    3
      # thisStaInfoList = [NET,STA,LOC,CHAN]
      #
      thisStaInfoList = staInfo.strip().split(".")
      thisStaInfoList[2] = staLib.getLocation(thisStaInfoList[2]) # replace blank locations with "--"

      #
      #                       0   1  
      # thisTimeInfoList = [START,END]
      #
      thisTimeInfoList.append(timeInfo.strip().split(" - "))

      #
      #                       0        1     2      3
      # thisChanInfoList = [SAMPLING,UNIT,SAMPLES,TEXT]
      #
      thisChanInfoList.append(chanInfo.strip().split(" "))

      #
      # thisRecordInfoList = RECORD
      #
      thisRecordInfoList.append(int(recInfo.strip()))

      #
      # name each record as a channel group (do not include channel)
      #
      thisGroupName  =  ".".join(thisStaInfoList[ii] for ii in xrange(len(thisStaInfoList)-1))

      #
      # starting the first group, start saving info
      #
      if thisGroupName != previousGroupName:
         groupCount +=1
         if VERBOSE:
            print "[QC-INFO] started group",groupCount,":",thisGroupName
         groupNames.append(thisGroupName)

         groupChannels.append([])
         groupRecords.append([])
     
         previousGroupName  = thisGroupName
     
      groupChannels[groupCount].append(thisStaInfoList[-1]) # save channel names
      groupRecords[groupCount].append(i)

      #
      # note: the following arrays are not grouped, hence extend and not append
      #
      timeInfoList.extend(thisTimeInfoList)
      chanInfoList.extend(thisChanInfoList)
      staInfoList.extend([thisStaInfoList])
      recordInfoList.extend(thisRecordInfoList)

   if VERBOSE:
      print "\n[QC3-INFO]found ",len(groupRecords)," record groups"

   #
   # QC each group
   #
   for i in xrange(len(groupRecords)):

      #
      # all group elements are in, start the QC
      #
      qcPassed = True

      if VERBOSE:
         print "\n[QC3-INFO] QC for record group ",groupNames[i]

      #
      # create a sorted list of unique channels
      #
      channelList = sorted(set(groupChannels[i]))
      if VERBOSE:
         print "[QC3-INFO] channel list:",channelList

      #
      # Missing Channels?
      #
      # - based on missing records
      #
      if len(groupRecords[i]) < 3:
         print "[QC3-rejected] missing channels records, received ",len(groupRecords[i])
         qcPassed = False
      else:
         #
         # - based on channels missing from channel list
         #
         if channelList not in sortedChannelList:   
            print "[QC3-rejected] missing channels records from",groupNames[i]," got (",channelList,"while expecting",sortedChannelList,")"
            qcPassed = False
         #
         # - channel list is valid
         #
         else:
            print "[QC3-passed] channel list complete",channelList

            #
            # Gaps?
            #
            # this is a simple rejection based on gaps. A better choice will be to take segments and process those with sufficient length
            # but with 3 channels involved, this will be too complicated -- manoch 2014-04-18
            #
            if len(groupRecords[i]) > 3:
               print "[QC3-check] gaps in ",groupNames[i]
               qcPassed = False
            else:
               print "[QC3-passed] no gaps in",groupNames[i]

               #
               # check for sampling rates
               #
               rec1,rec2,rec3 = map(int,groupRecords[i]) 
               samplingFrequency01 = float(chanInfoList[rec1][0])
               samplingFrequency02 = float(chanInfoList[rec2][0])
               samplingFrequency03 = float(chanInfoList[rec3][0])
               if samplingFrequency01 != samplingFrequency02 or samplingFrequency01 != samplingFrequency03:
                  print "[QC3-rejected] sampling frequencies do not match!(",samplingFrequency01, samplingFrequency02, samplingFrequency03
                  qcPassed = False
               else:
                  print "[QC3-passed] sampling frequencies",[samplingFrequency01,samplingFrequency02,samplingFrequency03]

                  #
                  # check for mismatched start time - Note: there are exactly 3 records
                  #
                  delay01 = np.abs(utcdatetime.UTCDateTime(timeInfoList[rec1][0]) -  utcdatetime.UTCDateTime(timeInfoList[rec2][0]))
                  delay02 = np.abs(utcdatetime.UTCDateTime(timeInfoList[rec1][0]) -  utcdatetime.UTCDateTime(timeInfoList[rec3][0]))
                  samplerate = 1.0 / float(chanInfoList[rec1][0])

                  #
                  # calculate number of points needed for FFT (as a power of 2) based on the run parameters
                  #
                  nSampNeeded  = 2**int(math.log(int((float(segmentLength) / samplerate +1)/window), 2)) # make sure it is power of 2
                  if delay01 == 0.0 and delay02 == 0.0:
                     print "[QC3-Passed] start time"
                  else:
                     if delay01 > 0.0 and delay01 < samplerate:
                        print "[QC3-Passed] start time difference between", '.'.join(staInfoList[rec1]), "and", '.'.join(staInfoList[rec2]), "is",delay01,"s, less than 1 sample"
                     elif delay01 > 0.0 and delay01 >= samplerate:
                        print "[QC3-Failed] start time difference between", '.'.join(staInfoList[rec1]), "and", '.'.join(staInfoList[rec2]), "is",delay01,"s, is 1 sample or more"
                        qcPassed = False
                     if delay02 > 0.0 and delay02 < samplerate:
                        print "[QC3-Passed] start time difference between", '.'.join(staInfoList[rec1]), "and", '.'.join(staInfoList[rec3]), "is",delay02,"s, less than 1 sample"
                     elif delay02 > 0.0 and delay02 >= samplerate:
                        print "[QC3-Failed] start time difference between", '.'.join(staInfoList[rec1]), "and", '.'.join(staInfoList[rec3]), "is",delay02,"s, is 1 sample or more"
                        qcPassed = False

                  #
                  # check for insufficient number of samples
                  #
                  if qcPassed:

                     samplesList = map(float,zip(chanInfoList[rec1],chanInfoList[rec2],chanInfoList[rec3])[2])
                     if VERBOSE:
                        print "[QC3-Info] samples:",samplesList
                     minimumSamples = np.min(samplesList)
                     if minimumSamples <  nSampNeeded:
                        print "[QC3-Failed] wanted minimum of", nSampNeeded, " but got only", minimumSamples
                        qcPassed = False 
                     else:
                        print "[QC3-Passed] wanted minimum of", nSampNeeded, " got ", minimumSamples
                        #
                        # mismatched end time
                        #
                        delay01 = np.abs(utcdatetime.UTCDateTime(timeInfoList[rec1][1]) -  utcdatetime.UTCDateTime(timeInfoList[rec2][1]))
                        delay02 = np.abs(utcdatetime.UTCDateTime(timeInfoList[rec1][1]) -  utcdatetime.UTCDateTime(timeInfoList[rec3][1]))
                        samplerate = 1.0 / float(chanInfoList[rec1][0])
                        qcPassed = True
                        if delay01 == 0.0 and delay02 == 0.0:
                           print "[QC3-Passed] end time"
                        #
                        # for information only, we know we have enough samples!
                        #
                        else:
                           if delay01 > 0.0 and delay01 < samplerate:
                              print "[QC3-Info] end time difference between", '.'.join(staInfoList[rec1]), "and", '.'.join(staInfoList[rec2]), "is",delay01,"s, less than 1 sample"
                           elif delay01 > 0.0 and delay01 >= samplerate:
                              print "[QC3-Info] end time difference between", '.'.join(staInfoList[rec1]), "and", '.'.join(staInfoList[rec2]), "is",delay01,"s, is 1 sample or more"
                           if delay02 > 0.0 and delay02 < samplerate:
                              print "[QC3-Info] end time difference between", '.'.join(staInfoList[rec1]), "and", '.'.join(staInfoList[rec3]), "is",delay02,"s, less than 1 sample"
                           elif delay02 > 0.0 and delay02 >= samplerate:
                              print "[QC3-Info] end time difference between", '.'.join(staInfoList[rec1]), "and", '.'.join(staInfoList[rec3]), "is",delay02,"s, is 1 sample or more"

            #
            # end of the QC save qcPassed flag
            #
            if qcPassed:
               #
               # put records in proper channel order
               # first  go through each requested channel group
               #
               for chanList in channelGroups:
                  #
                  # found the matching channel group?
                  #
                  if groupChannels[i][0] in chanList and groupChannels[i][1] in chanList and groupChannels[i][2] in chanList:
                      print "[QC-INFO] output channel order should be",chanList
                      orderedGroupRecords = [-1,-1,-1]
                      orderedGroupRecords[chanList.index(groupChannels[i][0])] = groupRecords[i][0]
                      orderedGroupRecords[chanList.index(groupChannels[i][1])] = groupRecords[i][1]
                      orderedGroupRecords[chanList.index(groupChannels[i][2])] = groupRecords[i][2]
                      qcRecordList.append(orderedGroupRecords)

   if VERBOSE:
      print "[QC-INFO] passed records:",qcRecordList
   return qcRecordList



