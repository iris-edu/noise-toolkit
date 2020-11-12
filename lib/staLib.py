"""

 HISTORY:
    2020-11-16 Manoch: R.2.0.0 Python 3 and adoption of PEP 8 style guide.
    2017-01-18 Manoch: added support for '' (blank) location codes
                       blank location codes can be represented as blank or None
    2014-02-07 Manoch: created

"""


def get_location(location):
    """Check for blank location codes (DASH)"""
    if location.strip().lower() == "dash":
        return "--"
    elif len(location.strip()) == 0 or location.strip().lower() == "none":
        return "--"
    else:
        return location.strip()
