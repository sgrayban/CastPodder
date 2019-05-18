#
# CastPodder player handling module
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: players.py 147 2006-11-07 08:17:03Z sgrayban $

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "Commercial"


import platform
import os
import logging
import re

log = logging.getLogger('iPodder')

UNCHECKED_SONGS = "__UNCHECKED_SONGS__"

class CannotInvoke(AssertionError): 
    """Player objects raise this in __init__ if they can't be invoked 
    on this system."""
    pass

class Player(object): 
    """Generic dict-style interface to media players."""

    def __init__(self): 
        """Raise CannotInvoke if you can't be used."""
        object.__init__(self)
        raise NotImplementedError

    def append_and_create(self, filename, playlistname, playnow=True): 
        """Add the tune to the playlist. Create the list if necessary.
        Don't add the tune if it's there already."""
        raise NotImplementedError

    def get_rating(self, filename, playlistname): 
        """Get the rating (0-100) for a particular entry in a 
        particular playlist. Probably iTunes specific, but perhaps 
        not."""
        raise NotImplementedError

    def playlist_filenames(self, playlistname): 
        """Return a list of files referred to by a particular 
        playlist."""
        raise NotImplementedError

    def play_file(self,filename, rude=False): 
        """Play a file."""
        raise NotImplementedError

    def remove_files(self,filesinfo):
        """Remove a list of files."""
        raise NotImplementedError
    
    def sync(self): 
        """Synchronise changes to the media player."""
        raise NotImplementedError

def makeOS9abspath(path):
    """Returns an ":" delimited, OS 9 style absolute path."""
    import Carbon.File, os.path
    rv = []
    fss = Carbon.File.FSSpec(path)
    while 1:
        vrefnum, dirid, filename = fss.as_tuple()
        rv.insert(0, filename)
        if dirid == 1: break
        fss = Carbon.File.FSSpec((vrefnum, dirid, ""))
    if len(rv) == 1:
        rv.append('')
    return ':'.join(rv)

class NoPlayer(Player): 
    """For when the user doesn't want player integration or
    has a player we don't yet support."""

    def __init__(self):
        return
    
    def append_and_create(self, filename, playlistname, playnow=True): 
        """Returns quietly without doing anything."""
        return

    def playlist_filenames(self, playlistname): 
        """Returns an empty list."""
        return []

    def remove_files(self,filesinfo):
        """Returns quietly without doing anything."""
        return
    
    def sync(self): 
        """Returns quietly without doing anything."""
        return
    
def sanitize(string, safechars): 
    """Sanitize the string according to the characters in `safe`."""
    # First, get the function's cache dict. 
    try: 
        safecache = sanitize.safecache
    except AttributeError: 
        safecache = sanitize.safecache = {}
    # Next, fetch or set a dict version of the safe string. 
    safehash = safecache.get(safechars)
    if safehash is None: 
        safehash = safecache[safechars] = {}
        for char in safechars: 
            safehash[char.lower()] = 1
    # Finally, sanitize the string.
    reslist = []
    for char in string: 
        lower = char.lower()
        if safehash.get(lower, 0): 
            reslist.append(char)
    return ''.join(reslist)
    
player_classes = [NoPlayer]

try:
    import xmms.control
    class XMMSPlayer(Player): 
      """Generic dict-style interface to media players."""

      
      def __init__(self): 
          """Raise CannotInvoke if you can't be used."""
          object.__init__(self)
          self.currentPlaylistFileName = ""
          print "USING XMMS"

      def append_and_create(self, filename, playlistname, playnow=True): 
          """Add the tune to the playlist. Create the list if necessary.
          Don't add the tune if it's there already."""
          print "append_and_create"
          print filename, playlistname, playnow

      def get_rating(self, filename, playlistname): 
          """Get the rating (0-100) for a particular entry in a 
          particular playlist. Probably iTunes specific, but perhaps 
          not."""
          print "get_rating"
          print filename, playlistname

      def playlist_filenames(self, playlistname): 
          """Return a list of files referred to by a particular 
          playlist."""
          print "playlist_filenames"
          print playlistname

      def play_file(self,filename, rude=False): 
          """Play a file."""
          xmms.enqueue_and_play_launch_if_session_not_started( [ filename ] )
          #xmms.control.enqueue_and_play( [ filename ] )
          print "play_file"
          print filename, rude

      def remove_files(self,filesinfo):
          """Remove a list of files."""
          xmms.control.playlist_delete( filesinfo )
          print "remove_files"
          print filesinfo

      def sync(self):
          """Synchronise changes to the media player."""
          print "sync"
          
          
    player_classes.insert( len(player_classes)-2, XMMSPlayer )
    print player_classes
