version = "R 0.6.0"
################################################################################################
#
#  usage message
#
################################################################################################
#
def usage():
   print "\n\nUSAGE("+version+"):\n\n"
   print "ntk_computePower.py - a Python script to calculate power of each PSD window over selected bin period bands\n\n"
   print "                         configuration file name           net     sta      loc    chan     PSD file type  mode=0       run with minimum message output"
   print "                                         |                 |       |        |        |        |            | = verbose run in verbose mode"
   print "                                         |                 |       |        |        |        |            |"
   print "                                         |                 |       |        |        |        |            |          'combined' PSD file to read"
   print "                                         |                 |       |        |        |        |            |              |"
   print " python bin/ntk_computePower.py   param=computePower   net=NM sta=SLM loc=DASH chan=BHZ  type=period mode=verbose  file=NM.SLM.--.BHZ.2009-01-01T00:00:00.2010-01-01T00:00:00_period.txt"
   print "\n\n\n"
   print "The input PSD file should have the same format as the output of the ntk_extractPsdHour.py script (see NTK PSD/PDF bundle)"
   print "For more information visit:"
   print ""
   print "     http://ds.iris.edu/ds/products/noise-toolkit-pdf-psd/"
   print "\n\n\n"

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
# NAME: # ntk_computePower.py - a Python script to calculate power of each PSD window over selected bin period bands
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
# PDF files
#
# HISTORY:
#
#    2015-04-22 Manoch: file name correction
#    2014-11-24 Manoch: Beta release (R0.5) to compute power based on a combined PSD file
#               with format similar to output of the ntk_extractPsdHour.py script (see NTK PSD/PDF bundle)
#    2013-10-07 Manoch: revision for production test
#    2013-03-14 Manoch: created
#
################################################################################################
#
#
# PACKAGES:
#
import glob,sys,re,os,math
import numpy as np
from obspy.core import UTCDateTime

#
# import the Noise Toolkit libraries
#
# os.path.dirname(__file__) gives the current directory
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
if len(args) < 8:
   msgLib.error("missing argument(s)",1)
   usage()
   sys.exit()

script = sys.argv[0]

#
# import the user-provided parameter file
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

VERBOSE = 0
arg = getParam(args,'mode',msgLib,1)
if arg == 'verbose':
      msgLib.message("VERBOSE RUN")
      VERBOSE        = 1
else:
      #
      # if mode is >1, then full debug info is printed
      #
      VERBOSE = int(arg)

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

network      = getParam(args,'net',msgLib,None)
station      = getParam(args,'sta',msgLib,None)
location     = staLib.getLocation(getParam(args,'loc',msgLib,None))
channel      = getParam(args,'chan',msgLib,None)
type         = getParam(args,'type',msgLib,None)

#
# NOTE: the input PSD file is assumed to have the same format as the output of the ntk_extractPsdHour.py script
#
psdFile         = getParam(args,'file',msgLib,None)
psdDirectory    = os.path.join(param.dataDirectory,param.psdDirectory) 
psdFileName     = os.path.join(psdDirectory,".".join([network,station,location]),channel,psdFile)

#
# check to see if the PSD file exists
#
if not os.path.isfile(psdFileName):
   msgLib.error("could not find the PSD file ["+psdFileName+"]",2)
   sys.exit()

#
# create the power directories as needed
#
powerDirectory  = os.path.join(param.dataDirectory,param.powerDirectory)
if not os.path.exists(powerDirectory):
      os.makedirs(powerDirectory)

powerDirectory  = os.path.join(powerDirectory,".".join([network,station,location]))
if not os.path.exists(powerDirectory):
      os.makedirs(powerDirectory)

powerDirectory  = os.path.join(powerDirectory,channel)
if not os.path.exists(powerDirectory):
      os.makedirs(powerDirectory)

#
# open the power file
#
powerFileName   = os.path.join(powerDirectory,psdFile.replace("_"+type,"").replace("."+type,""))
outFile         = open(powerFileName, 'w')

#
# write the output header 
#
outFile.write("Periods\n")
outFile.write("%20s %20s" % ("Date","Time"))
for k in xrange(len(binStart)):
   outFile.write("%20s" % (str(bins[k]) +" ("+str(binStart[k])+'-'+str(binEnd[k])+")"))
outFile.write("\n")

print "\nPSD FILE  :", psdFileName
print "\nPOWER FILE:", powerFileName

#####################################
#
# loop through the PSD file, compute bin powers and write them out
#
#####################################
previousDate = None
previousTime = None

