#!/usr/bin/env python

import sys
import os

import datetime

import numpy as np
import importlib
from obspy.core import UTCDateTime

# Import the Noise Toolkit libraries.
library_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
sys.path.append(library_path)

param_path = os.path.join(os.path.dirname(__file__), '..', 'param')
sys.path.append(param_path)

import msgLib as msg_lib
import fileLib as file_lib
import staLib as sta_lib
import utilsLib as utils_lib

"""
  NAME:

  ntk_medianPower.py - a Python 3 script to calculates median power for a given window length from
                       the computed PSD powers

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

  HISTORY:
     2020-11-16 Manoch: V.2.0.0 Python 3 and adoption of PEP 8 style guide.
     2015-02-20 Manoch: addressed the output file naming issue
     2014-11-24 Manoch: Beta (V.0.5) release
     2013-10-07 Manoch: revision for production test
     2013-03-14 Manoch: created partially
"""

version = 'V.2.0.0'
script = sys.argv[0]
script = os.path.basename(script)

# Initial mode settings.
timing = False
do_plot = False
verbose = False
mode_list = ['0', 'plot', 'time', 'verbose']
default_param_file = 'medianPower'
if os.path.isfile(os.path.join(param_path, f'{default_param_file}.py')):
    param = importlib.import_module(default_param_file)
else:
    code = msg_lib.error(f'could not load the default parameter file  [param/{default_param_file}.py]', 2)
    sys.exit(code)


def usage():
    """ Usage message.
    """
    print(f'\n\n{script} version {version}\n\n'
          f'A Python 3 script to calculate median power for a given window length '
          f'based on the computed PSD powers.'
          f'\n\nUsage:\n\t{script} to display the usage message (this message)'
          f'\n\n\t  OR'
          f'\n\n\t{script} param=FileName net=network sta=station loc=location chan=channel '
          f' start=YYYY-MM-DDTHH:MM:SS end=YYYY-MM-DDTHH:MM:SS win=hour verbose=[0|1] file=PSD_file_name'
          f'\n\tto compute median power where:'
          f'\n\t  param\t\t[default: {default_param_file}] the configuration file name '
          f'\n\t  net\t\t[required] network code'
          f'\n\t  sta\t\t[required] station code'
          f'\n\t  loc\t\t[required] location ID'
          f'\n\t  chan\t\t[required] channel ID'
          f'\n\t  win\t\t[required] smoothing window length in hours '
          f'\n\t  start\t\t[required] start date-time (UTC) for extraction '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  end\t\t[required] end date-time (UTC) for extraction '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t file\t\t[required] PSD file name'
          f'\n\t  verbose\t[0 or 1, default: {param.verbose}] to run in verbose mode set to 1'
          f'\n\nInput: '
          f'\n\tThe input PSD power file is expected to be under the "POWER" directory and should have the '
          f'same format as the output of ntk_computePower.py script. '
          f'\n\tThe "computePower" parameter file can be used as '
          f'the input parameter file for this script also.'
          f'\n\nOutput: '
          f'\n\tThe smooth PDFs are stored  under the corresponding "POWER"/window directory:'
          f'\n\tWin(h)     Dir\n\t   6    ->  6h\n\t  12    -> 12h\n\t  24    ->  1d\n\t  96    ->  4d\n\t'
          f' 384    -> 16d'
          f'\n\nExamples:'
          f'\n\n\t- usage:'
          f'\n\tpython {script}'
          f'\n\n\t- assuming that you have already "successfully" computed power via:'
          f'\n\tpython ntk_computePower.py param=computePower net=TA sta=O18A loc=DASH chan=BHZ xtype=period verbose=1  '
          f'file=TA.O18A.--.BHZ.2008-08-14.2008-08-14.period.txt'
          f'\n\n\tthen, compute median power "successfully" via:'
          f'\n\tpython {script} param={default_param_file} net=TA sta=O18A loc=DASH chan=BHZ xtype=period verbose=0 '
          f'win=12 start=2008-08-14T00:00:00 end=2008-08-14T23:00:00 '
          f'file=TA.O18A.--.BHZ.2008-08-14.2008-08-14.txt'
          f'\n\n\n\n')


# See if user has provided the run arguments.
args = utils_lib.get_args(sys.argv, usage)

param_file = utils_lib.get_param(args, 'param', default_param_file, usage)

# Check and see if the param file exists.
if os.path.isfile(os.path.join(param_path, param_file + ".py")):
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'param'))
    param = importlib.import_module(param_file)
else:
    msg_lib.error(f'bad parameter file name {param_file}', 2)
    usage()
    sys.exit()

verbose = utils_lib.get_param(args, 'verbose', False, usage)

if verbose:
    msg_lib.info(f'script: {script} {len(sys.argv) - 1} args: {sys.argv}')

if len(sys.argv) < 9:
    code = msg_lib.error('not enough argument(s)', 1)
    usage()
    sys.exit(code)

# The run arguments.
network = utils_lib.get_param(args, 'net', None, usage)
station = utils_lib.get_param(args, 'sta', None, usage)
location = sta_lib.get_location(utils_lib.get_param(args, 'loc', None, usage))

# Set the bin ranges.
bin_start = list()
bin_end = list()
bins = param.bins
for _bin in bins:
    try:
        bin_start.append(param.binStart[_bin])
        bin_end.append(param.binEnd[_bin])
    except Exception as ex:
        code = msg_lib.error(f'bad band [{_bin}] in param file', 2)
        sys.exit(2)

