import computePolarization
import shared

# Turn the verbose mode on or off (1/0).
verbose = 0

# Use 'WINDOWS' or 'PQLX' file naming convention?
namingConvention = shared.namingConvention

# Directories.
ntkDirectory = shared.ntkDirectory
dataDirectory = shared.dataDirectory
polarDirectory = shared.polarDirectory
polarDbDirectory = shared.polarDbDirectory
pdfDirectory = 'PDF'

# Channels directory label.
chanDir = 'BHZ_BHE_BHN'

# Possible x-axis types.
xType = shared.xType

# Save hourly files?
pdfHourlySave = 1
pdfHourlyDirectory = 'HOUR'

# Delimiter character used in the output.
separator = '\t'

# Create bins for each of the columns
variables = computePolarization.variables

# Bin limits [range start, range end, width of each bin] for each variable
bins = {'powerUD': [-200, -70, 1],
        'powerEW': [-200, -70, 1],
        'powerNS': [-200, -70, 1],
        'powerLambda': [-200, -70, 1],
        'betaSquare': [0.0, 1.0, 0.05],
        'thetaH': [0.0, 360.0, 1.0],
        'thetaV': [0.0, 90.0, 1.0],
        'phiVH': [-90.0, 90.0, 1.0],
        'phiHH': [-180.0, 180.0, 1.0]
        }
