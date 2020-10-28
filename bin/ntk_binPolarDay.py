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
   print "                                        configuration file name             net    sta      loc       channel directory  start date   end date[exclusive] x-axis type  verbose on/off"
   print "                                                           |                 |      |        |           |                  |               |               |            |"
   print "                   python ntk_binPolarDay.py   param=binPolarDay        net=NM sta=SLM loc=DASH chandir=BHZ_BHE_BHN start=2009-01-01 end=2009-01-06 type=frequency     mode=0"
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
# find bin for a given value
#
################################################################################################
#
def findBin(value,binStart,binEnd,binCenter):
   for i in xrange(len(binStart)):
      if i == len(binStart)-1:
         if float(value) >= binStart[i] and float(value) <= binEnd[i]:
            return binCenter[i]
      else:
         if float(value) >= binStart[i] and float(value) < binEnd[i]:
            return binCenter[i]
   return float(value)

################################################################################################
#
# Main
#
################################################################################################
#
# NAME: # ntk_binPolarDay.py - a Python script to bin polarization parameters to daily files for a given channel tag and bounding
#                     parameters. The output is similar to those available from IRIS PDF/PSD Bulk Data 
#                     Delivery System (http://www.iris.edu/dms/products/pdf-psd/)
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
#    2015-07-15 IRIS DMC Product Team (Manoch) R0.5.0: Beta release updates
#    2013-06-03 IRIS DMC Product Team (Manoch): created 
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

#
# see if user has provided the run arguments
#

args = getArgs(sys.argv)
if len(args) < 9:
   msgLib.error("missing argument(s)",1)
   usage()
   sys.exit()

#
# import the user-provided parameter file
#
# os.path.dirname(__file__) gives the current directory
#

script = sys.argv[0]
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

#
# RUN ARGUMENTS:
#
network     = getParam(args,'net',msgLib,None)
station     = getParam(args,'sta',msgLib,None)
location    = staLib.getLocation(getParam(args,'loc',msgLib,None))
channelDir  = getParam(args,'chandir',msgLib,None)

#
# polarization files are all HOURLY files with 50% overlap computed as part of the polarization product
# date parameter of the hourly PSDs to start, it starts at hour 00:00:00
#  - HOURLY files YYYY-MM-DD
#
variables        = param.variables
dataDirectory    = param.dataDirectory 
columnTag        = param.variables
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

xType            = getParam(args,'type',msgLib,'frequency') # what the x-axis should represent

#####################################
# find and start reading the polarization files 
#####################################
#
# build the file tag for the polarization files to read, example:
#     NM.SLM.--.BHZ_BHE_BHN_2009-09-01T08:00:00.035645_3600_frequency.txt
#
polarDbDirTag, polarDbFileTag = fileLib.getDir(param.dataDirectory,param.polarDbDirectory,network,station,location,channelDir)

print "\n[INFO] Polar DIR TAG: " + polarDbDirTag
if VERBOSE:
   print "\n[INFO] Polar FILE TAG: " + polarDbFileTag

#####################################
# loop through the windows
#####################################
#
bin = {}
for n in xrange(len(dataDaysList)):
   print "\n[INFO] day ",dataDaysList[n]
   Dfile = []
   Hfile = []
   for column in xrange(len(columnTag)):
      Hfile.append([])
      Dfile.append({})

   thisFile = os.path.join(polarDbDirTag, dataDaysList[n], polarDbFileTag+'*'+xType+'.txt')
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
   for thisPolarFile in thisFileList:
      if VERBOSE >0 :
        print "[INFO] Polarization FILE: " ,thisPolarFile
       
      #thisFileTimeLabel = thisPolarFile.split(polarDbFileTag+'.')[1].split('.')[0]
      thisFileTimeLabel = fileLib.getFileTimes(param.namingConvention,channelDir,thisPolarFile)[0]
      #thisFileTimeLabel = thisPolarFile.split(channelDir+'_')[1].split('.')[0]
      thisFileTime      = UTCDateTime(thisFileTimeLabel)
      thisYear          = thisFileTime.strftime("%Y")   
      thisHour          = thisFileTime.strftime("%H:%M")   
      thisDOY           = thisFileTime.strftime("%j")   
      if thisFileTime >= tStart and thisFileTime < tEnd:
        try:
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
                   values   = re.split('\s+',line.strip())
                   X        = values[0]

                   #
                   # each data column
                   #
                   for column in xrange(len(variables)):
                      #
                      # find the bin for this value and save it in the Hourly file
                      #
                      variable    = variables[column]
                      bins        = param.bins[variable]
                      bin[variable] = []
                      binCount = int((float(bins[1]) - float(bins[0]))/float(bins[2]))+1

                      #
                      # populate the bin values
                      #
                      for i in xrange(binCount+1):
                         bin[variable].append(float(bins[0]) + float(i) * float(bins[2]))

                      #
                      # get the value for this column and bin it
                      # The first column is T or F, so +1
                      #
                      if values[column + 1] == 'nan': 
                         continue
                      V = float(values[column + 1])
                      thisFreq,thisBin = np.histogram(V,bins=bin[variable])
                      if V >= bins[0] and V <= bins[1]:
                         if len(np.nonzero(thisFreq)[0]) <= 0:
                            continue
                         nonzeroElement = np.nonzero(thisFreq)[0][0]
                         thisLine = "%s%s%s%s%g" % (thisHour,param.separator,X,param.separator,thisBin[nonzeroElement])
                         Hfile[column].append(thisLine)
                      key = X
                      if key in Dfile[column].keys():
                         Dfile[column][key] += thisFreq
                      else:
                         Dfile[column][key] = thisFreq

           file.close()
           if VERBOSE >0 :
              print "done reading the file "
        except:
           msgLib. error("failed to open "+thisPolarFile+"\nis 'namingConvention' "+msgLib.param(param,'namingConvention').namingConvention+" set correctly?" +"\n",0)
           sys.exit()

   #####################################
   # open the output file
   #####################################
   #
   # each data column
   #
   for column in xrange(len(columnTag)):
      print "\n[INFO] variable",columnTag[column]
      pdfDirTag, pdfFileTag = fileLib.getDir(param.dataDirectory,param.pdfDirectory,network,station,location,channelDir)
      fileLib.makePath(pdfDirTag)
      thisPath = os.path.join(pdfDirTag,'Y'+thisYear)
      fileLib.makePath(thisPath)
      thisPath = os.path.join(thisPath, columnTag[column])
      fileLib.makePath(thisPath)
      outputFile = os.path.join(thisPath,'D' + thisDOY + '.bin')
      print "[INFO] DAILY OUTPUT FILE: " + outputFile
      with open(outputFile, 'w') as outputFile:
         for key in sorted(Dfile[column].keys()):
            if VERBOSE:
               print "[INFO] KEY:", key
            for ii in xrange(len(Dfile[column][key])):
               outputFile.write("%s%s%s%s%g\n" % (key,param.separator,bin[columnTag[column]][ii],param.separator,Dfile[column][key][ii]))
      outputFile.close()

      if param.pdfHourlySave > 0:
         thisPath = os.path.join(thisPath,param.pdfHourlyDirectory)
         fileLib.makePath(thisPath)
         outputFile = os.path.join(thisPath,'H' + thisDOY + '.bin')
         print "[INFO] HOURLY OUTPUT FILE: " + outputFile
         with open(outputFile, 'w') as outputFile:
            for i in xrange(len(Hfile[column])):
               outputFile.write("%s\n"%Hfile[column][i])
         outputFile.close()
      else:
        print "[INFO] hourly Polar save option turned off"
   