with open(psdFileName) as inFile:
    #
    # init the records
    #
    period = []
    psd    = []
    power  = []

    #
    # read the entire PSD file
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
    # process line by line
    #
    for i in xrange(lineCount):
        line = lines[i]
        #
        # each row, split columns
        #
        date,time,thisX,thisY = re.split('\s+',line.strip(' ').strip())

        #
        # depending on type, recompute X if needed
        #
        if type == 'frequency':
           thisX = 1.0/float(thisX)

        if previousDate == None:
           previousDate = date
           previousTime = time

        #
        # group lines based on date and time
        # save the period and value of interest
        #
        if (date == previousDate and time == previousTime) and i < lineCount-1:
           period.append(float(thisX))
           psd.append(float(thisY))

        #
        # new date-time, jump out and compute power for the previous date-time
        #
        else:
           previousLine = line

           #
           # save the values from the last row, if we are at the end of the file
           #
           if i == lineCount -1:
              period.append(float(thisX))
              psd.append(float(thisY))

           power = np.zeros(len(bins))

           ######################################
           # compute power
           ######################################
           #
           if len(period)>0:

              #
              # sort them to keep the code simple
              #
              period, psd = zip(*sorted(zip(period, psd)))

              #
              #
              # go through the records and for each bin convert to power from dB
              # NOTE: PSD is equal to the power as the a measure point divided by the width of the bin
              #       PSD = P / W
              #       log(PSD) = Log(P) - log(W)
              #       log(P)   = log(PSD) + log(W)  here W is width in frequency
              #       log(P)   = log(PSD) - log(Wt) here Wt is width in period
              #
              for k in xrange(len(bins)):
                 if VERBOSE > 1 : 
                     print "==================================="
                     print " CHAN",channel
                     print " DATE",previousDate,previousTime
                     print "PERIOD: ",bins[k]," from ",str(float(binStart[k]))," to ",str(float(binEnd[k]))
                     print "==================================="

                 #
                 # for each bin perform rectangular integration to compute power
                 # power is assigned to the period at the begining of the interval
                 #      _   _
                 #     | |_| |
                 #     |_|_|_|
                 #  

                 for j in xrange(0,len(psd)-1):
                    #if VERBOSE >0 :
                    #   print "    \nCHECKING: is "+str(float(period[j]))+" between "+str(float(binStart[k]))+ " to "+str(float(binEnd[k]))

                    #
                    # since to calculate the area we take the width between point j and j+1, as a result we 
                    # only accept the point if it falls before the end point, hence (<)
                    #
                    if(float(period[j]) >= float(binStart[k]) and float(period[j]) < float(binEnd[k])):

                       #
                       # here we want to add the area just before the first sample if our window start
                       # does not fall on a data point. We set start of the band as the start of our window
                       #
                       if j > 0 and  (float(period[j]) > float(binStart[k]) and float(period[j-1]) < float(binStart[k])):
                             if VERBOSE > 1 :
                                  print j,"ADJUST THE BAND START ",period[j]," BAND NOW GOES"
                                  print "    FROM 1: "+str(float(binStart[k]))+ " to "+str(float(period[j+1]))
                             binWidthHz = abs((1.0/float(binStart[k]))-(1.0/float(period[j+1])))
                       elif j == 0 and float(period[j]) > float(binStart[k]):
                             if VERBOSE > 1 :
                                  print j,"ADJUST THE BAND START ",period[j]," BAND NOW GOES"
                                  print "    FROM 1: "+str(float(binStart[k]))+ " to "+str(float(period[j+1]))
                             binWidthHz = abs((1.0/float(binStart[k]))-(1.0/float(period[j+1])))

                       #
                       # here we want to adjust the width if our window end
                       # does not fall on a data point
                       # 
                       elif j < len(psd)-1 and (float(period[j]) < float(binEnd[k]) and float(period[j+1]) >= float(binEnd[k])):
                            if VERBOSE > 1 :
                               print j,"ADJUST THE BAND END ",period[j], " BAND NOW GOES"
                               print "    \nFROM 2: "+str(float(period[j]))+ " to "+str(float(binEnd[k]))
                            binWidthHz = abs((1.0/float(period[j])) - (1.0/float(binEnd[k])))
                       elif j == len(psd)-1 and float(period[j]) < float(binEnd[k]):
                            if VERBOSE > 1 :
                               print j,"ADJUST THE BAND END ",period[j], " BAND NOW GOES"
                               print "    \nFROM 2: "+str(float(period[j]))+ " to "+str(float(binEnd[k]))
                            binWidthHz = abs((1.0/float(period[j])) - (1.0/float(binEnd[k])))
                       #
                       # for the rest in between
                       # 
                       else:
                            if VERBOSE > 1 :
                               print j,"NO ADJUSTMENT"
                               print "    BAND FROM 3: "+str(float(period[j]))+ " to "+str(float(period[j+1]))
                            binWidthHz = abs((1.0 /float(period[j])) - (1.0 / (float(period[j+1]))))
   
                       if VERBOSE > 1:
                            print "    BIN WIDTH "+str(binWidthHz)+"Hz"
                     
                       power[k] += (math.pow(10.0,float(psd[j])/10.0) * binWidthHz) 
                       if VERBOSE > 1:
 	                print "POWER ",psd[j]," ----> ",(math.pow(10.0,float(psd[j])/10.0) * binWidthHz)

                    else:
                       if VERBOSE >1:
                          print j,period[j]," REJECTED"
                 if VERBOSE >1 :
    	               print "TOTAL POWER ",power[k]
              outFile.write("%20s %20s" % (previousDate, previousTime))
              for index in xrange(0,len(binStart)):
                outFile.write("%20.5e" % (power[index]))
              outFile.write("\n")

              #
              # init the records
              #
              period = []
              psd    = []
              power  = []

              #
              # capture the first line tht was left over from previous itteration
              #
              date,time,thisX,thisY = re.split('\s+',previousLine.strip(' ').strip()) 
              if type == 'frequency':
                 thisX = 1.0/float(thisX)
              period.append(float(thisX))
              psd.append(float(thisY))
              previousDate = date
              previousTime = time


outFile.closed
