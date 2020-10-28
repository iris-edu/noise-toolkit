version = "R 0.8.0"

################################################################################################
#
# outout usage message
#
################################################################################################
#
def usage():
   print "\n\nUSAGE for version: %s\n\n"%(version)
   print "                                        configuration file name          net    sta      loc      chan    start date      end date-time[exclusive]     x-axis type  verbose on/off"
   print "                                                       |                  |      |        |        |           |                      |                       |                 |"
   print "                   python ntk_binPsdDay.py    param=binPsdDay        net=NM sta=SLM loc=DASH chan=BHZ start=2009-01-01          end=2009-01-06         type=period         mode=0"
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
# NAME: # ntk_binPsdDay.py - a Python script to bin PSD's to daily files for a given channel and bounding
#                     parameters. The output is similar to those available from IRIS PDF/PSD Bulk Data 
#                     Delivery System (http://www.iris.edu/dms/products/pdf-psd/)
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
#    2014-10-22 Manoch: added support for Windows installation
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
      VERBOSE   = 1
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
startDateTime    = getParam(args,'start',msgLib,None).split("T")[0] # we always want to start from the begining of the day, so we discard user hours, if any
startDateTime   += "T00:00:00"
tStart           = UTCDateTime(startDateTime)
startYear        = tStart.strftime("%Y")
startMonth       = tStart.strftime("%m")
startDay         = tStart.strftime("%d")
startDOY         = tStart.strftime("%j")
endDateTime      = getParam(args,'end',msgLib,None).split("T")[0] # we always want to start from the begining of the day, so we discard user hours, if any
endDateTime     += "T00:00:00" # endDateTime is included
tEnd             = UTCDateTime(endDateTime)+86400
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

xType       = getParam(args,'type',msgLib,None)

#####################################
# find and start reading the PSD files 
#####################################
#
# build the file tag for the PSD files to read, example:
#     NM_SLM_--_BH_2009-01-06
#
psdDbDirTag, psdDbFileTag = fileLib.getDir(param.dataDirectory,param.psdDbDirectory,network,station,location,channel)

print "\n[INFO] PSD DIR TAG: " + psdDbDirTag
if VERBOSE:
   print "\n[INFO] PSD FILE TAG: " + psdDbFileTag

#####################################
# loop through the windows
#####################################
#
for n in xrange(len(dataDaysList)):
   print "\n[INFO] day ",dataDaysList[n]
   Dfile = {}
   Hfile = []
   thisFile = os.path.join(psdDbDirTag, dataDaysList[n], psdDbFileTag+'*'+xType+'.txt')
   if VERBOSE:
      print "[INFO] Looking into:", thisFile 
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
      thisYear          = thisFileTime.strftime("%Y")   
      thisHour          = thisFileTime.strftime("%H:%M")   
      thisDOY           = thisFileTime.strftime("%j")   
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
                X,V      = re.split('\s+',line.strip(' ').strip())

                #
                # here we onver potential 'nan' values to user defined NAN
                #
                if V.upper() == 'NAN':
                   thisLine = "%s%s%s%s%d" % (thisHour,param.separator,X,param.separator,param.intNan)
                   key = X+":"+str(param.intNan)
                else:
                   thisLine = "%s%s%s%s%d" % (thisHour,param.separator,X,param.separator,int(round(float(V))))
                   key = X+":"+str(int(round(float(V)))) 
                Hfile.append(thisLine)
                if key in Dfile.keys():
                   Dfile[key] +=1
                else:
                   Dfile[key] =1

         file.close()

   #####################################
   # open the output file
   #####################################
   #
   pdfDirTag, pdfFileTag = fileLib.getDir(param.dataDirectory,param.pdfDirectory,network,station,location,channel)
   fileLib.makePath(pdfDirTag)
   thisPath = os.path.join(pdfDirTag,'Y'+thisYear)
   fileLib.makePath(thisPath)
   outputFile = os.path.join(thisPath,'D' + thisDOY + '.bin')
   print "[INFO] DAILY OUTPUT FILE: " + outputFile
   with open(outputFile, 'w') as outputFile:
      for key in sorted(Dfile.keys()):
         day,db = key.split(":") 
         outputFile.write("%s%s%s%s%i\n" % (day,param.separator,db,param.separator,Dfile[key]))
   outputFile.close()

   if param.pdfHourlySave > 0:
      thisPath = os.path.join(thisPath,param.pdfHourlyDirectory)
      fileLib.makePath(thisPath)
      outputFile = os.path.join(thisPath,'H' + thisDOY + '.bin')
      print "[INFO] HOURLY OUTPUT FILE: " + outputFile
      with open(outputFile, 'w') as outputFile:
         for i in xrange(len(Hfile)):
            outputFile.write("%s\n"%Hfile[i])
      outputFile.close()
   else:
     print "[INFO] hourly PSD save option turned off"
   
