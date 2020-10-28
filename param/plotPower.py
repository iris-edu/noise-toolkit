import os
import common
import computePower as power

#
# how file naming is donet
#
namingConvention = common.namingConvention

#
# directories
#
ntkDirectory   = common.ntkDirectory
dataDirectory  = common.dataDirectory
psdDirectory   = common.psdDirectory
powerDirectory = common.powerDirectory
imageDirectory =  common.imageDirectory

#
#  the following bins will be used to group powers within a period band
#
bins     = power.bins
binStart = power.binStart
binEnd   = power.binEnd
binIndex = power.binIndex

#
# plot parameter
#
plotSize          = (10,6)
columnTag     = ['Period',  'Power']
columnLabel   = ['Period',  'dB']
dotColor      = ['blue','green','red','cyan','magenta','yellow']
dotSize       = [0.3,0.3,0.3,0.3,0.3,0.3]

#
# column 0, blank column just to keep stuff in order
#
rangeLabel  = []
factor      = []
factorLabel = []
ymin        = []
ymax        = []
yticks      = []
ytickLabels = []
imageTag    = []

rangeLabel.append("")
factor.append(0)
factorLabel.append("")
ymin.append(0)
ymax.append(0)
yticks.append([0,0])
ytickLabels.append(['0','0'])
imageTag.append("")

#
# Local Microseism Power
#
rangeIndex = 1
rangeLabel.append("Local Microseism Acceleration Power (m^2/s^4")
factor.append(100000000000)
factorLabel.append(" x10^-"+str(str(factor[rangeIndex]).count('0'))+")") # blanks at the end for proper spacing
ymin.append(0)
ymax.append(0.5)
yticks.append([0.2,0.4])
ytickLabels.append(['0.2','0.4'])
imageTag.append("LM")

#
# rangeIndex 2, Secondary Microseism Power
#
rangeIndex = 2
rangeLabel.append("Secondary Microseism Acceleration Power (m^2/s^4")
factor.append(1000000000000)
factorLabel.append(" x10^-"+str(str(factor[rangeIndex]).count('0'))+")") # blanks at the end for proper spacing
ymin.append(0)
ymax.append(9.0)
yticks.append(['0.4','0.8','1.2'])
ytickLabels.append(['0.4','0.8','1.2'])
imageTag.append("SM")

#
# rangeIndex 3, Primary Microseism Power
#
rangeIndex = 3
rangeLabel.append("Primary Microseism Acceleration Power (m^2/s^4")
factor.append(1000000000000000)
factorLabel.append(" x10^-"+str(str(factor[rangeIndex]).count('0'))+")") # blanks at the end for proper spacing
ymin.append(0)
ymax.append(2)
yticks.append(['0.5','1.0','1.5'])
ytickLabels.append(['0.5','1.0','1.5'])
imageTag.append("PM")

#
# rangeIndex 4, Earth Hum
#
rangeIndex = 4
rangeLabel.append("Earth Hum Acceleration Power (m^2/s^4") # blanks at the end for proper spacing
factor.append(10000000000000000)
factorLabel.append(" x10^-"+str(str(factor[rangeIndex]).count('0'))+")")
ymin.append(0)
ymax.append(1)
yticks.append([0.2,0.4,0.6,0.8])
ytickLabels.append(['0.2','0.4','0.6','0.8'])
yLabel = rangeLabel + factorLabel										        
imageTag.append("EH")
