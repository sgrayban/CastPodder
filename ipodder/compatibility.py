#
# CastPodder compatibility module
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: compatibility.py 147 2006-11-07 08:17:03Z sgrayban $
# Various helper code for compatibility with versions of CastPodder.

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "Commercial"

import logging
import os, sys

log = logging.getLogger('CastPodder')

def migrate_2x_tmp_downloads(basepath,state):

    result = []

    try:
        #This path should not be part of a zip file.
        path = os.path.join(basepath,"compat","2x")
        sys.path.append(path)
        encinfolist = state['tmp_downloads']
        sys.path.remove(path)
        from ipodder.core import Enclosure
        for i in range(len(encinfolist)):
            encinfo = encinfolist[i]
            try:
                compatible_enclosure = Enclosure(
                    encinfo.url, \
                    encinfo.feed, \
                    encinfo.length, \
                    encinfo.marked, \
                    encinfo.item_title, \
                    encinfo.description, \
                    encinfo.item_link)
                compatible_enclosure.status = encinfo.status
                compatible_enclosure.creation_time = encinfo.creation_time
                compatible_enclosure.download_started = encinfo.download_started
                compatible_enclosure.download_completed = encinfo.download_completed
                result.append(compatible_enclosure)
            except:
                log.exception("Error migrating 2x-style tmp_downloads entry %d." % i)
                pass
        #Now save the fruits of our labor.
        state['tmp_downloads'] = result
        state.sync()
    except:
        log.exception("Error migrating 2x-style tmp_downloads.")
        pass

    return result
