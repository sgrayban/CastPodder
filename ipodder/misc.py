# 
# CastPodder miscellaneous methods
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: misc.py 147 2006-11-07 08:17:03Z sgrayban $

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "Commercial"

import os
import logging
import time

try: 
    import win32api
except ImportError: 
    win32api = None
    
log = logging.getLogger('iPodder')

def freespace(path): 
    "Return free disk space in MB for the requested path; -1 if unknown."
    if win32api is not None: 
        cwd = os.getcwd()
        try: 
            os.chdir(path)
            sps, bps, freeclusters, clusters = win32api.GetDiskFreeSpace()
            return sps * bps * freeclusters
        finally: 
            os.chdir(cwd)
    else:
        # These three lines could probably replace all of this?
        import statvfs
        stats = os.statvfs(path)
        return stats[statvfs.F_BAVAIL] * stats[statvfs.F_BSIZE]

    if not freespace.warned: 
        freespace.warned = True
        log.warn("Can't determine free disk space.")
    return -1
    
freespace.warned = False

def rename(old,new,backup=False):
    """Like os.rename, but first clears the new path so Windows
    won't throw Errno 17.  Optionally backs up the new location
    if something is there."""
    if not os.path.exists(old):
        raise Exception, "File %s doesn't exist" % old
    try:
        if backup:
            os.rename(new,"%s-%d" % (new,int(time.time())))
        else:
            os.remove(new)
    except OSError, ex:
        errno, message = ex.args
        if errno != 2: # ENOFILE
            raise OSError, ex

    os.rename(old,new)
