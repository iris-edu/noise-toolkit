import os
import msgLib as msg
from   time import time

#
# History:
#    2014-10-22 Manoch: added support for Windows installation
#
################################################################################################
#
# makePath
#
# function to check for existance of a directory and creates it
# if it does not exist (including the parent directories)
# the path must be an absolute path (start with "/") 
#
################################################################################################
#
def makePath(directory):
    "Checks a directory for existance and if it does not exist, "
    "create it. If needed, create all parent directories."

    #
    # the path must be an absolute path (start with "/") 
    #
    if not os.path.isabs(directory):
        print 'ERR [checkMakePath]: pat must be an absolute path'
        return None

    #
    # create directories
    #
    thisPath = os.path.abspath(directory)
    if not os.path.exists(thisPath):
            os.makedirs(thisPath)
    return thisPath

################################################################################################
#
# create tags for directories and files
#
################################################################################################
#
def getDir(dataDirectory,subDirectory,network,station,location,channel):
   directoryTag  = os.path.join(dataDirectory,subDirectory, getTag(".",[network,station,location]),channel)
   fileTag       = getTag(".",[network,station,location,channel])
   return directoryTag,fileTag

################################################################################################
#
# create tag for the files and directories
#
################################################################################################
#
def getTag(tagChar,tagList):
   tag  = tagChar.join(tagList)
   return tag

################################################################################################
#
# create smoothing window tag based on its length
# moving window length in hours
#
#  - 6hrs 12hrs 1d(24h) 4d(96h) 16d(384h)
#
################################################################################################
#
def getWindowTag(windowWidthHour):
    if(int(windowWidthHour) < 24):
        windowTag = windowWidthHour + "h"
    else:
	  windowTag = str(int(int(windowWidthHour)/24)) + "d"

    return windowTag

################################################################################################
#
# create file name
#
# PQLX if file name contains time, it will be in HH24:MM:SS format
# WINDOWS if file name contains time, it will be in HH24_MM_SS format
#
################################################################################################
#
def getFileName(namingConvention,filePath,tagList):
    if namingConvention != "PQLX":
       for i in xrange(len(tagList)):
           tagList[i] = tagList[i].replace(':','_')
    thisTag = getTag(".",tagList)+".txt"
    thisFileName = os.path.join(filePath,thisTag)

    return thisFileName

################################################################################################
#
# get file times by extracting file start and end times from the file name
# time is assumed to be included in the file name in CHA.Time1.Time2 format
# Time1 and Time2 are returned as string
#
# PQLX if file name contains time, it will be in HH24:MM:SS format
# WINDOWS if file name contains time, it will be in HH24_MM_SS format
#
################################################################################################
#
def getFileTimes(namingConvention,channel,filename):
  startTime = filename.split(channel+'.')[1].split('.')[0]
  endTime   = filename.split(channel+'.')[1].split('.')[1]
  if namingConvention != "PQLX":
      startTime = startTime.replace('_',':')
      endTime   = endTime.replace('_',':')

  return (startTime, endTime)

################################################################################################
#
# timeIt - compute elapsed time since the last cal
#
################################################################################################
#
def timeIt(who,t0):
   t1 = time()
   dt = t1 - t0
   t = t0
   if dt > 0.05:
      msg.message(" ".join([who,"[TIME]",str(dt),"seconds"]))
      t = t1
   return t

