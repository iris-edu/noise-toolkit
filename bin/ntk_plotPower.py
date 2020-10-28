version = "R 0.6.0"
################################################################################################
#
# outout usage message
#
################################################################################################
#
def usage():
   print "\n\nUSAGE("+version+"):\n\n"
   print "ntk_plotPower.py - a Python script to plot median power obtained from "
   print "the median power file produced by ntk_medianPower.py\n\n"
   print "                               configuration  net   station     loc     chan     start date time     end date time            smoothing window (hours)"
   print "                                    file       |      |          |       |           |                      |                       |                 bin to process(name as defined in the parameter file)"
   print "                                     |         |      |          |       |           |                      |                       |                       |     "
   print "                                     |         |      |          |       |           |                      |                       |                       |       maximum value for the y-axis"
   print "                                     |         |      |          |       |           |                      |                       |  input median PSD power file  |     "
   print "                                     |         |      |          |       |           |                      |                       |           |           |       |      | verbose mode on/off (0 or verbose)"
   print "   python ntk_plotPower.py param=plotPower net=NM sta=SLM  loc=DASH chan=BHZ start=2009-03-01T00:00:00 end=2009-03-31T00:00:00  win=12  file=fileName   bin=SM ymax=3 mode=0"
   print "  "
   print "   INPUT:"
   print "  "
   print "   The PSD median power file created by ntk_medianPower.py "
   print "   "
   print "   The output windowed PDFs are stored under the "
   print "   corresponding window directory as follows:"
   print "  "
   print "   Win(h)     Dir"
   print "     6    ->  6h"
   print "    12    -> 12h"
   print "    24    ->  1d"
   print "    96    ->  4d"
   print "   384    -> 16d"
   print "  "
   print "  "
   print " period range index:" 
   print " Index    Period range"
   print " 1        1-5 local microseism"
   print " 2       5-10 secondary microseism "
   print " 3      11-30 primary microseism"
   print " 4     50-200 Earth hum"
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
################################################################################################
#
# ntk_plotPower.py - a Python script to plot median power obtained from 
#                   the median power file produced by ntk_medianPower.py
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
#    2014-11-24 Manoch: R0.5, modified the inpot format to read
#               median power file produced by ntk_medianPower.py
#    2013-10-07 Manoch: revision for production test
#    2013-03-14 Manoch: created partially
#
#
################################################################################################
#

#
# PACKAGES:
#
from matplotlib.colors import LinearSegmentedColormap
from obspy.core import UTCDateTime
from matplotlib.dates import  DateFormatter, WeekdayLocator, HourLocator, \
     YearLocator, MonthLocator, DayLocator, WeekdayLocator, MONDAY
import matplotlib.cm as cm
import glob,sys,re,os
import numpy as np
import matplotlib.pyplot as plt
import datetime

#
# import the Noise Toolkit libraries
#
libraryPath      = os.path.join(os.path.dirname(__file__), '..', 'lib')
sys.path.append(libraryPath)

import msgLib  as msgLib
import fileLib as fileLib
import staLib  as staLib

script = sys.argv[0]

#
# os.path.dirname(__file__) gives the current directory
#
args = getArgs(sys.argv)

#
# see if user has provided the run arguments
#
if len(args) < 11:
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

#
# VERBODE 
#
VERBOSE  = 0
arg = getParam(args,'mode',msgLib,VERBOSE)
print "MODE:",arg
if arg == 'verbose':
      msgLib.message("VERBOSE RUN")
      VERBOSE        = True

if VERBOSE:
   print "\n\n[INFO] script: %s" % script
   print "[INFO] ARG#",len(sys.argv)
   print "[INFO] ARGS",sys.argv


#
# set parameters for the time axis labeling
#
years         = YearLocator()  # every year
months        = MonthLocator() # every month
days          = DayLocator()   # every day
weeks         = WeekdayLocator(byweekday=MONDAY, interval=1)
yearsFmt      = DateFormatter('%Y')
monthsFmt     = DateFormatter('%m/%Y')
daysFmt       = DateFormatter('%m/%d')

#
# read the parameters from the configuration file
#
columnTag     = param.columnTag
columnLabel   = param.columnLabel
dotColor      = param.dotColor
dotSize       = param.dotSize

network       = getParam(args,'net',msgLib,None)
station       = getParam(args,'sta',msgLib,None)
if VERBOSE:
   print "NET: ",network
   print "STA: ",station

location         = staLib.getLocation(getParam(args,'loc',msgLib,None))
channel          = getParam(args,'chan',msgLib,None)
start            = getParam(args,'start',msgLib,None)
end              = getParam(args,'end',msgLib,None)
windowWidthHour  = getParam(args,'win',msgLib,None)
ymax             = getParam(args,'ymax',msgLib,None)

#
# moving window length in hours
#  - 6hrs 1d(24h) 4d(96h) 16d(384h) ...
#
windowTag     = fileLib.getWindowTag(windowWidthHour)
if VERBOSE:
   print "WINDOW: "+windowWidthHour

periodBin     = getParam(args,'bin',msgLib,None)
if periodBin not in param.bins:
  msgLib.error("bad bin name ["+periodBin+"]",2)
  sys.exit()

if VERBOSE:
   print "PERIOD BIN: "+str(periodBin), 'from',param.binStart[periodBin],'to',param.binEnd[periodBin]

binIndex      = param.binIndex[periodBin]
rangeLabel    = param.rangeLabel[binIndex]
factor        = param.factor[binIndex]
factorLabel   = param.factorLabel[binIndex]
ymin          = param.ymin[binIndex]
yticks        = param.yticks[binIndex]
ytickLabels   = param.ytickLabels[binIndex]
imageTag      = param.imageTag[binIndex]

