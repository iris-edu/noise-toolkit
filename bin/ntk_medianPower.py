version = "R 0.6.0"
################################################################################################
#
# usage message
#
################################################################################################
#
def usage():
   print "\n\nUSAGE("+version+"):\n\n"
   print "ntk_medianPower.py - a Python script to calculates median power for a given window length from the computed PSD powers\n\n"
   print "                           parameter file         net    sta     loc      chan     start                      end             smoothing window"
   print "                                     |             |      |       |         |         |                        |                    (hours)   "
   print "                                     |             |      |       |         |         |                        |                       |      verbose mode (0 or verbose)"
   print "                                     |             |      |       |         |         |                        |                       |        |"
   print "                                     |             |      |       |         |         |                        |                       |        |            PSD power file name"
   print "                                     |             |      |       |         |         |                        |                       |        |            |"
   print "                                     |             |      |       |         |         |                        |                       |        |            |"
   print " python ntk_medianPower.py param=medianPower  net=NM sta=SLM loc=DASH chan=BHZ start=2009-02-27T00:00:00 end=2009-04-02T00:00:00  win=12 mode=verbose file=NM.SLM.--.BHZ.2009-02-27T00:00:00.2009-04-02T00:00:00.txt"
   print ""
   print " INPUT:"
   print ""
   print " The input PSD power file is expected to be under the 'POWER'"
   print " directory and should have the same format as the output of ntk_computePower.py script."
   print " The 'computePower' parameter file can be used as the input parameter file for this script."
   print ""
   print " OUTPUT:"
   print " The smoothed PDFs are stored inthe 'POWER' directory under the "
   print " corresponding window directory:"
   print ""
   print " Win(h)     Dir"
   print "   6    ->  6h"
   print "  12    -> 12h"
   print "  24    ->  1d"
   print "  96    ->  4d"
   print " 384    -> 16d"
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
# NAME:
#
# ntk_medianPower.py - a Python script to calculates median power for a given window length from
#                      the computed PSD powers
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
# HISTORY:
#
#    2015-02-20 Manoch: addressed the output file naming issue
#    2014-11-24 Manoch: Beta (R0.5) release
#    2013-10-07 Manoch: revision for production test
#    2013-03-14 Manoch: created partially
#
################################################################################################

#
# PACKAGES:
#

import glob,sys,re,os
import numpy as np
from obspy.core import UTCDateTime

#
# import the Noise Toolkit libraries
#
ntkDirectory   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
libraryPath    = os.path.join(ntkDirectory, 'lib')
sys.path.append(libraryPath)

import msgLib  as msgLib
import fileLib as fileLib
import staLib  as staLib

#
# see if user has provided the run arguments
#
args = getArgs(sys.argv)
if len(args) < 10:
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
paramPath      = os.path.join(ntkDirectory, 'param')

#
# check to see if param file exists
#
if os.path.isfile(os.path.join(paramPath,paramFile+".py")):
   sys.path.append(paramPath)
   param = importlib.import_module(paramFile)
else:
   msgLib.error("bad parameter file name ["+paramFile+"]",2)
   usage()
   sys.exit()

#
# VERBODE 
#
VERBOSE  = 0
arg = getParam(args,'mode',msgLib,VERBOSE)
if arg == 'verbose':
      msgLib.message("VERBOSE RUN")
      VERBOSE        = 1

if VERBOSE >0 :
   print "\n\n[INFO] script: %s" % script
   print "[INFO] ARG#",len(sys.argv)
   print "[INFO] ARGS",sys.argv

#
# bin ranges
#
binStart   = []
binEnd     = []
bins       = param.bins
for bin in bins:
   try:
     binStart.append(param.binStart[bin])
     binEnd.append(param.binEnd[bin])
   except Exception, e:
      msgLib.error("bad band ["+bin+"] in param file",2)
      sys.exit()

if VERBOSE >0 :
   print "\n\nPERIOD BIN START: " + str(binStart)
   print "\nPERIOD BIN ENDis: " + str(binEnd)

network          = getParam(args,'net',msgLib,None)
station          = getParam(args,'sta',msgLib,None)
location         = staLib.getLocation(getParam(args,'loc',msgLib,None))
channel          = getParam(args,'chan',msgLib,None)
start            = getParam(args,'start',msgLib,None)
end              = getParam(args,'end',msgLib,None)
windowWidthHour  = getParam(args,'win',msgLib,None)

#
# NOTE: the input PSD file is assumed to have the same format as the output of the ntk_extractPsdHour.py script
#
powerFile        = getParam(args,'file',msgLib,None)
powerDirectory   = os.path.join(param.dataDirectory,param.powerDirectory)
powerDirectory   = os.path.join(powerDirectory,".".join([network,station,location]),channel)
powerFileName    = os.path.join(powerDirectory,powerFile)

