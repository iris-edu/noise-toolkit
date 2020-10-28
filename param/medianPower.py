import os
import common

#
# how file naming is donet
#
namingConvention = common.namingConvention

#
# initialize a few parametrs
#
# PSD files are all HOURLY files with 50% overlap
#
VERBOSE        = 0         # thurn the verbose mode on or off
ntkDirectory   = common.ntkDirectory
dataDirectory  = common.dataDirectory
psdDirectory   = common.psdDirectory
powerDirectory = common.powerDirectory

windowShiftSecond = 600.0

#
# periods in second for bins of Interest:
#       local noise for stations near shore
#            |
#            |   secondary microseism
#            |           |
#            |           |   primary microseis
#            |           |       |
#            |           |       |    Earth hum
#            |           |       |        |
binStart = {'local':1, 'SM':5, 'PM':11, 'HUM':50}
binEnd   = {'local':5, 'SM':10,'PM':30, 'HUM':200}
bins     = ['local','SM','PM','HUM'] # bins will be used to order the output
