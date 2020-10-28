#
# check for blank location codes (DASH)
#
def getLocation(location):
	if location.strip() == "DASH" or len(location.strip()) == 0:
	    return  "--"
        else:
	    return  location.strip()
