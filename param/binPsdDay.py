import os
import common

#
# how file naming is done
#
namingConvention = common.namingConvention

#
# initialize a few parametrs
#
# PSD files are all HOURLY files with 50% overlap
#
VERBOSE              = 0         # thurn the verbose mode on or off
ntkDirectory         = common.ntkDirectory
dataDirectory        = common.dataDirectory
psdDbDirectory       = common.psdDbDirectory
pdfDirectory         = common.pdfDirectory
pdfHourlySave        = 1
pdfHourlyDirectory   = "HOUR"
intNan               = -999999
separator            = '\t' # separator character used in output

