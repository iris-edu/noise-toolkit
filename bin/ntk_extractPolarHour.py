#!/usr/bin/env python

import sys
import os
import glob
import importlib
from obspy.core import UTCDateTime
from datetime import date, timedelta as td

# Import the Noise Toolkit libraries.
library_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
sys.path.append(library_path)

param_path = os.path.join(os.path.dirname(__file__), '..', 'param')
sys.path.append(param_path)

import shared as shared

import msgLib as msg_lib
import fileLib as file_lib
import staLib as sta_lib
import utilsLib as utils_lib

"""  NAME:   ntk_ExtractPolarHour.py - is a Python a Python 3 script to extract hourly polarization values for 
          each of the variables defined by the "variables" parameter in the computePolarization parameter file 
          (the parameter file for this script must point to this variables in the "computePolarization" parameter 
          file (see  the "extractPolarHour" for an example). '

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
     2015-09-15 V.0.5.0: Beta release
     2013-06-07 IRIS DMC Product Team (MB): created """

version = 'V.2.0.0'
script = sys.argv[0]
script = os.path.basename(script)

# Initial mode settings.
timing = False
do_plot = False
verbose = False
mode_list = ['0', 'plot', 'time', 'verbose']
default_param_file = 'extractPolarHour'
if os.path.isfile(os.path.join(param_path, f'{default_param_file}.py')):
    param = importlib.import_module(default_param_file)
else:
    code = msg_lib.error(f'could not load the default parameter file  [param/{default_param_file}.py]', 2)
    sys.exit(code)


