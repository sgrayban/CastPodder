# 
# CastPodder configuration module
#
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: configuration.py 147 2006-11-07 08:17:03Z sgrayban $

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "Commercial"

__version__ =  '5.5'

import platform
import os
from os.path import join, abspath, split, isdir, isfile, exists
import logging
import sys
import optparse
import platform
import string
import re

# Parts of CastPodder
import players
import feeds
import hooks
import contrib.portalocker as portalocker
from gui.skin import PODCAST_DIRECTORY_ROOTS

log = logging.getLogger('iPodder')

array = []

## BEGIN new stuff motto
## Multimedia player parameters - Edit me!
VIDEOPLAYER = "xine"
WMVPLAYER = "gmplayer"
PDFPLAYER = "xpdf"
RTFPLAYER = "ooffice2 -writer"
EXTENSIONS = ["mov","mpg","wmv","avi","m4v","mp4","pdf","m4a","rtf"]
SYNCPATH = ""
## END new imports + variables by motto


#Debug params - Edit me
DEBUG = False
TIMER_INTERVAL = 10000
CONFIG_FILE_VERSION = 6

class RunTwiceError(Exception): 
    """Raised when CastPodder determines it is already running."""
    pass

class ConfigManagerConnectError(Exception):
    """Raised when unable to connect to the config manager, either
    because of missing connection data, network problems, or a bad
    password."""
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def determine_paths(): 
    """Figure out where to put stuff by default.

    Returns dict with keys base, gui, home, appdata."""

    base = abspath(split(sys.argv[0])[0])
    log.debug("CastPodder is hosted out of: %s", base)

    gui = appdata = home = downloads = preloads = None # sentinel defaults
    plat = platform.system()
    plat = plat.upper()
    
    if plat.find('WINDOWS') >= 0:
        try: 
            # If HOMEDRIVE and HOMEPATH exist, it looks like we're on 
            # Windows 2000 or above, in which case we should put stuff 
            # in a subdirectory of the user's Application Data. 
            home = join(os.environ['HOMEDRIVE'], 
                                os.environ['HOMEPATH'])
            log.debug("NT-style home directory: %s", home)
            appdatatop = join(home, "Application Data") # default
            appdatatop = os.environ.get('APPDATA', appdatatop) # on XP
            if isdir(appdatatop): 
                appdata = join(appdatatop, "iPodder")
            else: 
                log.warn("Unable to find user's Application Data "\
                         "directory.")
            mydocs = join(home, "My Documents")
            if isdir(mydocs): 
                downloads = join(mydocs, "My Received Podcasts")
                
        except KeyError: 
            appdatatop = os.environ.get('APPDATA', None)	
            if appdatatop is not None and isdir(appdatatop): 
                appdata = join(appdatatop, "iPodder")
            log.debug("Unable to find user's home directory. "\
                      "Defaulting to storing iPodder data in .")

    else: # unknown platform
        home = os.environ.get('HOME')
        if home is None: 
            log.warn("Unable to find user home directory.")
        else: 
            # UNIX-style defaults
            appdata = join(home, 'iPodderData')
            
    if appdata is None: 
        appdata = join(base, "data")
        log.warn("Unable to find an appropriate place to put "\
                 "iPodder's data. Defaulting to %s", appdata)

    if gui is None: 
        gui = join(base, "gui")

    if preloads is None:
        preloads = join(base, "preloads")
        
    return {
        'base': base, 
        'appdata': appdata, 
        'downloads': downloads,
        'home': home, 
        'gui': gui,
        'preloads': preloads
        }

