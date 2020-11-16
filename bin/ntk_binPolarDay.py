#!/usr/bin/env python

import sys
import os
import glob
import numpy as np
import importlib
from obspy.core import UTCDateTime
from datetime import date, timedelta as td

# Import the Noise Toolkit libraries.
library_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
sys.path.append(library_path)

param_path = os.path.join(os.path.dirname(__file__), '..', 'param')
sys.path.append(param_path)

import msgLib as msg_lib
import fileLib as file_lib
import staLib as sta_lib
import utilsLib as utils_lib

"""  NAME:   ntk_binPolarDay.py - a Python 3 script to bin polarization parameters into daily files for a given channel 
                      tag and bounding parameters. The output is similar to those available from the former
                      IRIS PDF/PSD Bulk Data Delivery System.

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

     hourly polarization files

  HISTORY:
     2020-11-16 Manoch: V.2.0.0 Python 3, use of Fedcatalog and adoption of PEP 8 style guide.
     2020-09-25 Timothy C. Bartholomaus, University of Idaho: conversion to python 3
     2015-07-15 IRIS DMC Product Team (Manoch) R0.5.0: Beta release updates
     2013-06-03 IRIS DMC Product Team (Manoch): created """

version = 'V.2.0.0'
script = sys.argv[0]
script = os.path.basename(script)

# Initial mode settings.
timing = False
do_plot = False
verbose = False
mode_list = ['0', 'plot', 'time', 'verbose']
default_param_file = 'binPolarDay'
if os.path.isfile(os.path.join(param_path, f'{default_param_file}.py')):
    param = importlib.import_module(default_param_file)
else:
    code = msg_lib.error(f'could not load the default parameter file  [param/{default_param_file}.py]', 2)
    sys.exit(code)


def usage():
    """ Usage message.
    """
    print(f'\n\n{script} version {version}\n\n'
          f'A Python 3 script to bin polarization parameters into daily files for a given channel '
          f'tag and bounding parameters for each of the variables defined by the "variables" parameter '
          f'in the computePolarization parameter file (the parameter file for this script must point to this '
          f'"variables" parameter). The output of this script is similar to those available '
          f'from the former IRIS PDF/PSD Bulk Data Delivery System.'
          f'\n\nUsage:\n\t{script} display the usage message (this message)'
          f'\n\t  OR'
          f'\n\t{script} param=FileName net=network sta=station loc=location chandir=channel_directory'
          f' start=YYYY-MM-DDTHH:MM:SS end=YYYY-MM-DDTHH:MM:SS xtype=[period|frequency] verbose=[0|1]\n'
          f'\n\tto perform extraction where:'
          f'\n\t  param\t\t[default: {default_param_file}] the configuration file name '
          f'\n\t  net\t\t[required] network code'
          f'\n\t  sta\t\t[required] station code'
          f'\n\t  loc\t\t[required] location ID'
          f'\n\t  chandir\t[default: {param.chanDir}] is the channel directory under {param.polarDbDirectory} '
          f'where the polarization output files are stored.'
          f'\n\t  xtype\t\t[period or frequency, default: {param.xType[0]}] X-axis type (period or '
          f'frequency for outputs and plots)'
          f'\n\t  start\t\t[required] start date-time (UTC) for extraction '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  end\t\t[required] end date-time (UTC) for extraction '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  verbose\t[0 or 1, default: {param.verbose}] to run in verbose mode set to 1'
          f'\n\nOutput: '
          f'\n\tFull paths to the daily and hourly output data files are provided at the end of the run. '
          f'You may turn off hourly file output via the configuration file.'
          f'\n\n\tThe daily and hourly output file names have the following form respectively:'
          f'\n\t\tD???.bin and H???.bin (??? represents 3-digit day of the year)'
          f'\n\tfor example:'
          f'\n\t\tD227.bin and H227.bin'
          f'\n\nExamples:'
          f'\n\n\t-usage:'
          f'\n\tpython {script}'
          f'\n\n\t- assuming that you already have executed the following command "successfully" to generate '
          f'polarization files:'
          f'\n\tpython ntk_computePolarization.py net=NM sta=SLM loc=DASH '
          f'start=2009-01-01T01:00:00 end=2009-01-01T03:00:00 xtype=frequency verbose=0'
          f'\n\n\tyou can bin the polarization parameters into daily files: '
          f'\n\tpython {script} param={default_param_file} net=NM sta=SLM loc=DASH '
          f'start=2009-01-01T01:00:00 end=2009-01-01T03:00:00 xtype=frequency verbose=0'
          f'\n\n\n\n')

    
