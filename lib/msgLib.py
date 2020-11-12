
def message(run_message):
    """Post a run message."""
    marker = 20 * '*'
    print(f'\n{marker} {run_message} {marker}\n')


def error(error_message, exit_code):
    """Post an error message."""
    print(f'[ERR] {error_message}\n')
    return exit_code


def info(info_message):
    """Post a warning message."""
    print(f'[INFO] {info_message}')


def warning(warn_sender, warn_message):
    """Post a warning message."""
    print(f'[WARN] from {warn_sender}: {warn_message}')
