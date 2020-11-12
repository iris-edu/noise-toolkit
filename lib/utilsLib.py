import sys
import os
from time import time
from urllib.request import urlopen

from obspy.core import UTCDateTime
import msgLib as msg_lib


class ObjDict(dict):
    """Accessing dictionary items as object attributes:
            https://goodcode.io/articles/python-dict-object/
    """

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: {}".format(name))

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: {}".format(name))


def get_args(arg_list, usage):
    """Get the run arguments.
  """
    args_dict = dict()

    for _i, arg_value in enumerate(arg_list):

        # Skip the script's name.
        if _i <= 0:
            continue
        if arg_value.strip() == 'usage':
            usage()
            sys.exit()
        try:
            key, value = arg_value.split('=')
            args_dict[key] = value
        except Exception as _ex:
            usage()
            code = msg_lib.error(f'Bad {arg_value} parameter!\n{_ex}', 3)
            sys.exit(code)
    return args_dict


def get_param(arg_dict, key, default_value, usage):
    """ Get a run argument for the given key.
  """
    if key in arg_dict.keys():
        return arg_dict[key]
    elif default_value is not None:
        return default_value
    else:
        usage()
        code = msg_lib.error(f'missing parameter {key}', 1)
        sys.exit(code)


def time_info(date_time, seconds=0):
    """Extract and return date-time information from date_time string."""
    datetime = UTCDateTime(date_time) + seconds
    year = datetime.strftime("%Y")
    month = datetime.strftime("%m")
    day = datetime.strftime("%d")
    doy = datetime.strftime("%j")

    return datetime, year, month, day, doy


def get_fedcatalog_url(request_net, request_sta, request_loc, request_chan, request_start, request_end):
    fedcatalog_ur = f'net={request_net}&sta={request_sta}&loc={request_loc}&' \
                    f'cha={request_chan}&targetservice=dataselect&level=channel&format=request&' \
                    f'start={request_start}&end={request_end}&' \
                    f'includeoverlaps=false&nodata=404'
    return fedcatalog_ur


def is_number(n):
    """Check if the input string input is a number.
    """
    try:
        float(n)
    except ValueError:
        return False
    return True


def param(params, var):
    """Get a variable from the parameter file by name"""
    if var in dir(params):
        return params
    code = msg_lib.error(f'variable {var} is not in the parameter file', 3)
    sys.exit(code)


def time_it(who, t0):
    """Compute elapsed time since the last cal."""
    t1 = time()
    dt = t1 - t0
    t = t0
    if dt > 0.05:
        msg_lib.message(f'{who} [TIME] {dt:0.2f} seconds')
        t = t1
    return t


def read_url(target_url, verbose=False):
    """Read content of a URL."""
    if verbose:
        msg_lib.info(f'Opening URL: {target_url}')

    with urlopen(target_url) as url:
        content = url.read().decode()
    return content


def mkdir(target_directory):
    """ Make a directory if it does not exist."""
    directory = None
    try:
        directory = target_directory
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory
    except Exception as _er:
        code = msg_lib.error(f'Failed to create directory {directory}\n{_er}', 3)
        return None


def is_true(flag):
    """Check to see if a given flag represents True condition."""
    if is_number(flag):
        if int(flag) == 0:
            return False
        else:
            return True

    if flag is None:
        return False

    if not flag:
        return False
    else:
        return True