# See if user has provided the run arguments.
args = utils_lib.get_args(sys.argv, usage)

param_file = utils_lib.get_param(args, 'param', default_param_file, usage)

# Check and see if the param file exists.
if os.path.isfile(os.path.join(param_path, param_file + ".py")):
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'param'))
    param = importlib.import_module(param_file)
else:
    usage()
    msg_lib.error(f'bad parameter file name {param_file}', 2)
    sys.exit()

channel_directory = utils_lib.get_param(args, 'chandir', utils_lib.param(param, 'chanDir').chanDir, usage)

verbose = utils_lib.get_param(args, 'verbose', False, usage)
verbose = utils_lib.is_true(verbose)

delimiter = param.separator

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

"""polarization files are all HOURLY files with 50% overlap computed as part of the polarization product
  date parameter of the hourly PSDs to start, it starts at hour 00:00:00
   - HOURLY files YYYY-MM-DD"""
variables = param.variables
data_directory = param.dataDirectory
column_tag = param.variables

# We always want to start from the beginning of the day, so we discard user hours, if any
start_date_time = utils_lib.get_param(args, 'start', None, usage)
try:
    start_datetime, start_year, start_month, start_day, start_doy = utils_lib.time_info(start_date_time)
except Exception as ex:
    usage()
    code = msg_lib.error(f'Invalid start ({start_date_time})\n{ex}', 2)
    sys.exit(code)

# We always want to start from the beginning of the day, so we discard user hours, if any.
end_date_time = utils_lib.get_param(args, 'end', None, usage)

# end_date_time is included.
try:
    end_datetime, end_year, end_month, end_day, end_doy = utils_lib.time_info(end_date_time)
except Exception as ex:
    usage()
    code = msg_lib.error(f'Invalid end ({end_date_time})\n{ex}', 2)
    sys.exit(code)

duration = end_datetime - start_datetime

end_date = date(int(end_year), int(end_month), int(end_day))
start_date = date(int(start_year), int(start_month), int(start_day))
delta = end_date - start_date
data_day_list = list()

for i in range(delta.days + 1):
    this_day = start_date + td(days=i)
    data_day_list.append(this_day.strftime("%Y/%j"))

if duration <= 0 or len(data_day_list) <= 0:
    usage()
    code = msg_lib.error(f'bad start/end times [{start_date_time}, {end_date_time}]', 2)
    sys.exit(code)

xtype = utils_lib.get_param(args, 'xtype', 'frequency', usage)  # what the x-axis should represent

"""Find the polarization files and start reading.
  build the file tag for the polarization files to read, example:
      NM.SLM.--.BHZ_BHE_BHN_2009-09-01T08:00:00.035645_3600_frequency.txt"""
polar_db_dir_tag, polar_db_file_tag = file_lib.get_dir(param.dataDirectory, param.polarDbDirectory,
                                                      network, station, location, channel_directory)

msg_lib.info(f'Polar DIR TAG: {polar_db_dir_tag}')
if verbose:
    msg_lib.info(f'Polar FILE TAG: {polar_db_file_tag}')

