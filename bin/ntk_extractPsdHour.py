#!/usr/bin/env python

import sys
import os
import importlib
import glob
from obspy.core import UTCDateTime
from datetime import date, timedelta as td

# Import the Noise Toolkit libraries.
ntk_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

param_path = os.path.join(ntk_directory, 'param')
lib_path = os.path.join(ntk_directory, 'lib')

sys.path.append(param_path)
sys.path.append(lib_path)

import msgLib as msg_lib
import fileLib as file_lib
import staLib  as sta_lib
import utilsLib as utils_lib

"""
  Name:   ntk_extractPsdHour.py - a Python 3 script to extract PSDs for a given channel and bounding
                      parameters. The output is similar to PQLX's exPSDhour script

  Copyright (C) 2020  Product Team, IRIS Data Management Center

     This is a free software; you can redistribute it and/or modify
     it under the terms of the GNU Lesser General Public License as
     published by the Free Software Foundation; either version 3 of the
     License, or (at your option) any later version.

     This script is distributed in the hope that it will be useful, but
     WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     Lesser General Public License (GNU-LGPL) for more details.  The
     GNU-LGPL and further information can be found here:
     http://www.gnu.org/

     You should have received a copy of the GNU Affero General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

  INPUT:

  hourly PSD files

  HISTORY:
     2020-11-16 Manoch: V.2.0.0 Python 3 and adoption of PEP 8 style guide.
     2015-04-02 Manoch: based on feedback from Robert Anthony, in addition to nan values other
                        non-numeric values may exist. The write that contains a flot() conversion
                        is placed in a try block so we can catch any non-numeric conversion issue
                        and report it as user-defined NAN
     2014-10-22 Manoch: added support for Windows installation
     2014-10-06 IRIS DMC Product Team (MB): Beta release: output file name now includes the x-axis type
     2013-05-19 IRIS DMC Product Team (MB): created 
"""
version = 'V.2.0.0'
script = sys.argv[0]
script = os.path.basename(script)

# Initial mode settings.
timing = False
do_plot = False
verbose = False
mode_list = ['0', 'plot', 'time', 'verbose']
default_param_file = 'extractPsdHour'
if os.path.isfile(os.path.join(param_path, f'{default_param_file}.py')):
    param = importlib.import_module(default_param_file)
else:
    code = msg_lib.error(f'could not load the default parameter file  [param/{default_param_file}.py]', 2)
    sys.exit(code)


def usage():
    """ Usage message.
  """
    print(f'\n\n{script} version {version}\n\n'
          f'A Python 3 script to extract PSDs for a given channel and bounding parameters. '
          f'The output is similar to the PQLX\'s exPSDhour script: '
          f'\n\thttps://pubs.usgs.gov/of/2010/1292/pdf/OF10-1292.pdf. '
          f'\n\nUsage:\n\t{script} to display the usage message (this message)'
          f'\n\t  OR'
          f'\n\t{script} param=FileName net=network sta=station loc=location chan=channel(s)'
          f' start=YYYY-MM-DDTHH:MM:SS end=YYYY-MM-DDTHH:MM:SS xtype=[period|frequency] verbose=[0|1]\n'
          f'\n\tto perform binning:'
          f'\n\t  param\t\t[default: {default_param_file}] the configuration file name '
          f'\n\t  net\t\t[required] network code'
          f'\n\t  sta\t\t[required] station code'
          f'\n\t  loc\t\t[required] location ID'
          f'\n\t  chan\t\t[required] channel ID '
          f'\n\t  xtype\t\t[required] X-axis type (period or '
          f'frequency for output)'
          f'\n\t  start\t\t[required] start date-time (UTC) of the interval for which PSDs to be computed '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  end\t\t[required] end date-time (UTC) of the interval for which PSDs to be computed '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  verbose\t[0 or 1, default: {param.verbose}] to run in verbose mode set to 1'
          f'\n\nOutput format: '
          f'\n\nDate Hour X-value (period/frequency) Power with values separated using the "separator" character '
          f'specified in the parameter file.'
          f'\n\nOutput file: '
          f'\n\tFull path to the  output data file is provided at the end of the run. '
          f'\n\n\tThe output file name has the form:'
          f'\n\t\tnet.sta.loc.chan.start.end.xtype.txt'
          f'\n\tfor example:'
          f'\n\t\tTA.O18A.--.BHZ.2008-08-14.2008-08-14.period.txt'
          f'\n\nExamples:'
          f'\n\n\t- usage:'
          f'\n\tpython {script}'
          f'\n\n\t- Assuming that you already have tried the following ntk_compute_PSD.py example "successfully":'
          f'\n\tpython ntk_computePSD.py net=TA sta=O18A loc=DASH start=2008-08-14T12:00:00 end=2008-08-14T13:30:00'
          f'\n\n\tyou can perform PSD extraction via:'
          f'\n\tpython {script} net=TA sta=O18A loc=DASH chan=BHZ start=2008-08-14T12:00:00 '
          f'end=2008-08-14T12:30:00 xtype=period'
          f'\n\n\n\n')


# Get the run arguments.
args = utils_lib.get_args(sys.argv, usage)
if not args:
    usage()
    sys.exit(0)

