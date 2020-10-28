import os
#
# Noise Toolit common configuration parameters
#

#
# how file naming is done
# PQLX if file name contains time, it will be in HH24:MM:SS format
# WINDOWS if file name contains time, it will be in HH24_MM_SS format
#
namingConvention = "PQLX" # use 'WINDOWS' or 'PQLX'

#
# Directories
#
ntkDirectory   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dataDirectory  = os.path.join(ntkDirectory,"data")
workDir        = os.path.join(ntkDirectory,"scratch")
pdfDirectory   = "PDF"
psdDirectory   = "PSD"
psdDbDirectory = "psdDb"
powerDirectory = "POWER"
imageDirectory = "IMAGE"