# Loop through the windows
bin_list = dict()
for n in range(len(data_day_list)):
    msg_lib.info(f'day {data_day_list[n]}')
    day_file = list()
    hour_file = list()
    for column in range(len(column_tag)):
        hour_file.append(list())
        day_file.append(dict())

    thisFile = os.path.join(polar_db_dir_tag, data_day_list[n], f'{polar_db_file_tag}*{xtype}.txt')
    if verbose:
        msg_lib.info(f'Looking into: {thisFile}')
    this_file_list = sorted(glob.glob(thisFile))

    if len(this_file_list) <= 0:
        msg_lib.warning('Main', 'No files found!')
        if verbose:
            msg_lib.info(f'skip')
        continue
    elif len(this_file_list) > 1:
        if verbose:
            msg_lib.info(f'{len(this_file_list)} files  found!')

    # Found the file, open and read it.
    for this_polar_file in this_file_list:
        if verbose:
            msg_lib.info(f'Polarization FILE: "{this_polar_file}')

        this_file_time_label = file_lib.get_file_times(param.namingConvention, channel_directory, this_polar_file)[0]

        file_time = UTCDateTime(this_file_time_label)
        this_year = file_time.strftime("%Y")
        this_hour = file_time.strftime("%H:%M")
        this_doy = file_time.strftime("%j")
        if start_datetime <= file_time < end_datetime:
            try:
                with open(this_polar_file) as file:
                    if verbose:
                        msg_lib.info(f'Working on {this_polar_file}')

                    # Skip the header lines.
                    for i in (1, 2):
                        next(file)

                    # Go through individual periods/frequencies.
                    for line in file:
                        # For each row, split column values.
                        line = line.strip()
                        values = line.split()
                        X = values[0]
                        # Go through each data column.
                        for column_index, column in enumerate(variables):
                            # Find the bin for this value and save it in the Hourly file.
                            bin_start, bin_end, bin_width = param.bins[column]
                            bin_list[column] = list()
                            binCount = int((float(bin_end) - float(bin_start)) / float(bin_width)) + 1

                            # Set the bin values.
                            for i in range(binCount + 1):
                                bin_list[column].append(float(bin_start) + float(i) * float(bin_width))

                            # Get the value for this column and bin it. The first column is T or F, so +1.
                            if values[column_index + 1] == 'nan':
                                continue
                            V = float(values[column_index + 1])
                            this_freq, this_bin = np.histogram(V, bins=bin_list[column])
                            # Is the value within the range?
                            if bin_start <= V <= bin_end:
                                if len(np.nonzero(this_freq)[0]) <= 0:
                                    continue
                                nonzero_element = np.nonzero(this_freq)[0][0]
                                this_line = f'{this_hour}{delimiter}{X}{delimiter}{this_bin[nonzero_element]}'
                                hour_file[column_index].append(this_line)
                            key = f'{X}'
                            if key in day_file[column_index]:
                                day_file[column_index][key] += this_freq
                            else:
                                day_file[column_index][key] = this_freq

                file.close()
                if verbose:
                    msg_lib.info(f'done reading the file ')
            except Exception as ex:
                naming_convention = param.namingConvention
                code = msg_lib.error(f'failed to open {this_polar_file}\nis the "namingConvention" of in the param file'
                                     f'{naming_convention} set correctly?\n{ex}', 3)
                sys.exit(code)

    # Open the output file and go through each data column.
    for column in range(len(column_tag)):
        msg_lib.info(f'variable: {column_tag[column]}')
        pdf_dir_tag, pdf_file_tag = file_lib.get_dir(param.dataDirectory, param.pdfDirectory, network,
                                                     station, location,
                                                     channel_directory)
        utils_lib.mkdir(pdf_dir_tag)
        this_path = os.path.join(pdf_dir_tag, f'Y{this_year}')
        utils_lib.mkdir(this_path)
        this_path = os.path.join(this_path, column_tag[column])
        utils_lib.mkdir(this_path)
        output_file = os.path.join(this_path, f'D{this_doy}.bin')
        msg_lib.info(f'DAILY OUTPUT FILE: {output_file}')
        with open(output_file, 'w') as output_file:
            for key in sorted(day_file[column]):
                if verbose:
                    msg_lib.info(f'KEY: {key}')
                for ii in range(len(day_file[column][key])):
                    output_file.write(f'{key}{delimiter}{bin_list[column_tag[column]][ii]}{delimiter}'
                                      f'{day_file[column][key][ii]}\n')
        output_file.close()

        if param.pdfHourlySave > 0:
            this_path = os.path.join(this_path, param.pdfHourlyDirectory)
            utils_lib.mkdir(this_path)
            output_file = os.path.join(this_path, f'H{this_doy}.bin')
            msg_lib.info(f'Hourly output file: {output_file}')
            with open(output_file, 'w') as output_file:
                for i in range(len(hour_file[column])):
                    output_file.write(f'{hour_file[column][i]}\n')
            output_file.close()
        else:
            msg_lib.info(f'hourly Polar save option turned off')
