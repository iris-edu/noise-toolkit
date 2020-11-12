import shared
import computePolarization

# Turn the verbose mode on or off (1/0).
verbose = 0

# Use 'WINDOWS' or 'PQLX' file naming convention?
namingConvention = shared.namingConvention

# Directories.
ntkDirectory = shared.ntkDirectory
dataDirectory = shared.dataDirectory
polarDirectory = shared.polarDirectory
polarDbDirectory = shared.polarDbDirectory
chanDir = 'BHZ_BHE_BHN'

# Possible x-axis types.
xType = computePolarization.xType

# Delimiter character used for output.
separator = '\t'

# Variables to extract.
variables = computePolarization.variables

# Number of decimal places in the output file.
decimalPlaces = {'powerUD': 0,
                 'powerEW': 0,
                 'powerNS': 0,
                 'powerLambda': 0,
                 'betaSquare': 1,
                 'thetaH': 0,
                 'thetaV': 0,
                 'phiVH': 0,
                 'phiHH': 0}