except ImportError, ex:
    print "xmms couldn't be imported" 
    pass 

try:
    import bmp.control
    class BMPPlayer(Player): 
      
      def __init__(self): 
          """Raise CannotInvoke if you can't be used."""
          object.__init__(self)
          self.currentPlaylistFileName = ""
          print "USING BMP"

      def append_and_create(self, filename, playlistname, playnow=True): 
          """Add the tune to the playlist. Create the list if necessary.
          Don't add the tune if it's there already."""
          print "append_and_create"
          print filename, playlistname, playnow

      def get_rating(self, filename, playlistname): 
          """Get the rating (0-100) for a particular entry in a 
          particular playlist. Probably iTunes specific, but perhaps 
          not."""
          print "get_rating"
          print filename, playlistname

      def playlist_filenames(self, playlistname): 
          """Return a list of files referred to by a particular 
          playlist."""
          print "playlist_filenames"
          print playlistname

      def play_file(self,filename, rude=False): 
          """Play a file."""
          bmp.enqueue_and_play_launch_if_session_not_started( [ filename ] )
          print "play_file"
          print filename, rude

      def remove_files(self,filesinfo):
          """Remove a list of files."""
          bmp.control.playlist_delete( filesinfo )
          print "remove_files"
          print filesinfo

      def sync(self):
          """Synchronise changes to the media player."""
          print "sync"
          
    player_classes.insert( len(player_classes)-1, BMPPlayer )
    print player_classes
except ImportError, ex:
    print "Beep-Media-Player couldn't be imported" 
    pass 

def all_player_types(): 
    """Return a list of all defined player classes, workable or not."""
    return [pclass.__name__ for pclass in player_classes]

def player_types(): 
    """Return a list of invokable player classes for this system."""
    valid = []
    log.debug("Looking for invokable players...")
    for pclass in player_classes: 
        name = pclass.__name__
        try: 
            if pclass.__name__=="iTunes":
		pclass().version()
	    else:
		pclass()
            log.debug("Successfully invoked player %s.", name)
            valid.append(name)
        except CannotInvoke: 
            log.debug("Can't invoke %s.", name)
    return valid

def get(name): 
    """Get a player object by class name. Returns None if it can't 
    be invoked. Raises KeyError if it doesn't exist."""
    matches = [pclass for pclass in player_classes 
               if pclass.__name__.lower() == name.lower()]
    assert len(matches) <= 1
    if not matches: 
        log.debug("Couldn't locate requested player class %s", name)
        raise KeyError
    pclass = matches[0]
    try: 
	if pclass.__name__ == "iTunes":
		return pclass().version()
	else:
        	return pclass()
    except CannotInvoke, ex: 
        log.debug("Couldn't invoke requested player class %s", name)
        return None

if __name__ == '__main__': 
    # test code
    import conlogging
    logging.basicConfig()
    handler = logging.StreamHandler()
    handler.formatter = conlogging.ConsoleFormatter("%(message)s", wrap=False)
    log.addHandler(handler)
    log.propagate = 0
    log.setLevel(logging.DEBUG)
    log.info("Defined player classes: %s", ', '.join(all_player_types()))
    log.info("Invokable player classes: %s", ', '.join(player_types()))

    player = get(player_types()[0])
