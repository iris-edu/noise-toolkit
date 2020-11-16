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
import utilsLib  as utils_lib

"""
 Name: ntk_bin_PsdDay.py - a Python 3 script to bin PSD's to daily files for a given channel and bounding parameter.

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
    2014-10-22 Manoch: added support for Windows installation
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
default_param_file = 'binPsdDay'
if os.path.isfile(os.path.join(param_path, f'{default_param_file}.py')):
    param = importlib.import_module(default_param_file)
else:
    code = msg_lib.error(f'could not load the default parameter file  [param/{default_param_file}.py]', 2)
    sys.exit(code)


def usage():
    """ Usage message.
   """
    print(f'\n\n{script} version {version}\n\n'
          f'A Python 3 script to bin PSDs to daily files for a given channel and bounding parameters. '
          f'\n\nUsage:\n\t{script} to display the usage message (this message)'
          f'\n\t  OR'
          f'\n\t{script} param=FileName net=network sta=station loc=location chan=channel(s)'
          f' start=YYYY-MM-DDTHH:MM:SS end=YYYY-MM-DDTHH:MM:SS xtype=[period|frequency] verbose=[0|1]\n'
          f'\n\twhere:'
          f'\n\t  param\t\t[default: {default_param_file}] the configuration file name '
          f'\n\t  net\t\t[required] network code'
          f'\n\t  sta\t\t[required] station code'
          f'\n\t  loc\t\t[required] location ID'
          f'\n\t  chan\t\t[required] channel ID '
          f'\n\t  xtype\t\t[required] X-axis type for output (period or '
          f'frequency)'
          f'\n\t  start\t\t[required] start date-time (UTC) of the binning interval '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  end\t\t[required] end date-time (UTC) of the binning interval '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  verbose\t[0 or 1, default: {param.verbose}] to run in verbose mode set to 1'
          f'\n\nOutput format for the daily files: '
          f'\n\n\tX-value (period/frequency) Power number of hits with values separated using the "separator" character '
          f'specified in the parameter file.'
          f'\n\nOutput format for the hourly files: '
          f'\n\n\thour X-value (period/frequency) Power with values separated using the "separator" character '
          f'specified in the parameter file.'
          f'\n\nOutput: '
          f'\n\tFull paths to the daily and hourly output data files are provided at the end of the run. '
          f'You may turn off hourly file output via the configuration file.'
          f'\n\n\tThe daily and hourly output file names have the following form respectively:'
          f'\n\t\tD???.bin and H???.bin (??? represents 3-digit day of the year)'
          f'\n\tfor example:'
          f'\n\t\tD227.bin and H227.bin'
          f'\n\nExamples:'
          f'\n\n\t- usage:'
          f'\n\tpython {script}'
          f'\n\n\t- Assuming that you already have tried the following ntk_compute_PSD.py example "successfully":'
          f'\n\tpython ntk_computePSD.py net=TA sta=O18A loc=DASH start=2008-08-14T12:00:00 end=2008-08-14T13:30:00'
          f'\n\n\tyou can perform binning via:'
          f'\n\tpython {script} net=TA sta=O18A loc=DASH chan=BHZ start=2008-08-14T12:00:00 end=2008-08-14T13:30:00 '
          f'xtype=period '
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

"""
 PSD files are all HOURLY files with 50% overlap computed as part of the polarization product
 date parameter of the hourly PSDs to start, it starts at hour 00:00:00
  - HOURLY files YYYY-MM-DD
"""

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

data_day_list = list()
for i in range(delta.days + 1):
    this_day = start_datetime + td(days=i)
    data_day_list.append(this_day.strftime("%Y/%j"))

if len(data_day_list) <= 0:
    usage()
    msg_lib.error(f'Bad start/end times [{start_date_time}, {end_date_time}]', 2)
    sys.exit()

# Find PSD files and start reading them.
# build the file tag for the PSD files to read, example:
#     NM_SLM_--_BH_2009-01-06
psd_db_dir_tag, psd_db_file_tag = file_lib.get_dir(param.dataDirectory, param.psdDbDirectory, network,
                                                   station, location, channel)

msg_lib.info(f'PSD DIR TAG: {psd_db_dir_tag}')

# Loop through the windows.
for n in range(len(data_day_list)):
    msg_lib.info(f'day {data_day_list[n]}')
    d_file = dict()
    h_file = list()
    this_file = os.path.join(psd_db_dir_tag, data_day_list[n], f'{psd_db_file_tag}*{xtype}.txt')
    if verbose:
        msg_lib.info(f'Looking into: {this_file}')
    this_file_list = sorted(glob.glob(this_file))

    if len(this_file_list) <= 0:
        msg_lib.warning('Main', 'No files found!')
        if verbose:
            msg_lib.warning('Main', 'skip')
        continue
    elif len(this_file_list) > 1:
        if verbose:
            msg_lib.info(f'{len(this_file_list)} files found!')

    # Found the file, open it and read it.
    for this_psd_file in this_file_list:
        if verbose > 0:
            msg_lib.info(f'PSD FILE: {this_psd_file}')

        this_file_time_label = file_lib.get_file_times(param.namingConvention, channel, this_psd_file)
        this_file_time = UTCDateTime(this_file_time_label[0])
        this_year = this_file_time.strftime("%Y")
        this_hour = this_file_time.strftime("%H:%M")
        this_doy = this_file_time.strftime("%j")
        if start_datetime <= this_file_time <= end_datetime:
            with open(this_psd_file) as file:
                if verbose > 0:
                    msg_lib.info(f'working on ...{this_psd_file}')

                # Skip the Header line.
                next(file)

                # Go through individual periods/frequencies.
                for line in file:
                    # Each row, split column values.
                    X, V = (line.strip()).split()

                    # Here we change the potential 'nan' values to user defined NAN.
                    if V.upper() == 'NAN':
                        this_line = f'{this_hour}{param.separator}{X}{param.separator}{param.intNan}'
                        key = f'{X}:{param.intNan}'
                    else:
                        this_line = f'{this_hour}{param.separator}{X}{param.separator}{int(round(float(V)))}'
                        key = f'{X}:{int(round(float(V)))}'
                    h_file.append(this_line)
                    if key in d_file.keys():
                        d_file[key] += 1
                    else:
                        d_file[key] = 1

            file.close()

    # Open the output file.
    pdf_dir_tag, pdf_file_tag = file_lib.get_dir(param.dataDirectory, param.pdfDirectory, network,
                                                 station, location, channel)
    file_lib.make_path(pdf_dir_tag)
    this_path = os.path.join(pdf_dir_tag, f'Y{this_year}')
    file_lib.make_path(this_path)
    output_file = os.path.join(this_path, f'D{this_doy}.bin')
    msg_lib.info(f'DAILY OUTPUT FILE: {output_file}')
    with open(output_file, 'w') as output_file:
        for key in sorted(d_file.keys()):
            day, db = key.split(':')
            output_file.write(f'{day}{param.separator}{db}{param.separator}{d_file[key]}\n')
    output_file.close()

    if param.pdfHourlySave > 0:
        this_path = os.path.join(this_path, param.pdfHourlyDirectory)
        file_lib.make_path(this_path)
        output_file = os.path.join(this_path, f'H{this_doy}.bin')
        msg_lib.info(f'HOURLY OUTPUT FILE: {output_file}')
        with open(output_file, 'w') as output_file:
            for i in range(len(h_file)):
                output_file.write(f'{h_file[i]}\n')
        output_file.close()
    else:
        output_file.write(f'Hourly PSD save option turned off')

