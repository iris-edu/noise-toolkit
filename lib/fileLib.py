import os
import msgLib as msg_lib


def make_path(directory):
    """Checks a directory for existance and if it does not exist, create it.
    If needed, create all parent directories."""

    # The path must be an absolute path.
    if not os.path.isabs(directory):
        msg_lib.error(f'path must be an absolute path {directory}', 2)
        return None

    # Create the directories.
    path = os.path.abspath(directory)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_dir(data_directory, sub_directory, network, station, location, channel=None):
    """Create tags for directories and files."""
    if channel is None:
        directory_tag = os.path.join(data_directory, sub_directory, get_tag(".", [network, station, location]))
        file_tag = get_tag(".", [network, station, location])
    else:
        directory_tag = os.path.join(data_directory, sub_directory, get_tag(".", [network, station, location]), channel)
        file_tag = get_tag(".", [network, station, location, channel])
    return directory_tag, file_tag


def get_tag(tag_char, tag_list):
    """Create tag for the files and directories."""
    tag = tag_char.join(tag_list)
    return tag


def get_window_tag(window_width_hour):
    """Create smoothing window tag based on its length moving window length in hours
       - 6hrs 12hrs 1d(24h) 4d(96h) 16d(384h)"""
    if int(window_width_hour) < 24:
        window_tag = f'{window_width_hour}h'
    else:
        window_tag = f'{int(int(window_width_hour)/24)}d'

    return window_tag


def get_file_name(naming_convention, file_path, tag_list):
    """Create file name
       PQLX if file name contains time, it will be in HH24:MM:SS format
       WINDOWS if file name contains time, it will be in HH24_MM_SS format"""
    
    if naming_convention != 'PQLX':
        for i in range(len(tag_list)):
            tag_list[i] = tag_list[i].replace(':', '_')
    this_tag = f'{get_tag(".", tag_list)}.txt'
    file_name = os.path.join(file_path, this_tag)

    return file_name


def get_file_times(naming_convention, channel, filename):
    """  get file times by extracting file start and end times from the file name
    time is assumed to be included in the file name in CHA.Time1.Time2 format
    Time1 and Time2 are returned as string
 
    PQLX if file name contains time, it will be in HH24:MM:SS format
    WINDOWS if file name contains time, it will be in HH24_MM_SS format"""
    
    start_time = filename.split(channel+'.')[1].split('.')[0]
    end_time = filename.split(channel+'.')[1].split('.')[1]
    if naming_convention != "PQLX":
        start_time = start_time.replace('_', ':')
        end_time = end_time.replace('_', ':')

    return start_time, end_time

