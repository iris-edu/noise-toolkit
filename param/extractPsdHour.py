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
psdDbDirectory = common.psdDbDirectory
separator      = '\t' # separator character used in output
intNan         = -999999

