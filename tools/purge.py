#!/usr/bin/env python
#
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: purge.py 147 2006-11-07 08:17:03Z sgrayban $

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "Commercial"

from ipodder import players
import os.path

player = players.get(players.player_types()[0])
bad = [t for t in player.iTunes.LibraryPlaylist.Tracks
       if not (hasattr(t, 'Location') and t.Location and os.path.isfile(t.Location))]
print len([t.Delete() for t in bad])
