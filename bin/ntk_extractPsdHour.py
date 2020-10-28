version = "R 0.8.0"

################################################################################################
#
# outout usage message
#
################################################################################################
#
def usage():
   print "\n\nUSAGE for version: %s\n\n"%(version)
   print "                                         configuration file name         net     sta      loc     channel startDateTime           endDateTime             x-axis type         0       run with minimum message output"
   print "                                                         |               |       |        |        |         |                        |                         |             |  verbose run in verbose mode"
   print "                                                         |               |       |        |        |         |                        |                         |             |"
   print "                   python ntk_extractPsdHour.py param=extractPsdHour net=NM sta=SLM loc=DASH chan=BHZ start=2009-11-01T11:00:00 end=2009-11-06T00:00:00  type=period     mode=0"
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
# NAME: # ntk_extractPsdHour.py - a Python script to extract PSDs for a given channel and bounding
#                     parameters. The output is similar to PQLX's exPSDhour script
#
# Copyright (C) 2014  Product Team, IRIS Data Management Center
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
# INPUT:
#
# hourly PSD files
#
# HISTORY:
#
#    2015-04-02 Manoch: based on feedback from Robert Anthony, in addition to nan values other
#                       non-numeric values may exist. The write that contains a flot() conversion
#                       is placed in a try block so we can catch any non-numeric conversion issue
#                       and report it as user-defined NAN
#    2014-10-22 Manoch: added support for Windows installation
#    2014-10-06 IRIS DMC Product Team (MB): Beta release :
#                                              output file name now includes the x-axis type
#    2013-05-19 IRIS DMC Product Team (MB): created 
#
################################################################################################
#

#
# PACKAGES:
#
import glob,sys,re,os,math
import numpy as np
from obspy.core import UTCDateTime
from datetime import date, timedelta as td

#
# import the Noise Toolkit libraries
#
libraryPath      = os.path.join(os.path.dirname(__file__), '..', 'lib')
sys.path.append(libraryPath)

import msgLib as msgLib
import fileLib as fileLib
import staLib as staLib

args = getArgs(sys.argv)

#
# see if user has provided the run arguments
#

if len(args) < 9:
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

#
# check to see if param file exists
#
paramPath      = os.path.join(os.path.dirname(__file__), '..', 'param')
if os.path.isfile(os.path.join(paramPath,paramFile+'.py')):
   sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'param'))
   param = importlib.import_module(paramFile)
else:
   msgLib.error('bad parameter file name [' + paramFile + ']', 2)
   usage()
   sys.exit()

VERBOSE      = param.VERBOSE

#
# flag to run in verbose mode
#
VERBOSE  = 0
arg = getParam(args,'mode',msgLib,'verbose')
print "MODE",arg
if arg == 'verbose':
      msgLib.message("VERBOSE RUN")
      VERBOSE        = 1
      print "\n\n[INFO] script: %s" % script
      print "[INFO] ARG#",len(sys.argv)
      print "[INFO] ARGS",sys.argv

#
# RUN ARGUMENTS:
#
network     = getParam(args,'net',msgLib,None)
station     = getParam(args,'sta',msgLib,None)
location    = staLib.getLocation(getParam(args,'loc',msgLib,None))
channel     = getParam(args,'chan',msgLib,None)
if len(channel) <3:
   channel += "*"

#
# PSD files are all HOURLY files with 50% overlap computed as part of the polarization product
# date parameter of the hourly PSDs to start, it starts at hour 00:00:00
#  - HOURLY files YYYY-MM-DD
#
dataDirectory    = param.dataDirectory 
startDateTime    = getParam(args,'start',msgLib,None)
tStart           = UTCDateTime(startDateTime)
startYear        = tStart.strftime("%Y")
startMonth       = tStart.strftime("%m")
startDay         = tStart.strftime("%d")
startDOY         = tStart.strftime("%j")
endDateTime      = getParam(args,'end',msgLib,None)
tEnd             = UTCDateTime(endDateTime)
endYear          = tEnd.strftime("%Y")
endMonth         = tEnd.strftime("%m")
endDay           = tEnd.strftime("%d")
endDOY           = tEnd.strftime("%j")
duration         = tEnd - tStart