yLabel = rangeLabel + factorLabel

fileName     = getParam(args,'file',msgLib,None)
startDate    = getParam(args,'start',msgLib,None)
startYear    = int(startDate.split("-")[0])
xStartL      = startDate.split('T')[0]
startDate    = UTCDateTime(startDate)

endDate      = getParam(args,'end',msgLib,None)
endYear      = int(endDate.split("-")[0])
xEndL        = endDate.split('T')[0]
endDate      = UTCDateTime(endDate)

xminL       = datetime.datetime(int(xStartL.split('-')[0]),int(xStartL.split('-')[1]),int(xStartL.split('-')[2]),0,0,0)
xmaxL       = datetime.datetime(int(xEndL.split('-')[0]),int(xEndL.split('-')[1]),int(xEndL.split('-')[2]),0,0,0)

if VERBOSE:
   print "START: ",startDate
   print "END: ",endDate
   print "YMAX: ",str(ymax)

#
# set the target for the Power directory. The associated window directory
# is under the corresponding power directory also
#
powerFileTag        = []
powerFilePath       = []

title = " ".join([fileLib.getTag(".",[network,station.replace(',','+'),location]),periodBin,"with",windowTag,"sliding window"])

#
# plot bg color
#
#bgColor = (0.98,0.34,0.98)
bgColor = (1,1,1)

#
# start reading the PDF file
#
#
# initialize the limits
#
X    = []
Y    = []
XLabel = []
powerDirectory = os.path.join(param.dataDirectory,param.powerDirectory)
fileName = os.path.join(powerDirectory,".".join([network,station,location]),channel,windowTag,fileName)
with open(fileName) as file:
  if VERBOSE:
            print "OPENING: "+ fileName

  #
  # read the entire power file
  #
  lines    = file.readlines()

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
  # get the time of each line and the power, skip headers
  #
  powerTime = []
  for i in xrange(2,lineCount):
      values   = re.split('\s+',lines[i].strip(' ').strip())
      thisTime = UTCDateTime(values[0])
      if thisTime >= startDate and thisTime <= endDate:
         date , time = values[0].split('T')
         dateValues = date.split('-')
         timeValues = time.split(':')
         X.append(datetime.datetime(int(dateValues[0]),int(dateValues[1]),int(dateValues[2]),int(timeValues[0]),int(timeValues[1])))
         Y.append(float(values[binIndex])*factor) 

if len(X) <= 1:
   msgLib.error("No data found",2)
   sys.exit()

#
# convert the column XYZ data to grid for plotting
#
if VERBOSE:
   print "PLOT SIZE:",param.plotSize
fig = plt.figure(figsize=param.plotSize)

fig.set_facecolor('w')

xStart  = datetime.datetime(int(xStartL.split('-')[0]),int(xStartL.split('-')[1]),int(xStartL.split('-')[2]),0,0,0) + datetime.timedelta(seconds=7200)
xEnd    = datetime.datetime(int(xEndL.split('-')[0]),int(xEndL.split('-')[1]),int(xEndL.split('-')[2]),00,00,00) - datetime.timedelta(seconds=7200)

for i in xrange(0,1):
    ax = fig.add_subplot(1, 1, i + 1)
    if VERBOSE:
       print "DOT COLOR:",dotColor[i]
    ax.scatter(X, Y, s=dotSize, marker='o', alpha=1.0, color=dotColor[i], label=columnLabel[i+1])

    #
    # ".   " is added for proper spacing
    #
    ax.text(xStart, (0.9)*float(ymax), ".    "+".".join([network,station,channel]),  horizontalalignment='left', fontsize=10, weight='bold', color=dotColor[i])

    #
    # "   ." is added for proper spacing
    #
    #ax.text(xEnd, 0.9*float(ymax), columnLabel+' '+yLabel+"   .",  horizontalalignment='right', fontsize=10, weight='bold')
    
    ax.set_xticklabels([])
    ax.set_ylabel(yLabel, fontsize='small')
    plt.title(title)
    plt.ylim(ymin,float(ymax))
    plt.xlim(xminL,xmaxL)

#
# format the ticks for the date axis depending on the duration
#
ax.xaxis_date()
#daterange = int((UTCDateTime(endDate+"T00:00:00") - UTCDateTime(startDate+"T00:00:00"))/86400.0)
daterange = 15
if(daterange < 21 ):
   ax.xaxis.set_major_locator(days)
   ax.xaxis.set_major_formatter(daysFmt)
elif(daterange < 45 ):
   ax.xaxis.set_major_locator(weeks)
   ax.xaxis.set_major_formatter(daysFmt)
elif(daterange < 90):
   ax.xaxis.set_major_locator(weeks)
   ax.xaxis.set_major_formatter(monthsFmt)
elif(daterange < 400):
   ax.xaxis.set_major_locator(months)
   ax.xaxis.set_major_formatter(monthsFmt)
else:
   ax.xaxis.set_major_locator(years)
   ax.xaxis.set_major_formatter(yearsFmt)

#
# rotate the x labels by 60 degrees
#
for xlab in ax.get_xticklabels():
   xlab.set_rotation(60)

fig.subplots_adjust(top=0.95, right=0.95, bottom=0.2, hspace=0)
imageDirectory = os.path.join(param.ntkDirectory,param.imageDirectory)
fileLib.makePath(imageDirectory)
imageFile = os.path.join(imageDirectory,"_".join([fileName.replace('.txt',''),imageTag,windowTag]))
plt.savefig(imageFile+".eps",format="eps",dpi=300)
print "image file:",imageFile+".eps"
plt.savefig(imageFile+".png",format="png",dpi=150)
print "image file:",imageFile+".png"
plt.show()