def makeCommandLineParser(): 
    """Make the default command line option parser.
    
    Versions of CastPodder inheriting from the base version can extend this 
    parser with other options, or can over-ride settings of existing 
    options. The Configuration object lets the command line take 
    precedence over anything loaded from the configuration file.
    
    TODO: have CLI options *not* get written to the config file."""

    usage = "usage: %prog [options]\n\n"\
            "MOST OPTIONS CAUSE CHANGES TO THE CONFIGURATION FILE IF SAVED."

    parser = optparse.OptionParser(usage = usage,
                                   version = "%prog " + __version__)
    
    parser.add_option('-d', '--debug', 
                      dest = 'debug', 
                      action = 'store_true', 
                      default = False, 
                      help = "Tell you more than you probably need to know.")
    
    parser.add_option('-c', '--config', 
                      dest = 'config_file', 
                      action = 'store', 
                      type = 'string', 
                      default = None,
                      help = "Specify where to find ipodder.cfg")
    
    parser.add_option('-f', '--favorites', 
                      dest = 'favorites_file', 
                      action = 'store', 
                      type = 'string', 
                      default = None,
                      help = "Override: specify which favorites file to use")
    
    parser.add_option('-D', '--downloads', 
                      dest = 'download_dir', 
                      action = 'store', 
                      type = 'string', 
                      default = None,
                      help = "Override: specify where to put downloads")
    
    parser.add_option('-U', '--force-playlist-updates', 
                      dest = 'force_playlist_updates', 
                      action = 'store_true', 
                      default = None, 
                      help = "Force playlist updates even if no new items "\
                             "needed to be downloaded.")

    parser.add_option('-P', '--player', 
                      dest = 'player_type', 
                      action = 'store', 
                      type = 'string', 
                      default = None,
                      help = "Select which player (%s) to use." % (
                          ', '.join(players.all_player_types())))

    parser.add_option('--bloglines-username', 
                      dest = 'bl_username', 
                      action = 'store', 
                      type = 'string', 
                      default = None,
                      help = "Bloglines username")

    parser.add_option('--bloglines-password',
                      dest = 'bl_password', 
                      action = 'store', 
                      type = 'string', 
                      default = None,
                      help = "Bloglines password")

    parser.add_option('--bloglines-folder', 
                      dest = 'bl_folder', 
                      action = 'store', 
                      type = 'string', 
                      default = None,
                      help = "Bloglines folder")

    parser.add_option('-n', '--dry-run',
                      dest = 'dry_run', 
                      action = 'store_true', 
                      default = False,
                      help = "Don't actually download enclosures")

    parser.add_option('--add-feed',
                      dest = 'add_feed',
                      action = 'store',
                      default = None,
                      help = "The URL of a feed to add to the subscription list")

    parser.add_option('--add-feed-from-rss',
                      dest = 'add_feed_from_rss',
                      action = 'store',
                      default = None,
                      help = "A feed to add to the subscription list")

    return parser
 
# Configuration options. If it isn't defined here, it won't be loaded 
# from the configuration file. 

configOptions = [
    # ('key',default, exposed, remoteable)
    ('appdata_dir', None, True, False),
    ('gui_dir', None, False, False),
    ('download_dir', None, True, False),
    ('sync_dir', '/mnt/sda1', True, False),
    ('debug', False, True, False),
    ('player_type', 'XMMSPlayer', True, True),
    ('force_playlist_updates', False, False, False),
    ('bl_username', '', True, False),
    ('bl_password', '', True, False),
    ('bl_folder', '', True, False),
    ('hide_on_startup', False, True, True),
    ('hide_tray_icon', False, True, False),
    ('scan_on_startup', False, True, True),
    ('X_behaviour', 'ask', False, False),
    ('dl_command_enable', False, True, False),
    ('dl_command', '',True, False),
    # min to wait between polls of a feed, unless force_playlist_updates
    # politeness * 60 seconds
    ('politeness', 5, True, False),
    ('dry_run', False, False, False),
    ('use_new_download_code', False, False, False),
    ('min_mb_free', 1024, True, False),
    ('max_scan_jobs', 4, True, False), # maximum jobs
    ('max_download_jobs', 2, True, False), # maximum jobs
    ('timeout', 60, True, False),
    ('podcast_directory_roots', PODCAST_DIRECTORY_ROOTS, False, False),
    ('show_log_page', False, True, False),
    ('use_proxy_server', False, True, False),
    ('http_proxy_server', '', True, False),
    ('http_proxy_port', '', True, False),
    ('http_proxy_username', '', True, False),
    ('http_proxy_password', '', True, False),
    ('play_on_download', False, True, True),
    ('window_dimensions', None, True, False),
    ('window_is_maximized', False, True, False),
    ('feedslist_col_sort', None, True, False),
    ('coralize_urls', False, True, False),
    ('feedmanager_enable', False, True, False),
    ('feedmanager_opml_url', '', True, True),
    ('screen_language', None, True, False),
    ('clp_play_command', None, True, False),
    ('pl_opt_iTunes_ow_genre_enable', False, True, True),
    ('pl_opt_iTunes_ow_genre', 'Podcast', True, True),
    ('chkupdate_on_startup', True, True, False),
    ('listen_port', None, True, False),
    ('ensure_oneclick_handler', False, True, True),
    ('ask_ensure_oneclick_handler', True, True, False),
    ('catchup_marks_downloaded', True, True, True),
    ('ask_catchup_marks_downloaded', True, True, False),
    ('goto_background_on_close', True, True, False),
    ('ask_goto_background_on_close', True, True, False),
    ('sched_runTimes', None, True, True),
    ('sched_runTimesEnable', None, True, True),
    ('sched_defaultMinute', None, True, True),
    ('sched_runMode', None, True, True),
    ('sched_enableAuto', None, True, True),
    ('sched_intervalHours', None, True, True),
    ('sched_startingAt', None, True, True),
    ('config_manager_enable', False, True, False),
    ('config_manager_url', None, True, False),
    ('config_manager_username', None, True, False),
    ('config_manager_password', None, True, False),
    ('config_manager_settings_url', None, True, True),
    ('config_file_version',5,True,False),
    ]