dEnd             = date(int(endYear),int(endMonth),int(endDay))
dStart           = date(int(startYear),int(startMonth),int(startDay))
delta            = dEnd - dStart
dataDaysList     = []
for i in xrange(delta.days +1):
   thisDay = dStart + td(days=i)
   dataDaysList.append(thisDay.strftime("%Y/%j"))

if duration <=0 or len(dataDaysList) <= 0:
   msgLib.error('bad start/end times [' + startDateTime + ', ' + endDateTime + ']', 2)
   usage()
   sys.exit()

xType            = getParam(args,'type',msgLib,None)

#####################################
# find and start reading the PSD files 
#####################################
#
# build the file tag for the PSD files to read, example:
#     NM_SLM_--_BH_2009-01-06
#
psdDbDirTag, psdDbFileTag = fileLib.getDir(param.dataDirectory,param.psdDbDirectory,network,station,location,channel)

print "\n[INFO] PSD DIR TAG: " + psdDbDirTag
if VERBOSE >0 :
   print "\n[INFO] PSD FILE TAG: " + psdDbFileTag

#####################################
# open the output file
#####################################
#
psdDirTag, psdFileTag = fileLib.getDir(param.dataDirectory,param.psdDirectory,network,station,location,channel)
fileLib.makePath(psdDirTag)
tagList               = [psdFileTag,startDateTime.split('.')[0],endDateTime.split('.')[0],xType]
outputFileName        = fileLib.getFileName(param.namingConvention,psdDirTag,tagList)   
#outputFileName = os.path.join(psdDirTag,'.'.join([psdFileTag,startDateTime.split('.')[0],endDateTime.split('.')[0]+'_'+xType+'.txt']))
with open(outputFileName, 'w') as outputFile:

   #####################################
   # loop through the windows
   #####################################
   #
   for n in xrange(len(dataDaysList)):

      thisFile = os.path.join(psdDbDirTag, dataDaysList[n], psdDbFileTag+'*'+xType+'.txt')
      print "[INFO] Day:", dataDaysList[n] 
      thisFileList = sorted(glob.glob(thisFile))   
   
      if len(thisFileList)<=0:
         msgLib.warning('Main','No files found!')
         if VERBOSE:
            print "skip"
         continue
      elif len(thisFileList)>1:
         if VERBOSE:
            print len(thisFileList), "files  found!"
      #####################################
      # found the file, open it and read it
      #####################################
      #
      for thisPsdFile in thisFileList:
         if VERBOSE >0 :
            print "[INFO] PSD FILE: " ,thisPsdFile
         thisFileTimeLabel = fileLib.getFileTimes(param.namingConvention,channel,thisPsdFile)
         thisFileTime      = UTCDateTime(thisFileTimeLabel[0])
         if thisFileTime >= tStart and thisFileTime <= tEnd:
            with open(thisPsdFile) as file:
               if VERBOSE >0 :
                  print "OK, working on ..." + thisPsdFile

               #
               # skip the header line
               #
               next(file)

               #
               # go through individual periods/frequencies
               #
               for line in file:

                   #
                   # each row, split column values
                   #
                   X,V = re.split('\s+',line.strip('.').strip())

                   #
                   # save the period/frequency and the value of interest
                   #
                   thisOutDate,thisOutTime = thisFileTimeLabel[0].split('T')

                   #
                   # here we convert potential 'nan' and 'inf' (non-numeric) values to user defined NAN
                   #
                   try:
                      outputFile.write("%s%s%s%s%s%s%d\n" % (thisOutDate,param.separator,thisOutTime.split('.')[0],param.separator,X,param.separator,round(float(V))))
                   except: 
                      outputFile.write("%s%s%s%s%s%s%d\n" % (thisOutDate,param.separator,thisOutTime.split('.')[0],param.separator,X,param.separator,param.intNan))

            file.close()
print "\n[INFO] OUTPUT FILE: " + outputFileName
outputFile.close()