if verbose:
    msg_lib.info(f'PERIOD BIN START: {bin_start}, PERIOD BIN ENDis: {bin_end}')

network = utils_lib.get_param(args, 'net', None, usage)
station = utils_lib.get_param(args, 'sta', None, usage)
location = sta_lib.get_location(utils_lib.get_param(args, 'loc', None, usage))
channel = utils_lib.get_param(args, 'chan', None, usage)
start = utils_lib.get_param(args, 'start', None, usage)
end = utils_lib.get_param(args, 'end', None, usage)
window_width_hour = utils_lib.get_param(args, 'win', None, usage)

# NOTE: the input PSD file is assumed to have the same format as the output of the ntk_extractPsdHour.py script.
power_file = utils_lib.get_param(args, 'file', None, usage)
power_directory = os.path.join(param.dataDirectory, param.powerDirectory)
power_directory = os.path.join(power_directory, ".".join([network, station, location]), channel)
power_file_name = os.path.join(power_directory, power_file)

# Check to see if the power file exists, then read its content.
if not os.path.isfile(power_file_name):
    code = msg_lib.error(f'Could not find the POWER file [{power_file_name}]', 2)
    sys.exit(code)

with open(power_file_name) as input_file:
    # Read the entire power file
    lines = input_file.readlines()

    # Find the last non-blank line
    line_count = len(lines)
    for i in range(1, len(lines)):
        line = lines[-i].strip()
        if len(line) > 0:
            line_count = len(lines) - i + 1
            break
    if verbose:
        msg_lib.info(f'INPUT: {line_count} lines')

# Get the time of each line, skip headers.
power_time = list()
for i in range(2, line_count):
    line = lines[i].strip()
    values = line.split()
    power_time.append(UTCDateTime(values[0] + 'T' + values[1]))

# Window length in hours.
#
window_tag = file_lib.get_window_tag(window_width_hour)
msg_lib.info(f'smoothing window {window_width_hour} hours')

power_directory = os.path.join(power_directory, window_tag)
if not os.path.exists(power_directory):
    os.makedirs(power_directory)

# Window length in hours and second plus the half window length
# base on these calculate number of shifts that will be performed.
window_width_second = float(window_width_hour) * 3600.0
window_shift_second = param.windowShiftSecond
msg_lib.info(f'Wind length and shift in seconds {window_width_second}, {window_shift_second}')
start_time = UTCDateTime(start) - (window_width_second / 2.0)  # we want the first sample at start_time
end_time = UTCDateTime(end) + (window_width_second / 2.0)
duration = end_time - start_time  # seconds to process
n_shift = int(float(duration / window_shift_second))

# Place the median directory under the power directory.
if verbose:
    msg_lib.info(f'POWER PATH: {power_directory}')

if not file_lib.make_path(power_directory):
    code = msg_lib.error(f'Error, failed to access {power_directory}', 2)
    sys.exit(code)

# Out_power_file_name = file_lib.getFileName(param.namingConvention, power_directory,
out_power_file_name = file_lib.get_file_name(param.namingConvention, power_directory,
                                           [power_file.replace('.txt', ''), window_tag])

# Open the output file.
with open(os.path.join(power_directory, out_power_file_name), 'w') as output_file:
    # w\Write the output header.
    output_file.write(f'Period\n')
    output_file.write(f'{"Date-Time":20s}')
    for k in range(len(bin_start)):
        output_file.write(f"{f'{bins[k]} ({bin_start[k]}-{bin_end[k]})':20s}")
    output_file.write("\n")

    # Loop through the windows.
    for n in range(0, n_shift + 1):
        # Get start and end of the current window.
        this_window_start = start_time + float(n * window_shift_second)
        this_window_end = this_window_start + window_width_second
        center_time = this_window_start + (this_window_end - this_window_start) / 2.0
        if center_time < UTCDateTime(start) or center_time > UTCDateTime(end):
            continue

        if verbose:
            msg_lib.info(f'START: {this_window_start.strftime("%Y-%m-%dT%H:%M:%S.0")} '
                         f'END: {this_window_end.strftime("%Y-%m-%dT%H:%M:%S.0")}')
            msg_lib.info(f'POINT: {center_time.strftime("%Y-%m-%dT%H:%M:%S.0")}')

        # Initialize the list that will hold all the extracted hourly Power.
        all_power = list()
        for i in range(len(bins)):
            all_power.append(list())

        # Cycle through all the power lines for this window and extract the values that fall in this window.
        for p in range(2, line_count):
            if this_window_start <= power_time[p - 2] <= this_window_end:
                """ For each row, split column values
                    columns are:
                        Date      Time 
                        values[0] values[1]  values[2]  values[3] ...
                """
                line = lines[p]
                line = line.strip()
                values = line.split()

                # Save the the value of interest (start at column 2, 0=Date and 1=Time).
                for i in range(len(bins)):
                    all_power[i].append(float(values[2 + i]))

        # Done, write out the results.
        if len(all_power[0]) > 0:
            output_file.write(f'{center_time.strftime("%Y-%m-%dT%H:%M:%S.0"):20s}')
            for i in range(len(bins)):
                output_file.write(f'{np.median(all_power[i]):20.5e}')
            output_file.write("\n")

msg_lib.info(f'OUTPUT: {os.path.join(power_directory, out_power_file_name)}')
