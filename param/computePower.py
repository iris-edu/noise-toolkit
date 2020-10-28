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
ntkDirectory   = common.ntkDirectory
dataDirectory  = common.dataDirectory
psdDirectory   = common.psdDirectory
powerDirectory = common.powerDirectory

#
#  the following bins will be used to group powers within a period band
#
#       local noise for stations near shore
#            |
#            |   secondary microseisms
#            |       |
#            |       |   primary microseisms
#            |       |    |
#            |       |    |    Earth hum
#            |       |    |     |
bins     = ['LM','SM','PM','HUM'] 
binIndex = {'LM':1, 'SM':2,'PM':3, 'HUM':4}

#
# period bands in second for bins of Interest:
#       local noise for stations near shore
#            |
#            |   secondary microseism
#            |           |
#            |           |   primary microseis
#            |           |       |
#            |           |       |    Earth hum
#            |           |       |        |
binStart = {'LM':1, 'SM':5, 'PM':11, 'HUM':50}
binEnd   = {'LM':5, 'SM':10,'PM':30, 'HUM':200}

