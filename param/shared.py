import os

# Noise Toolkit shared configuration parameters.

"""
  how file naming is done
  PQLX if file name contains time, it will be in HH24:MM:SS format
  WINDOWS if file name contains time, it will be in HH24_MM_SS format
"""

# Possible x-axis types.
xType = ["period", "frequency"]

production_label = 'IRIS DMC'
ntk_doi = '10.17611/dp/ntk.3'
production_label_position = (0.01, - 0.07)

# Use 'WINDOWS' or 'PQLX' file naming convention?
namingConvention = 'PQLX'

# Directories.
ntkDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
dataDirectory = os.path.join(ntkDirectory, 'data')

# To disable looking for response files on local drives, set this parameter to None. Otherwise, 
# set it to the response directory path.
respDirectory = os.path.join(dataDirectory, 'resp')
workDir = os.path.join(ntkDirectory, 'scratch')
pdfDirectory = 'PDF'
psdDirectory = 'PSD'

# Polarization database directory where individual polarization files are stored
polarDbDirectory = 'polarDb'
psdDbDirectory = 'psdDb'
powerDirectory = 'POWER'
polarDirectory = 'POLAR'
imageDirectory = 'IMAGE'


# Fedcatalog request URL
fedcatalog_url = f'http://service.iris.edu/irisws/fedcatalog/1/query?'


# To avoid  making one single large request for data to a data center, it is better to make multiple requests.
# The parameter _chunck_length in the parameter file determines maximum length of request in seconds (chunk) that
# will be sent  to a data center. This number should be adjusted based on the
chunk_length = 6 * 3600
chunk_count = 10