def usage():
    """ Usage message.
    """
    print(f'\n\n{script} version {version}\n\n'
          f'A Python 3 script to extract hourly polarization values for each of the variables '
          f'defined by the "variables" parameter in the computePolarization parameter file (the parameter file for '
          f'this script must point to this variables in the "computePolarization" parameter file.'
          f'\n\nUsage:\n\t{script} to display the usage message (this message)'
          f'\n\t  OR'
          f'\n\t{script} param=FileName net=network sta=station loc=location chandir=channel_directory'
          f' start=YYYY-MM-DDTHH:MM:SS end=YYYY-MM-DDTHH:MM:SS xtype=[period|frequency] verbose=[0|1]\n'
          f'\n\tto perform extraction where:'
          f'\n\t  param\t\t[default: {default_param_file}] the configuration file name '
          f'\n\t  net\t\t[required] network code'
          f'\n\t  sta\t\t[required] station code'
          f'\n\t  loc\t\t[required] location ID'
          f'\n\t  chandir\t[default: {param.chanDir}] is the channel directory under {param.polarDbDirectory} '
          f'where the polarization output files are stored'
          f'\n\t  xtype\t\t[period or frequency, default: {param.xType[0]}] X-axis type (period or '
          f'frequency for outputs and plots)'
          f'\n\t  start\t\t[required] start date-time (UTC) for extraction '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  end\t\t[required] end date-time (UTC) for extraction '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  verbose\t[0 or 1, default: {param.verbose}] to run in verbose mode set to 1'
          f'\n\nOutput: '
          f'\n\n\tData file names are provided at the end of the run.'
          f'\n\n\tThe output file columns are:'
          f'\n\t\tdate hour x-value parameter value separated by the "separator" '
          f'character defined in the parameter file.'
          f'\n\nExamples:'
          f'\n\n\t- usage:'
          f'\n\tpython {script}'
          f'\n\n\t- assuming that you already have executed the following command "successfully" to generate '
          f'polarization files:'
          f'\n\tpython ntk_computePolarization.py net=NM sta=SLM loc=DASH '
          f'start=2009-01-01T01:00:00 end=2009-01-01T03:00:00 xtype=frequency verbose=0'
          f'\n\n\tyou can perform extraction via:'
          f'\n\tpython {script} param=extractPolarHour net=NM sta=SLM loc=DASH chandir=BHZ_BHE_BHN '
          f'start=2009-01-01T01:00:00 end=2009-01-02T0:00:00 xtype=frequency verbose=0'
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
    code = msg_lib.error(f'{script}, parameter file is required', 2)
    sys.exit(code)

# Import the parameter file if it exists.
if os.path.isfile(os.path.join(param_path, f'{param_file}.py')):
    param = importlib.import_module(param_file)
else:
    usage()
    code = msg_lib.error(f'{script}, bad parameter file name [{param_file}]', 2)
    sys.exit(code)

# Polarization files are all HOURLY files with 50% overlap computed as part of the polarization product
# date parameter of the hourly Polarizations to start, it starts at hour 00:00:00
#  - HOURLY files YYYY-MM-DD
variable_list = param.variables
data_directory = param.dataDirectory
channel_directory = utils_lib.get_param(args, 'chandir', utils_lib.param(param, 'chanDir').chanDir, usage)

if channel_directory is None:
    code = msg_lib.error(f'{script}, could not find the "chanDir"  parameter in the parameter file', 2)
    sys.exit(code)

# Run parameters.
xtype = utils_lib.get_param(args, 'xtype', utils_lib.param(param, 'xType').xType[0], usage)
if xtype not in param.xType:
    usage()
    code = msg_lib.error(f'{script}, Invalid xtype  [{xtype}]', 2)
    sys.exit(code)

# Set the run mode.
verbose = utils_lib.get_param(args, 'verbose', utils_lib.param(param, 'verbose').verbose, usage)
verbose = utils_lib.is_true(verbose)

if verbose:
    msg_lib.info(f'{script}, script: {script} {len(sys.argv) - 1} args: {sys.argv}')

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

xType = utils_lib.get_param(args, 'type', 'frequency', usage)  # what the x-axis should represent

# The run arguments.
network = utils_lib.get_param(args, 'net', None, usage)
station = utils_lib.get_param(args, 'sta', None, usage)
location = sta_lib.get_location(utils_lib.get_param(args, 'loc', None, usage))

xtype = utils_lib.get_param(args, 'xtype', utils_lib.param(param, 'xType').xType[0], usage)
if xtype not in param.xType:
    usage()
    code = msg_lib.error(f'{script}, Invalid xtype  [{xtype}]', 2)
    sys.exit(code)

# Find and start reading the polarization files.
# Build the file tag for the polarization files to read, example:
#     NM_SLM_--_BH_2009-01-06
polarDbDirTag, polarization_db_file_tag = file_lib.get_dir(data_directory, param.polarDbDirectory,
                                                          network, station, location, channel_directory)

msg_lib.info(f'polarization DIR TAG: {polarDbDirTag}')
if verbose:
    msg_lib.info(f'polarization FILE TAG: {polarization_db_file_tag}')

# Open the output file for each parameter.
thisPolarDirTag, polarFileTag = file_lib.get_dir(data_directory, param.polarDirectory, network, station, location,
                                                channel_directory)
for pn, variable in enumerate(variable_list):
    msg_lib.info(f'variable: {variable}')
    polarDirTag = os.path.join(thisPolarDirTag, variable)
    utils_lib.mkdir(polarDirTag)
    tag_list = [polarFileTag, start_date_time.split('.')[0], end_date_time.split('.')[0], xtype]
    output_file_name = file_lib.get_file_name(param.namingConvention, polarDirTag, tag_list)
    try:
        with open(output_file_name, 'w') as output_file:
            # Loop through the windows.
            for n in range(len(data_day_list)):

                thisFile = os.path.join(polarDbDirTag, data_day_list[n],
                                        polarization_db_file_tag + f'*{xtype}.txt')
                msg_lib.info(f'Day: {data_day_list[n]}, {thisFile}')
                this_file_list = sorted(glob.glob(thisFile))

                if len(this_file_list) <= 0:
                    msg_lib.warning('Main', 'No files found!')
                    if verbose:
                        msg_lib.info('skip')
                    continue
                elif len(this_file_list) > 1:
                    if verbose:
                        msg_lib.info(f'{len(this_file_list)} files  found!')
                # Found the file, open it and read it.
                for this_polarization_file in this_file_list:
                    if verbose > 0:
                        msg_lib.info(f'polarization FILE: {this_polarization_file}')
                    this_file_time_label = this_polarization_file.split(polarization_db_file_tag + '.')[1].split('.')[0]
                    this_file_time = UTCDateTime(this_file_time_label)

                    if start_datetime <= this_file_time < end_datetime:
                        with open(this_polarization_file) as file:
                            if verbose > 0:
                                msg_lib.info(f'OK, working on ...{this_polarization_file}')

                            header = list()
                            # Go through individual periods/frequencies.
                            line_count = 0
                            for line in file:
                                line = line.strip()
                                line_count += 1
                                if line_count > 2:
                                    # Each row, split column values.
                                    values = line.split()
                                    X = values[0]
                                    V = str(round(float(values[pn + 1]), param.decimalPlaces[variable]))

                                    # Save the period/frequency and the value of interest.
                                    this_out_date, this_out_time = this_file_time_label.split('T')
                                    output_file.write(f'{this_out_date}{param.separator}{this_out_time.split(".")[0]}'
                                                      f'{param.separator}{X}{param.separator}{V}\n')
                                else:
                                    continue
                        file.close()
    except Exception as ex:
        code = msg_lib.error(f'failed to write {output_file_name}. Is the "namingConvention" parameter '
                             f'{shared.namingConvention} set correctly? \n{ex}', 3)
        sys.exit()
    msg_lib.info(f'OUTPUT FILE: {output_file_name}')
    output_file.close()
