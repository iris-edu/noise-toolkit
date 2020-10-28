import sys
version = "R 0.5.0"
################################################################################################
#
# outout usage message
#
################################################################################################
#
def usage():
   print "\n\nUSAGE:\n\n"
   print "                               configuration file name                       net   sta      loc       channel directory     start date-time        end date-time         x-axis type mode = verbose -- run in verbose mode"
   print "                                                    |                         |     |        |           |                   |                     |                        |          |    0       -- run with minimum message output"
   print "                                                    |                         |     |        |           |                   |                     |                        |          |"
   print "                   python ntk_extractPolarHour.py param=extractPolarHour net=NM sta=SLM loc=DASH chandir=BHZ_BHE_BHN start=2009-11-01T11:00:00 end=2009-11-06T00:00:00 type=frequency mode=0"

   print " "
   print " chandir is the ichannel directory under which the polarization output files are stored (under polarDb)"
   print " "
   print " hourly polarization values are extracted for each variable as defined by 'variables' in the computePolarization parameter file and the param file above ('variables' must have the same value in both parameter files)"
   print " available variables are: powerUD, powerEW, powerNS, powerLambda, betaSquare, thetaH, thetaV, phiVH, phiHH"
   print "\n\nOutput file name provided during the run"
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
      if '=' not in argList[i]:
         print '[ERROR] bad parameter definition',argList[i]
         usage()
         sys.exit()
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
      print '[ERROR] missing parameter ',key
      usage()
      sys.exit()

################################################################################################
#
# Main
#
################################################################################################
#
# NAME: # ntk_extractPolarHour.py - a Python script to extract polarization parameters for the given channelis and bounding
#                     parameters. The output is similar to PQLX's exPSDhour script
#
# Copyright (C) 2015  Product Team, IRIS Data Management Center
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
# hourly polarization files
#
# HISTORY:
#
#    2015-09-15 R0.5.0: Beta release
#    2013-06-07 IRIS DMC Product Team (MB): created 
#
################################################################################################
#

#
# PACKAGES:
#
import glob,re,os,math
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

if len(args) < 8:
   msgLib.error("missing argument(s)",1)
   usage()
   sys.exit()

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

VERBOSE      = msgLib.param(param,'VERBOSE').VERBOSE

VERBOSE  = 0
arg = getParam(args,'mode',msgLib,'verbose')
print "MODE",arg
if arg == 'verbose':
      msgLib.message("VERBOSE RUN")
      VERBOSE        = 1

if VERBOSE >0 :
   print "\n\n[INFO] script: %s" % script
   print "[INFO] ARG#",len(sys.argv)
   print "[INFO] ARGS",sys.argv

if len(sys.argv) < 9:
   msgLib.error("missing argument(s)",1)
   usage()
   sys.exit()

script = sys.argv[0]

#
# RUN ARGUMENTS:
#
print "\n"
msgLib.message("START")


network     = getParam(args,'net',msgLib,None)
station     = getParam(args,'sta',msgLib,None)
location    = staLib.getLocation(getParam(args,'loc',msgLib,None))
channelDir  = getParam(args,'chandir',msgLib,None)

#
# Polarization files are all HOURLY files with 50% overlap computed as part of the polarization product
# date parameter of the hourly Polarizations to start, it starts at hour 00:00:00
#  - HOURLY files YYYY-MM-DD
#
variableList     = param.variables
dataDirectory    = param.dataDirectory 
startDateTime    = getParam(args,'start',msgLib,None)

#
# processing parameters
#
xType            = getParam(args,'type',msgLib,'period')   # what the x-axis should represent
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

#####################################
# find and start reading the polarization files 
#####################################
#
# build the file tag for the polarization files to read, example:
#     NM_SLM_--_BH_2009-01-06
#
polarDbDirTag, polarDbFileTag = fileLib.getDir(param.dataDirectory,param.polarDbDirectory,network,station,location,channelDir)

print "\n[INFO] polarization DIR TAG: " + polarDbDirTag + "\n"
if VERBOSE >0 :
   print "\n[INFO] polarization FILE TAG: " + polarDbFileTag

#####################################
# open the output file for each parameter
#####################################
#
thisPolarDirTag, polarFileTag = fileLib.getDir(param.dataDirectory,param.polarDirectory,network,station,location,channelDir)
for pn in xrange(len(variableList)):
   variable = variableList[pn]
   print "[INFO] variable:",variable+"\n"
   polarDirTag = os.path.join(thisPolarDirTag,variable)
   fileLib.makePath(polarDirTag)
   tagList        = [polarFileTag,startDateTime.split('.')[0],endDateTime.split('.')[0],xType]
   outputFileName = fileLib.getFileName(param.namingConvention,polarDirTag,tagList)
   try:
      with open(outputFileName, 'w') as outputFile:


         #####################################
         # loop through the windows
         #####################################
         #
         for n in xrange(len(dataDaysList)):

            thisFile = os.path.join(polarDbDirTag, dataDaysList[n], polarDbFileTag+'*'+xType+'.txt')
            print "[INFO] Day:", dataDaysList[n] ,thisFile
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
            for thisPolarFile in thisFileList:
               if VERBOSE >0 :
                  print "[INFO] polarization FILE: " ,thisPolarFile
               #print "polarDbFileTag",polarDbFileTag
               thisFileTimeLabel = thisPolarFile.split(polarDbFileTag+'.')[1].split('.')[0]
               #print "thisFileTimeLabel",thisFileTimeLabel
               #thisFileTimeLabel = thisPolarFile.split(channelDir+'_')[1].split('.')[0]
               thisFileTime      = UTCDateTime(thisFileTimeLabel)
               if thisFileTime >= tStart and thisFileTime < tEnd:
                  with open(thisPolarFile) as file:
                     if VERBOSE >0 :
                        print "OK, working on ..." + thisPolarFile

                     #
                     # skip the header lines
                     #
                     for i in (1,2):
                        next(file)

                     #
                     # go through individual periods/frequencies
                     #
                     for line in file:

                         #
                         # each row, split column values
                         #
                         values = re.split('\s+',line.strip('.').strip())
                         X      = values[0]
                         #print "values[pn+1]",values[pn+1]
                         V      = str(round(float(values[pn+1]),param.decimalPlaces[variable]))
                         #print "V",V

                         #
                         # save the period/frequency and the value of interest
                         #
                         thisOutDate,thisOutTime = thisFileTimeLabel.split('T')
                         outputFile.write("%s%s%s%s%s%s%s\n" % (thisOutDate,param.separator,thisOutTime.split('.')[0],param.separator,X,param.separator,V))

                  file.close()
   except:
      msgLib. error("failed to open "+outFileName+"\nis 'namingConvention' "+msgLib.param(param,'namingConvention').namingConvention+" set correctly?" +"\n",0)
      sys.exit()
   print "[INFO] OUTPUT FILE: " + outputFileName + "\n"
   outputFile.close()