# build configDefaults dictionary
configDefaults = {}
for key, default, exposed, remoteable in configOptions:
    configDefaults[key] = default

class Configuration(object): 
    "Object to hold CastPodder configuration."

    def __init__(self, options): 
        "Initialise CastPodder configuration."
        log.debug("Initialising configuration object.")

        self.hooks = hooks.HookCollection()

        paths = determine_paths()
        appdata = paths['appdata']
        gui = paths['gui']
        downloads = paths['downloads']

        if options.config_file: 
            config = self._loadconfig(options.config_file)
        else: 
            config = self._findconfig(paths)
        if config is None: 
            loaded = dirty = False
            config = {}
        else: 
            loaded = True
            dirty = False
        
        # Let people tailor appdata_dir, gui_dir, download_dir, debug, 
        # player_type, etc. 
        # TODO: warn them if they try to do more than that. 

        defaults = configDefaults.copy() # what are our defaults?
        defaults['appdata_dir'] = appdata
        defaults['gui_dir'] = gui
        defaults['download_dir'] = downloads

        # Eliminate troublesome configuration file entries --  useful if 
        # someone added a configuration entry and set it visible, and then 
        # we wanted to change the default later. 
        vermin = [] # was ['podcast_directory_roots']
        for victim in vermin: 
            if config.has_key(victim): 
                log.warn("Eliminating %s from configuration file.", victim)
                log.debug("(default is %s)", defaults[victim])
                del config[victim]
                dirty = True
                continue
            
        # Copy in variables from the loaded configuration, defaulting to 
        # the defaults defined above. 
        for key, default in defaults.items(): 
            if key == 'podcast_directory_roots': 
                try: 
                    # Merge them in
                    rootdict = dict(default) # map URL -> display name
                    cfgval = config.get(key, [])
                    res = []
                    log.debug("Loading podcast directory roots from " \
                              "configuration file...")
                    
                    # Do they refer to ANY of the default feeds?
                    for url, title in cfgval: 
                        if rootdict.has_key(url): 
                            break
                    else: 
                        # No: okay, we need to prepend ours
                        log.debug("Looks like the user is only adding feeds.")
                        cfgval = default + cfgval
                    
                    # Import new directories and over-ride the titles of
                    # old ones mentioned in the configuration file. 
                    for url, title in cfgval: 
                        res.append((url, title))
                        if rootdict.has_key(url): 
                            if title != rootdict[url]: 
                                log.debug("Title for default directory %s " \
                                          "over-ridden to %s", url, title)
                            del rootdict[url]
                        else: 
                            log.debug("User directory added: %s (%s)", 
                                      title, url)

                    # Assert any missing defaults.
                    for url, title in default: 
                        if rootdict.get(url) is not None:
                            # The configuration file didn't specify a 
                            # directory specified in our defaults, so 
                            # we'll add it at the bottom. 
                            log.debug("Asserting default directory %s (%s)", 
                                      title, default)
                            res.append((url, title))

                    # Store the results. 
                    setattr(self, key, res)
                except Exception, ex: 
                    log.exception("The user-specified podcast_directory_roots " \
                                  "option caused an exception, so we'll use " \
                                  "the default option instead.")
                    setattr(self, key, default)
            else: 
                setattr(self, key, config.get(key, default))
            
        if self.download_dir is None: 
            # Calculate the default download_dir if determine_paths didn't. 
            # Delayed because we didn't know appdata for sure 'til now. 
            self.download_dir = join(appdata, 'downloads')

        # Now, over-ride again with the command line options. 
        first = True
        self.masked_options = []
        for att in configDefaults.keys(): 
            if not hasattr(options, att): 
                continue
            val = getattr(options, att)
            if val is not None: 
                if att == 'debug': 
                    # Only over-ride config's debug if CLI set it to true
                    if not val: 
                        continue
                if first: 
                    log.debug("Over-riding defaults or configuration file.")
                    first = False
                log.debug("%s = %s", att, val)
                setattr(self, att, val)
                self.masked_options.append(att)
                
        # ---- DO NOT INTERPRET ANY MORE OPTIONS BELOW THIS LINE ----

        log.debug("Deferring player invocation until we need it.")
        
        # Put the files where they belong. No configuration allowed. 
        self.history_file = join(appdata, "history.txt")
        self.favorites_file = join(appdata, "favorites.txt")
        self.schedule_file = join(appdata, "schedule.txt")
        self.delete_list_file = join(appdata, "delete_list.txt")
        self.state_db_file = join(appdata, "iPodder.db")
        self.guiresource_file = join(gui, "CastPodder.xrc")
        self.mediasync_file = join(gui, "sync-player.xrc")

        if not exists(self.appdata_dir): 
            log.info("Creating application data directory %s", 
                     self.appdata_dir)
            os.makedirs(self.appdata_dir)

        if not exists(self.download_dir): 
            log.info("Creating download directory %s", self.download_dir)
            os.makedirs(self.download_dir)

        if dirty or not loaded: 
            self.configfile = join(self.appdata_dir, "ipodder.cfg")
            if dirty: 
                log.info("Flushing alterations to configuration file %s", 
                         self.configfile)
            else: 
                log.info("Creating default configuration file %s", 
                         self.configfile)
            self.flush()

        if self.config_file_version < CONFIG_FILE_VERSION:
            self.upgrade_logic(self.config_file_version)
    
    def _loadconfig(self, filename): 
        """Attempt to load the configuration from `filename`.

        Returns None if the configuration file doesn't exist, or a dict 
        containing whatever the configuration file had. Raises exceptions 
        if the configuration file exists but can't be loaded."""

        log.debug("Attempting to load config file %s", filename)
        lockfilename = filename + '.lock'
        try: 
            lfp = self.lockfilefp = file(lockfilename, 'wt')
            lfp.write("This is CastPodder's lock file.")
            portalocker.lock(lfp, portalocker.LOCK_EX|portalocker.LOCK_NB)
        except OverflowError, ex: 
            log.exception("I can't check to see if another CastPodder is running.")
        except Exception, ex: 
            log.fatal("Another CastPodder process is running. Please kill it " \
                      "and try again. If you are absolutely sure another " \
                      "CastPodder process is not running, delete the lock " \
                      "file: %s", lockfilename, exc_info=True)
            raise RunTwiceError
            
        config = {}
        try: 
            execfile(filename, {}, config)
        except Exception, ex: 
            log.exception("Caught exception loading config file %s", 
                    filename)
            sys.exit(1)
        log.info("Successfully loaded config file %s", filename)
        for key, val in config.items(): 
            log.debug("%s = %s", key, val)
        self.configfile = filename
        return config

    def _findconfig(self, paths): 
        """Tries to find and load a configuration file.
        
        paths -- path object from `determine_paths`."""

        for dirkey in ['appdata', 'home', 'base']: 
            path = paths[dirkey]
            if path is not None:
                configfile = join(path, "ipodder.cfg")
                if isfile(configfile): 
                    config = self._loadconfig(join(path, "ipodder.cfg"))
                    if config is not None: 
                        return config
        return None

    def load_remote_config(self):
        log.debug("load_remote_config: Attempting to load remote configuration.")
        if not self.config_manager_url:
            log.debug("load_remote_config: Couldn't find config_manager_url, bailing out.")
            raise ConfigManagerConnectError("We couldn't find the Configuration Manager URL.")
        if not self.config_manager_username or not self.config_manager_password:
            log.debug("load_remote_config: Couldn't find username or password, bailing out.")
            raise ConfigManagerConnectError("We couldn't find the Configuration Manager username or password.")

        #Looks like we have everything we need.  Time to try to connect.
        #TODO: add proxy support, figure out exception handling.
        import xmlrpclib
        s = xmlrpclib.Server(self.config_manager_url)
        try:
            r = s.ipodderConfigManager.getConfig(self.config_manager_username,\
                                          self.config_manager_password)
        except:
            log.exception("load_remote_config: Error connecting to config manager.")
            raise ConfigManagerConnectError("There was a problem connecting to the configuration manager.  Try re-entering your username and password, and if that doesn't work, contact your service provider.")

        for key, default, exposed, remoteable in configOptions:
            if remoteable:
                if r.has_key(key):
                    log.debug("load_remote_config: Setting remotable option %s = %s." % (key,str(r[key])))
                    setattr(self, key, r[key])
                else:
                    log.debug("load_remote_config: Option %s is remoteable but we got no value." % key)
    
    def flush(self): 
        "Write the configuration back to the configuration file."
        log.debug("Writing configuration to %s", self.configfile)
        config = file(self.configfile, 'wt')
        self.dump(handle = config)
        config.close()

    def dump(self, handle=sys.stdout): 
        "Dump configuration to `handle`."
        print >> handle, "# CastPodder configuration file."
        print >> handle, "# DO NOT MODIFY YOURSELF IF CASTPODDER IS RUNNING."
        print >> handle, "#"
        for key, default, exposed, remoteable in configOptions:
            value = getattr(self, key)
            if exposed or value != default: 
                print >> handle, "%s = %s" % (key, repr(value))

    def determine_player(self): 
        # Nut out the player. 
        self.hooks.get('invoke-player-begin')()
        self.player = player = None
        player_type = self.player_type
        if player_type.lower() == 'none': 
            log.info("Not using a media player; just downloading files.")
        elif player_type.lower() == 'auto': 
            log.info("Trying to determine your player type...")
            options = players.player_types()
            if len(options) < 1: 
                log.error("Can't detect an invokable player. Will download, "\
                          "but won't do anything else.")
            else: 
                player_type = options[0]
                log.info("Automatically selected %s as your media player.",
                         player_type)
                player = players.get(player_type)
        else: 
            try: 
                player = players.get(player_type)
            except KeyError: 
                log.critical("Requested media player %s is not defined.", 
                             player_type)
            if player is None: 
                log.critical("Requested media player %s can't be invoked.",
                             player_type)
        self.player_type = player_type
        self.player = player
        self.hooks.get('invoke-player-end')()
        return self.player

    def __getattr__(self, att): 
        "Calculate missing attributes on the fly."
        if att == 'player': 
            return self.determine_player()
        else: 
            raise AttributeError, att

    def upgrade_logic(self, from_version):
        """Run any upgrade logic that might be necessary."""

        #CastPodder 5.2: if we get here there's only one thing to do.
        self.upgrade_to_v6()

    def upgrade_to_v6(self):

        #Reset the one-click handler settings as we've expanded our reach.
        log.info("Upgrading config file to version 6, CastPodder 4.1")
        self.ensure_oneclick_handler = False
        self.ask_ensure_oneclick_handler = True
        self.config_file_version = CONFIG_FILE_VERSION
        self.flush()

if __name__ == '__main__': 
    import conlogging
    # test code
    logging.basicConfig()
    handler = logging.StreamHandler()
    handler.formatter = conlogging.ConsoleFormatter("%(message)s", wrap=False)
    log.addHandler(handler)
    log.propagate = 0
    parser = makeCommandLineParser()
    options, args = parser.parse_args()
    if args: 
        parser.error("only need options; no arguments.")
    if options.debug: 
        log.setLevel(logging.DEBUG)
    config = Configuration(options)
    config.dump()

