import os
import numpy as np
import common

#
# initialize a few parametrs
#
# PSD files are all HOURLY files with 50% overlap
#
VERBOSE              = 0         # thurn the verbose mode on or off
namingConvention     = common.namingConvention
ntkDirectory         = common.ntkDirectory
dataDirectory        = common.dataDirectory
polarDirectory       = common.polarDirectory
polarDbDirectory     = common.polarDbDirectory
pdfDirectory         = "PDF"
pdfHourlySave        = 1
pdfHourlyDirectory   = "HOUR"
separator            = '\t' # separator character used in output
#
# create bins for each of the columns
#
variables        = ["powerUD","powerEW","powerNS","powerLambda","betaSquare","thetaH","thetaV","phiVH","phiHH"]
bins             = {"powerUD":[-200,-70,1], # bin limits [range start, range end, width of each bin] for each variable
                    "powerEW":[-200,-70,1],
                    "powerNS":[-200,-70,1],
                    "powerLambda":[-200,-70,1],
                    "betaSquare":[0.0,1.0,0.05],
                    "thetaH":[0.0,360.0,1.0],
                    "thetaV":[0.0,90.0,1.0],
                    "phiVH":[-90.0,90.0,1.0],
                    "phiHH":[-180.0,180.0,1.0]}
