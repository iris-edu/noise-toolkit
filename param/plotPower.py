import os
import shared
import computePower as power

# How file naming is done?
namingConvention = shared.namingConvention

# Verbose mode on/off (1/0)
verbose = 0

# Directories
ntkDirectory = shared.ntkDirectory
dataDirectory = shared.dataDirectory
psdDirectory = shared.psdDirectory
powerDirectory = shared.powerDirectory
imageDirectory = shared.imageDirectory

#  The following bins will be used to group powers within a period band.
bins = power.bins
binStart = power.binStart
binEnd = power.binEnd
binIndex = power.binIndex

# Plot parameters.
plotSize = (10, 6)
columnTag = ['Period',  'Power']
columnLabel = ['Period',  'dB']
# dotColor = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow']
dotColor = ['C0', 'C1', 'C3', 'C2', 'C4', 'C5', 'C6', 'C7']
dotSize = [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]

# Column 0, blank column just to keep stuff in order
rangeLabel = list()
factor = list()
factorLabel = list()
ymin = list()
ymax = list()
yticks = list()
ytickLabels = list()
imageTag = list()

rangeLabel.append('')
factor.append(0)
factorLabel.append('')
ymin.append(0)
ymax.append(0)
yticks.append([0, 0])
ytickLabels.append(['0', '0'])
imageTag.append('')

# Local Microseism Power.
rangeIndex = 1
rangeLabel.append("Local Microseism Acceleration Power (m^2/s^4")
factor.append(100000000000)
# Blanks at the end for proper spacing.
factorLabel.append(" x10^-"+str(str(factor[rangeIndex]).count('0'))+")")
ymin.append(0)
ymax.append(0.5)
yticks.append([0.2, 0.4])
ytickLabels.append(['0.2', '0.4'])
imageTag.append("LM")

# rangeIndex 2, Secondary Microseism Power.
rangeIndex = 2
rangeLabel.append("Secondary Microseism Acceleration Power (m^2/s^4")
factor.append(1000000000000)
# Blanks at the end for proper spacing.
factorLabel.append(" x10^-"+str(str(factor[rangeIndex]).count('0'))+")")
ymin.append(0)
ymax.append(9.0)
yticks.append(['0.4', '0.8', '1.2'])
ytickLabels.append(['0.4', '0.8', '1.2'])
imageTag.append("SM")

# rangeIndex 3, Primary Microseism Power.
rangeIndex = 3
rangeLabel.append("Primary Microseism Acceleration Power (m^2/s^4")
factor.append(1000000000000000)
# Blanks at the end for proper spacing.
factorLabel.append(" x10^-"+str(str(factor[rangeIndex]).count('0'))+")")
ymin.append(0)
ymax.append(2)
yticks.append(['0.5', '1.0', '1.5'])
ytickLabels.append(['0.5', '1.0', '1.5'])
imageTag.append("PM")

# rangeIndex 4, Earth Hum
rangeIndex = 4
# Blanks at the end for proper spacing.
rangeLabel.append("Earth Hum Acceleration Power (m^2/s^4")
factor.append(10000000000000000)
factorLabel.append(" x10^-"+str(str(factor[rangeIndex]).count('0'))+")")
ymin.append(0)
ymax.append(1)
yticks.append([0.2, 0.4, 0.6, 0.8])
ytickLabels.append(['0.2', '0.4', '0.6', '0.8'])
yLabel = rangeLabel + factorLabel										        
imageTag.append("EH")