#
# check to see if the power file exists, then read its content
#
if not os.path.isfile(powerFileName):
   msgLib.error("could not find the POWER file ["+powerFileName+"]",2)
   sys.exit()

with open(powerFileName) as inFile:
    #
    # read the entire power file
    #
    lines    = inFile.readlines()

    #
    # find the last non-blank line
    #
    lineCount = len(lines)
    for i in xrange(1,len(lines)):
       line = lines[-i].strip()
       if len(line) > 0:
          lineCount = len(lines) -i +1
          break
    if VERBOSE:
       print "INPUT:",lineCount,"lines"

#
# get the time of each line, skip headers
#
powerTime = []
for i in xrange(2,lineCount):
   values   = re.split('\s+',lines[i].strip(' ').strip())
   powerTime.append(UTCDateTime(values[0]+'T'+values[1]))

#
# window length in hours
#
windowTag         = fileLib.getWindowTag(windowWidthHour)
print "smoothing window",windowWidthHour,"hours"

powerDirectory  = os.path.join(powerDirectory,windowTag)
if not os.path.exists(powerDirectory):
      os.makedirs(powerDirectory)

#
# window length in hours and second plus the half window length
# base on these calculate number of shifts that will be performed
#
windowWidthSecond = float(windowWidthHour) * 3600.0
windowShiftSecond = param.windowShiftSecond
print "wind length and shift in seconds",windowWidthSecond,windowShiftSecond
startTime         = UTCDateTime(start) - (windowWidthSecond/2.0) # we want the first sample at startTime
endTime           = UTCDateTime(end)   + (windowWidthSecond/2.0)
duration          = endTime - startTime # seconds to process
nShift            = int(float(duration / windowShiftSecond))

#
# place the median directory under the power directory
#

if VERBOSE:
    print "POWER PATH: " ,powerDirectory

if(not fileLib.makePath(powerDirectory)):
    msgLib.error("Error, failed to access "+ powerDirectory)
    sys.exit(1)

#outPowerFileName = fileLib.getFileName(param.namingConvention,powerDirectory,[".".join([network,station,location]), startTime.strftime("%Y-%m-%dT%H:%M:%S.0") , windowTag])
outPowerFileName = fileLib.getFileName(param.namingConvention,powerDirectory,[powerFile.replace('.txt','') , windowTag])

#
# open the output file
#
with open(os.path.join(powerDirectory,outPowerFileName),'w') as outFile: 

   #
   # write the output header
   #
   outFile.write("Period\n")
   outFile.write("%20s" % ("Date-Time"))
   for k in xrange(len(binStart)):
      outFile.write("%20s" % (str(bins[k]) +" ("+str(binStart[k])+'-'+str(binEnd[k])+")"))
   outFile.write("\n")

   #
   # loop through the windows
   #
   for n in xrange(0,nShift+1):

      #
      # get start and end of the current window
      #
      thisWindowStart = startTime + float(n * windowShiftSecond)
      thisWindowEnd   = thisWindowStart + windowWidthSecond
      centerTime      = thisWindowStart + (thisWindowEnd-thisWindowStart)/2.0
      if centerTime < UTCDateTime(start) or centerTime > UTCDateTime(end):
         continue

      #
      # VERBOSE
      #
      if VERBOSE :
         print "   "
         print "START: "+ thisWindowStart.strftime("%Y-%m-%dT%H:%M:%S.0")
         print "END: " + thisWindowEnd.strftime("%Y-%m-%dT%H:%M:%S.0")
         thisCenter  = thisWindowStart + (thisWindowEnd-thisWindowStart)/2.0
      print "[INFO] POINT: " + centerTime.strftime("%Y-%m-%dT%H:%M:%S.0")

      #
      # initialize the list that will hold all the extracted hourly Power
      #
      allPower   = []
      for i in xrange(len(bins)):
         allPower.append([])

      #
      # cycle through all the power lines for this window and extract the values that fall in this window
      #
      for p in xrange(2,lineCount):
         if powerTime[p-2] >= thisWindowStart and powerTime[p-2] <= thisWindowEnd:
            #if VERBOSE:
               #print thisWindowStart,"<=",powerTime[p-2],"<=", thisWindowEnd
            #
            # each row, split column values
            # columns are:
            #     Date      Time 
            #     values[0] values[1]  values[2]  values[3] ...
            #
            values = re.split('\s+',lines[p].strip(' ').strip())

            #
            # save the the value of interest (start at column 2, 0=Date and 1=Time)
            #
            for i in xrange(len(bins)):
               allPower[i].append(float(values[2+i]))

      #
      # Done, write out the results
      #
      if len(allPower[0]) > 0:
         outFile.write("%20s" % (centerTime.strftime("%Y-%m-%dT%H:%M:%S.0")))
         for i in xrange(len(bins)):
            outFile.write("%20.5e" % (np.median(allPower[i])))
         outFile.write("\n")
outFile.close()
print "OUTPUT",os.path.join(powerDirectory,outPowerFileName)
