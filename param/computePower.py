import os
import shared

# How file naming is done
namingConvention = shared.namingConvention

# PSD files are all HOURLY files with 50% overlap
#
ntkDirectory = shared.ntkDirectory
dataDirectory = shared.dataDirectory
psdDirectory = shared.psdDirectory
powerDirectory = shared.powerDirectory

verbose = 0

xType = ['period', 'frequency']
"""
   The following bins will be used to group powers within a period band
 
        local noise for stations near shore
         |
         |   secondary microseisms
         |       |
         |       |   primary microseisms
         |       |    |
         |       |    |    Earth hum
         |       |    |     |
"""
bins = ['LM', 'SM', 'PM', 'HUM'] 
binIndex = {'LM': 1, 'SM': 2, 'PM': 3, 'HUM': 4}

"""
  period bands in second for bins of Interest:
        local noise for stations near shore
            |
            |   secondary microseism
            |           |
            |           |   primary microseis
            |           |       |
            |           |       |    Earth hum
            |           |       |        |
"""
binStart = {'LM': 1, 'SM': 5, 'PM': 11, 'HUM': 50}
binEnd = {'LM': 5, 'SM': 10, 'PM': 30, 'HUM': 200}

