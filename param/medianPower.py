import os
import shared

# How file naming is done?
namingConvention = shared.namingConvention

# Turn the verbose mode on or off (1/0).
verbose = 0       
ntkDirectory = shared.ntkDirectory
dataDirectory = shared.dataDirectory
psdDirectory = shared.psdDirectory
powerDirectory = shared.powerDirectory

windowShiftSecond = 600.0

"""
  periods in second for bins of Interest:
        local noise for stations near shore
             |
             |   secondary microseism
             |           |
             |           |   primary microseis
             |           |       |
             |           |       |    Earth hum
             |           |       |        |
"""
binStart = {'local': 1, 'SM': 5, 'PM': 11, 'HUM': 50}
binEnd = {'local': 5, 'SM': 10, 'PM': 30, 'HUM': 200}

# bins will be used to order the output.
bins = ['local', 'SM', 'PM', 'HUM']
