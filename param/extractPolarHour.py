import os
import common

#
# initialize a few parametrs
#
# PSD files are all HOURLY files with 50% overlap
#
VERBOSE          = 0         # thurn the verbose mode on or off
namingConvention = common.namingConvention
ntkDirectory     = common.ntkDirectory
dataDirectory    = common.dataDirectory
polarDirectory   = common.polarDirectory
polarDbDirectory = common.polarDbDirectory
separator        = '\t' # separator character used in output
variables        = ["powerUD","powerEW","powerNS","powerLambda","betaSquare","thetaH","thetaV","phiVH","phiHH"]
decimalPlaces    = {"powerUD":0, # number of decimal places in the output file
                    "powerEW":0,
                    "powerNS":0,
                    "powerLambda":0,
                    "betaSquare":1,
                    "thetaH":0,
                    "thetaV":0,
                    "phiVH":0,
                    "phiHH":0}