# Import the user-provided parameter file. The parameter file is under the param directory at the same level
# as the script directory.
param_file = utils_lib.get_param(args, 'param', default_param_file, usage)

if param_file is None:
    usage()
    code = msg_lib.error(f' parameter file is required', 2)
    sys.exit(code)

# Import the parameter file if it exists.
if os.path.isfile(os.path.join(param_path, f'{param_file}.py')):
    param = importlib.import_module(param_file)
else:
    usage()
    code = msg_lib.error(f'bad parameter file name [{param_file}]', 2)
    sys.exit(code)

network = utils_lib.get_param(args, 'net', None, usage)
station = utils_lib.get_param(args, 'sta', None, usage)
location = sta_lib.get_location(utils_lib.get_param(args, 'loc', None, usage))
channel = utils_lib.get_param(args, 'chan', None, usage)
xtype = utils_lib.get_param(args, 'xtype', None, usage)

# Specific start and end date and times from user.
# We always want to start from the beginning of the day, so we discard user hours, if any.
start_date_time = utils_lib.get_param(args, 'start', None, usage)
start_date_time = start_date_time.split('T')[0]
start_year, start_month, start_day = start_date_time.split('-')
try:
    start_datetime = UTCDateTime(start_date_time)
except Exception as ex:
    usage()
    code = msg_lib.error(f'Invalid start ({start_date_time})\n{ex}', 2)
    sys.exit(code)

end_date_time = utils_lib.get_param(args, 'end', None, usage)
end_date_time = end_date_time.split('T')[0]
end_year, end_month, end_day = end_date_time.split('-')
try:
    end_datetime = UTCDateTime(end_date_time) + 86400
except Exception as ex:
    usage()
    code = msg_lib.error(f'Invalid end ({end_date_time})\n{ex}', 2)
    sys.exit(code)

delta = date(int(end_year), int(end_month), int(end_day)) - \
        date(int(start_year), int(start_month), int(start_day))

data_days_list = list()
for i in range(delta.days + 1):
    this_day = start_datetime + td(days=i)
    data_days_list.append(this_day.strftime("%Y/%j"))

""" Find and start reading the PSD files.
    Build the file tag for the PSD files to read, example:
      NM_SLM_--_BH_2009-01-06
"""
psd_db_dir_tag, psd_db_file_tag = file_lib.get_dir(param.dataDirectory, param.psdDbDirectory, network,
                                                   station, location, channel)

msg_lib.info(f'PSD DIR TAG: {psd_db_dir_tag}')
if verbose > 0:
    msg_lib.info(f'PSD FILE TAG: {psd_db_file_tag}')

# Open the output file.
psd_dir_tag, psd_file_tag = file_lib.get_dir(param.dataDirectory, param.psdDirectory, network,
                                             station, location, channel)
file_lib.make_path(psd_dir_tag)
tag_list = [psd_file_tag, start_date_time.split('.')[0], end_date_time.split('.')[0], xtype]
output_file_name = file_lib.get_file_name(param.namingConvention, psd_dir_tag, tag_list)
with open(output_file_name, 'w') as output_file:
    # Loop through the windows.
    for n in range(len(data_days_list)):

        thisFile = os.path.join(psd_db_dir_tag, data_days_list[n], psd_db_file_tag + '*' + xtype + '.txt')
        msg_lib.info(f'Day: {data_days_list[n]}')
        this_file_list = sorted(glob.glob(thisFile))

        if len(this_file_list) <= 0:
            msg_lib.warning('Main', 'No files found!')
            if verbose:
                msg_lib.info(f'skip')
            continue
        elif len(this_file_list) > 1:
            if verbose:
                msg_lib.info(f'{len(this_file_list)} files  found!')

        # Found the file, open it and read it.
        for this_psd_file in this_file_list:
            if verbose > 0:
                msg_lib.info(f'PSD FILE: {this_psd_file}')
            this_file_time_label = file_lib.get_file_times(param.namingConvention, channel, this_psd_file)
            this_file_time = UTCDateTime(this_file_time_label[0])
            if start_datetime <= this_file_time <= end_datetime:
                with open(this_psd_file) as file:
                    if verbose > 0:
                        msg_lib.info(f'working on ... {this_psd_file}')

                    # Skip the header line.
                    next(file)

                    # Go through individual periods/frequencies.
                    for line in file:
                        # Each row, split column values.
                        X, V = (line.strip()).split()

                        # Save the period/frequency and the value of interest.
                        this_out_date, this_out_time = this_file_time_label[0].split('T')

                        # Here we convert potential 'nan' and 'inf' (non-numeric) values to user defined NAN.
                        try:
                            output_file.write(f'{this_out_date}{param.separator}{this_out_time.split(".")[0]}'
                                              f'{param.separator}{X}{param.separator}{round(float(V))}\n')
                        except Exception as ex:
                            output_file.write(f'{this_out_date}{param.separator}{this_out_time.split(".")[0]}'
                                              f'{param.separator}{X}{param.separator}{param.intNan}\n')

                file.close()
msg_lib.info(f'OUTPUT FILE: {output_file_name}')
output_file.close()
