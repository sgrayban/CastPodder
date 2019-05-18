#
# CastPodder core code
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: core.py 147 2006-11-07 08:17:03Z sgrayban $

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "Commercial"

import platform
import sys
import urllib
import urllib2
import httplib
import os
from   os.path import *
from   string import join
import time
import re
from   sha import *

from   contrib.BitTorrent.bencode import bencode, bdecode
from   contrib.BitTorrent.btformats import check_message
import contrib.BitTorrent.download as download
import contrib.BitTorrent.track as track

###This doesn't work yet - sgrayban
##from   BitTorrent.bencode import bencode, bdecode
##from   BitTorrent.btformats import check_message
##import BitTorrent.track as track
##import BitTorrent.download as download

import contrib.urlnorm as urlnorm
from   threading import Event
import logging
import pickle, bsddb.db, bsddb.dbshelve

import socket # just so we can catch timeout
import StringIO

# Parts of iPodder
from ipodder import configuration
from ipodder import conlogging
from ipodder import feeds
from ipodder import hooks
from ipodder import engine
from ipodder import grabbers
from ipodder import misc
from ipodder import state as statemodule
from ipodder import history as historymodule

# Third-party parts of iPodder
from ipodder.contrib import urlnorm
from ipodder.contrib import feedparser

import ipodder

__version__ = configuration.__version__

AGENT = "CastPodder/%s (%s) +http://dev-1.borgforge.net/trac/castpodder/" %(__version__,platform.system())

log = logging.getLogger('iPodder')
SPAM = logging.DEBUG / 2

# Critical errors
CRITICAL_MINSPACE_EXCEEDED = 0

def PLEASEREPORT():
    log.exception("Please report this traceback:")

# Customise urllib
class AppURLopener(urllib.FancyURLopener):
    def __init__(self, *args):
        self.version = AGENT
        urllib.FancyURLopener.__init__(self, *args)
urllib._urlopener = AppURLopener()

class Enclosure:
    def __init__(self, url, feed, length, marked, item_title, item_description, item_link):
        """Initialise the `Enclosure`.
        
        url -- the url of the enclosure
        feed -- the feed it's in
        length -- the length of the enclosure
        marked -- marked for download?
        title -- title of the enclosing item"""
        
        self.url = url
        self.feed = feed
        self.marked = marked # for download
        self.length = length
        self.item_title = item_title
        self.creation_time = time.localtime()
        self.download_started = None
        self.download_completed = None
        self.description = item_description
        self.item_link = item_link
        self.status = "new"
        
    def unmark(self):
        "Unmark this enclosure for download."
        self.marked = False

    def GetStatus(self):
        """Return a displayable version of self.status.
        AG: Superseded by i18n lookups in str_dl_(state)"""
        if self.status == "new":
            return "New"
        if self.status == "queued":
            return "Queued"
        if self.status == "downloading":
            return "Downloading"
        if self.status == "cancelled":
            return "Cancelled"
        if self.status == "downloaded":
            return "Finished"
        if self.status == "partial":
            return "Partially downloaded"
        if self.status == "error":
            return "Error"
        log.debug("Enclosure has unknown status %s" % self.status)
        return "Unknown"
    
    def GetStatusDownloadSpeed(self):
        """Return a displayable version of self.status.  i18n lookups
        go in here."""
        retval = ""
        if self.status == "downloading" and hasattr(self,"grabber") and self.grabber:
            retval += "%.1f%%; %.1fkB/s" % ((100*self.grabber.fraction_done),self.grabber.download_rate/1024)
        return retval
    
    #We have to remove the feed object to make this pickleable.
    def __getstate__(self):
        state = self.__dict__.copy()
        state['feedid'] = self.feed.id
        del state['feed']
        return state
    
    def __setstate__(self,dict):
        self.__dict__.update(dict)
        self.feed = ipodder.get_feeds_instance()[self.feedid]
        del self.feedid
        if not hasattr(self,"creation_time"):
            self.creation_time = time.localtime()
        if not hasattr(self,"download_started"):
            self.download_started = None
        if not hasattr(self,"download_completed"):
            self.download_completed = None
        if not hasattr(self,"status"):
            self.status = "downloaded"
        if not hasattr(self,"description"):
            self.description = None
        if not hasattr(self,"item_link"):
            self.item_link = None
	#Not used just yet. Moving history into the db slowly
        #if not hasattr(self,"filename"):
        #    #TODO: client code assigns filename via history lookup
        #    self.filename = None

    def __str__(self): 
        "Return our filename as a string."
        return basename(self.feed.get_target_filename(self))
            
class FeedScanningJob(engine.Job): 
    """Feed scanning job."""
    
    def __init__(self, myengine, feedinfo, resultlist, state={}, catchup=0): 
        """Initialise the FeedScanningJob."""
        engine.Job.__init__(self, myengine, name=str(feedinfo))
        self.feedinfo = feedinfo
        self.resultlist = resultlist
        self.state = state
        self.catchup = catchup
        self.hooks = hooks.HookCollection()
        
    def _stop(self): 
        grabber = self.grabber # take a copy to avoid race condition
        if grabber is not None: 
            grabber.stop()
        
    def run(self): 
        """Run, Forrest! Run!"""
        feedinfo = self.feedinfo
        sio = StringIO.StringIO()
        # etag = feedinfo.get('etag', '')
        # modified = feedinfo.get('modified', '')
        self.grabber = grabbers.BasicGrabber(
                feedinfo.url, sio, state=self.state)
        # ... etag=etag, modified=modified, 
        try: 
            self.grabber()
            if hasattr(self.grabber,'is_cache_hit'):
                #Save for later since we set drop the reference to the grabber
                is_cache_hit = self.grabber.is_cache_hit
        except grabbers.AuthenticationError, ex:
            self.hooks('autherror',feedinfo)
            self.error("Auth error: Can't grab %s: %s", str(feedinfo), ex.message)
            return
        except grabbers.GrabError, ex: 
            self.error("Can't grab %s: %s", str(feedinfo), ex.message)
            feedinfo.status = "error"
            return
        self.grabber = None
        if self.abort: 
            log.debug("Asked to abort during or just after download.")
            return

        feed = feedparser.parse(sio.getvalue())
        for key in ['etag', 'modified', 'tagline', 'generator', 'link',
                                'lastbuilddate', 'copyright']:
                setattr(feedinfo, key, feed.get(key, ''))
        for key in ['copyright_detail', 'title_detail']:
                setattr(feedinfo, key, dict(feed.get(key, {})))
        feedinfo.version = feed.get('version', 'unknown')
        channeltitle = feed.feed.get('title')
        if channeltitle: 
            if not feedinfo.title:
                self.info("Naming feed #%d \"%s\"", 
                          feedinfo.id, channeltitle)
                feedinfo.title = channeltitle
            elif feedinfo.title != channeltitle:
                self.info("Feed %d renamed \"%s\"", 
                          feedinfo.id, channeltitle)
                feedinfo.title = channeltitle
        feedinfo.half_flush() # write back to the state database
        
        if self.abort: 
            log.debug("Asked to abort whilst updating feed metadata.")
            return

        # Look for enclosures
        entrynum = 0
        foundenc = 0
        mark_for_download = True
        for entry in feed.entries:
            if self.abort: 
                log.debug("Asked to abort whilst iterating feed entries.")
                return
            entrynum = entrynum + 1
            try:
                try:
                    enclosures = entry.enclosures
                except AttributeError:
                    continue # no enclosures
                if len(enclosures) < 1: 
                    continue # no enclosures
                
                if len(enclosures) > 1:
                    self.warn("Item %d has more than one enclosure", entrynum)

                for enclosure in enclosures: 
                    if self.abort: 
                        break # wrap around faster!

                    # Get enclosure attributes
                    # Use the url from feedburner_origenclosure
		    # instead of crappy feedburner url - Stu
                    if entry.has_key("feedburner_origenclosurelink"):
                        url = entry.feedburner_origenclosurelink
                    else:
                        url = enclosure.get('url')
                    
                    if self.m_ipodder.config.coralize_urls:
                        if "nyud.net:8090" not in url.lower():
                            class C:
                              def __init__(self):
                                self.m_cnt = 0
                              def f(self, x):
                                if self.m_cnt == 0: 
                                  if "http" not in x:
                                    if len(x)!=0:
                                      self.m_cnt += 1
                                      x = x + ".nyud.net:8090"
                                return x
                            
                            c = C()
                            coral_url =  map(c.f, url.split("/"))
                            sb = ""
                            frst = True
                            for i in coral_url:
                                if not frst:
                                    sb += "/"
                                frst = False
                                sb += i 
                            
                            url = sb
       
                    if url is None:
                        self.error("Item %d has enclosure with no 'url' "\
                                   "attribute.", entrynum)
                        continue
                    if not url:
                        self.error("Item %d has enclosure with empty 'url' "\
                                   "attribute.", entrynum)
                        continue
                    try: 
                        length = int(enclosure.get('length', -1))
                    except ValueError, ex: 
                        length = -1

                    #Get the enclosing item's title for displaying in the UI
                    item_title = url
                    if hasattr(entry,'title'):
                        try:
                            str(entry.title)
                            item_title = entry.title
                        except UnicodeEncodeError:
                            item_title = entry.title.encode('ascii','ignore')

                    item_description = ""
                    if hasattr(entry,'description'):
                        item_description = entry.description

                    item_link = ""
                    if hasattr(entry,'link'):
                        item_link = entry.link

                    self.spam("Found enclosure: %s (%d bytes)", url, length)

                    foundenc += 1
                    encinfo = Enclosure(url, feedinfo, length, mark_for_download, item_title, item_description, item_link)

                    # Append the enclosure information to our download list.
                    self.resultlist.append(encinfo)

                    # Update the mark_for_download setting.
                    if mark_for_download:
                        if feedinfo.sub_state == 'newly-subscribed':
                            # This feed is new, so let's only grab the first item.
                            self.info("Feed #%d (%s) is new, so we're only "\
                                      "grabbing the first item. All other items "\
                                      "will be marked as already having been "\
                                      "seen.", feedinfo.id, feedinfo)
                            mark_for_download = False
                        if feedinfo.sub_state == 'preview':
                            self.info("Feed %d (%s) is still in preview mode, "\
                                      "so we're only grabbing the first item.",
                                      feedinfo.id, feedinfo)
                            mark_for_download = False
                        if self.catchup > 0:
                            self.info("User is scanning in catch-up mode, "\
                                      "so we're only grabbing the first item.")
                            mark_for_download = False
                        
            except KeyboardInterrupt:
                raise
            except:
                PLEASEREPORT()
        self.debug("%d enclosure(s) found mentioned in the feed", foundenc)

class DownloadJob(engine.Job): 
    def __init__(self, 
                 myengine, 
                 encinfo, 
                 download_enclosure,
                 update_playlist,
                 #history, #history in db
                 state = {}, 
                 announcer = lambda encinfo: None,
                 downloadingannouncer = lambda encinfo: None,
                 completeannouncer = lambda encinfo, destfile: None,
                 backannouncer = lambda encinfo: None,
                 config = None): 
        """Initialise the DownloadJob."""
        engine.Job.__init__(self, myengine, name=str(encinfo))
        self.encinfo = encinfo
        self.state = state
        self.download_enclosure = download_enclosure
        self.update_playlist = update_playlist
        #self.history = history #history in db
        self.announcer = announcer
        self.downloadingannouncer = downloadingannouncer
        self.completeannouncer = completeannouncer
        self.backannouncer = backannouncer
        self.complete = False
        self.config = config
        self.hooks = hooks.HookCollection()

    def _stop(self): 
        """Try and stop. We'll call the hook, which hopefully 
        iPodder.download_enclosure will have hooked with a 
        method that'll tell the grabber to stop. Pant. Wheeze."""
        self.hooks('stop')

    def run(self): 
        # First, check for free disk space.
        if self.config: 
            freebytes = misc.freespace(self.config.download_dir)
            if freebytes >= 0: 
                freemb = freebytes / 1024**2
                self.debug("Free MB: %d", freemb)
                if freemb < self.config.min_mb_free: 
                    self.error("Download skipped; free space %dMB less " \
                               "than min %dMB.", 
                               freemb, self.config.min_mb_free)
                    return
        # Okay, on with the show. 
        encinfo = self.encinfo
        try:
            if encinfo.status == "clearing":
                log.debug("Download for %s was cleared before we could get to it" % encinfo.url)
            else:
                self.announcer(encinfo)
                encinfo.status = "downloading"
                self.downloadingannouncer(encinfo) # This is redundant, right?
                try: 
                    log.debug("%s", repr(self.download_enclosure))
                    complete, destfile = self.download_enclosure(
                            encinfo, 
                            self.downloadingannouncer,
                            job = self)
                    if complete: 
                        self.complete = True
                        encinfo.filename = destfile
                    #Slowly moving the history to the db
                    #quick pause to save enclosure state
                    #self.history.save_encinfo(encinfo)

                    if complete: 
                        self.completeannouncer(encinfo, destfile)
                        self.update_playlist(destfile, str(encinfo.feed))
                except:
                    self.exception("An error occurred; aborting.")
        finally: 
            self.backannouncer(encinfo)

class DownloadEngine(engine.Engine): 
    """Engine class specifically tuned for Grabbers."""

    def __init__(self, *args, **kwargs):
        engine.Engine.__init__(self, *args, **kwargs)
        self.hooks.add('stopped', self.__stopped)
    
    def __stopped(self): 
        """Called when we're stopped."""
        self.hooks('rate', 0, 0, 0, 0)

    def _tick(self): 
        """Called repeatedly during the Engine's loop."""
        ulrate = 0
        dlrate = 0
        live = 0
        percent_sum = 0
        for worker, job in self.workers.items(): 
            if hasattr(job, 'grabber'): 
                live += 1
                ulrate += job.grabber.upload_rate
                dlrate += job.grabber.download_rate
                percent_sum += (100*job.grabber.fraction_done)

        percent_sum += 100*self.donejobs
        alljobs = self.donejobs + len(self.workers) + self.queue.qsize()
        if alljobs > 0:
            percent = percent_sum/float(alljobs)
        else:
            percent = 100

        self.hooks('rate', live, ulrate, dlrate, percent)


class iPodder:
    def makesafeurl(self, url):
        "PENDING DEPRECATION: make a URL safe."
        return urlnorm.normalize(str(url))

    def feedstoscan(self, contenders=None, polite=True): 
        "Look for feeds to scan."
        log.info("Figuring out which feeds to scan...")
        feeds = []
        now = time.time()
        politenesss = self.config.politeness * 60 # in seconds
        if contenders is None: 
            contenders = self.feeds
        log.debug("We have %d contender(s) to filter.", len(contenders))
        # Just how impolite do we want to be?
        if self.config.force_playlist_updates: 
            log.warn("Last-modified and ETag checks disabled, as "\
                     "force_playlist_updates is set. This is impolite; "\
                     "you should turn it off as soon as possible.")
            log.debug("Returning all %d contender(s).", len(contenders))
            return contenders
        for feedinfo in contenders: 
            if feedinfo.sub_state in ('unsubscribed', 'disabled'): 
                continue
            if feedinfo.sub_state in ('preview'): 
                log.warn("Feed sub_state %s not implemented yet; "\
                         "skipping feed %s", feedinfo)
                continue
            if feedinfo.checked is not None: 
                delta = now - time.mktime(feedinfo.checked)
                if delta < 0: # Daylight Savings? :)
                    delta = politenesss 
                log.debug("Check delta is %d versus politenesss of %d", 
                          delta, politenesss)
                if delta < politenesss: 
                    log.warn("It'd be impolite to scan %s again only "\
                             "%d seconds since we last did it.", feedinfo, 
                             delta)
                    if not polite: 
                        log.warn("... but we'll do it anyway, given "\
                                 "that you singled it out.")
                    else:
                        continue
            feeds.append(feedinfo)
        if len(feeds) == 1: 
            log.info("We have one feed to scan.")
        else: 
            log.info("We have %d feeds to scan.", len(feeds))

        return feeds
        
    def scanenclosures(self, mask=None, catchup=0):
            
        log.info("Pass #1: downloading feeds and looking for enclosures")

        # scan-enclosures-begin hooks get no arguments
        beginner = self.hooks.get('scan-enclosures-begin')
        
        # scan-enclosures-announce hooks get feedinfo
        # encurl is *not* None on the last call
        announcer = self.hooks.get('scan-enclosures-announce')
        backannouncer = self.hooks.get('scan-enclosures-backannounce')
        
        # scan-enclosures-count hooks get encnum, maxnum
        # encnum == maxnum on the last call
        counter = self.hooks.get('scan-enclosures-count')

        # scan-enclosures-end hooks get no arguments
        ender = self.hooks.get('scan-enclosures-end')

        beginner()

        # Step #1: figure out what to scan
        # First, mask the feeds.
        polite = True
        if mask is None: 
            maskedfeeds = self.feeds
        else: 
            maskedfeeds = [feedinfo for feedinfo in self.feeds 
                           if feedinfo in mask]
            if len(mask) < 2: 
                polite = False

        # Second, pass it through a more thorough filter. 
        feeds = self.feedstoscan(maskedfeeds, polite)
        log.info("Scanning...")

        self.m_enclosures = []

        mw = maxworkers=lambda: self.config.max_scan_jobs
        self.scanner = scanner = engine.Engine(mw)
        scanner.hooks.add('counter', counter)
        scanner.hooks.add('doing', lambda job: announcer(job.feedinfo))
        scanner.hooks.add('done', lambda job: backannouncer(job.feedinfo))
        resultlist = []
        num = 0
        for feedinfo in feeds: 
            num = num + 1
            job = FeedScanningJob(scanner, feedinfo, self.m_enclosures, self.state, catchup)
            job.m_ipodder = self
            scanner.addjob(job, priority=num)
            
        scanner.run()
        ender()
        self.scanner = None
        log.info("Pass #1 ended with %d enclosures discovered.",
                 len(self.m_enclosures))
        
    def progress(self, block_count, block_size, total_size):
        #Internal stats must be set for both console and GUI.
        self.m_f_downloaded_size = block_count*block_size;
        self.m_f_total_size = total_size;

        if self.ui_progress:
            self.ui_progress(block_count, block_size, total_size)

    def console_progress(self, block_count, block_size, total_size):
        """Print console progress."""
        print self.m_download_file + " - %.2f MB of %.2f MB\r" % (
                float(block_count*block_size)/1000000, 
                float(total_size)/1000000),
        sys.stdout.flush()

    def filter_enclosure(self, encinfo): 
        """Figure out whether this enclosure needs more work."""
        url = encinfo.url
        feed = encinfo.feed
        filename = feed.get_target_filename(encinfo)
        basename = os.path.basename(filename)
        base, ext = os.path.splitext(filename)
        
        if not encinfo.marked: 
            log.debug("This enclosure has been unmarked for some reason.")
            return False

        #if filter_enclosure.first_check: 
        #    filter_enclosure.first_check = False
        #    log.warn("Enclosure filtering is a little tenuous right now.")
            
        # Take a look at the history
        # DEPENDENCY: when we successfully complete downloading something
        # via BitTorrent, we must add the response file's target filename 
        # to the history, NOT the filenames of whatever we might have 
        # grabbed. 
        historic = self.m_downloadlog.__contains__(basename)
        if historic and not feed.sub_state == 'force':
            log.debug("History says we've already grabbed %s.", basename)
            return False

        # Backup check for old undecoded filenames. 
        basename = url.split('/')[-1]
        historic = self.m_downloadlog.__contains__(basename)
        if historic and not feed.sub_state == 'force':
            log.debug("History says we've already grabbed %s.", basename)
            return False
        
        if ext == '.torrent': 
            # Ghastly, I know, but it'll have to do until we:
            # TODO: maintain state to map torrent URL to filename 
            # and track status. 
            return True

        if feed.get_target_status(url)[0]:
            return False

        # We've survived all checks, so we need to be downloaded. 
        return True
                
    #filter_enclosure.first_check = True
    
    def filter_enclosures(self, enclosures): 
        """Filter discovered enclosures by, well, all sorts of stuff."""
        log.info("Filtering %d discovered enclosures...", len(enclosures))
        survivors = []
        for encinfo in enclosures:
            if self.filter_enclosure(encinfo): 
                survivors.append(encinfo)
        log.info("%d enclosures need more work.", len(survivors))
        return survivors
        
    def download_enclosures(self):
        """Download all the enclosures in self.m_enclosures."""

        log.info("Pass #2: downloading enclosures...")

        # download-content-critical hooks get an error code and
        # error specific args
        criticalerror = self.hooks.get('download-content-critical-error');
        
        # download-content-begin hooks get no arguments
        beginner = self.hooks.get('download-content-begin')
        
        # download-content-announce hooks get encinfo
        # encinfo is *not* None on the last call anymore
        announcer = self.hooks.get('download-content-announce')
        backannouncer = self.hooks.get('download-content-backannounce')
        # download-torrent-* hooks get filename, encinfo
        # we're sometimes checking instead of downloading
        torrentannouncer = self.hooks.get('download-torrent-announce')
        torrentbackannouncer = self.hooks.get('download-torrent-backannounce')

        # download-content-downloading hooks get encinfo
        downloadingannouncer = self.hooks.get('download-content-downloading')
        
        # download-content-downloaded hooks get encinfo, destfile
        # (and thus all feed attrs via encinfo.feed)
        downloadedhooks = self.hooks.get('download-content-downloaded')
        
        # download-content-count hooks get encnum, maxnum
        # encnum == maxnum on the last call
        counter = self.hooks.get('download-content-count')

        # download-content-end hooks get the number of downloads completed.
        ender = self.hooks.get('download-content-end')

        # download-content-rate hooks get live, ulrate, dlrate
        rater = self.hooks.get('download-content-rate')

        # Step #0: determine if we have enough space
        freebytes = misc.freespace(self.config.download_dir)
        if freebytes >= 0: 
            freemb = freebytes / 1024**2
            log.debug("Free MB: %d", freemb)
            if freemb < self.config.min_mb_free: 
                criticalerror(CRITICAL_MINSPACE_EXCEEDED,freemb,self.config.min_mb_free)
                ender(0)
                return 0
            
        # Step #1: figure out what to download
        enclosures = self.filter_enclosures(self.m_enclosures)

        if self.config.dry_run: 
            log.warn("dry_run set: no enclosures will be downloaded.")
            enclosures = []

        # Step #2: scan
        beginner()
        countmax = len(enclosures)
        count = 0
        grabbed = 0

        for encinfo in enclosures:
            encinfo.status = "queued"
            downloadingannouncer(encinfo)

        download_engine = DownloadEngine(
                maxworkers=lambda: self.config.max_download_jobs, 
                name="download")

        download_engine.hooks.add('rate', \
                lambda live, ulrate, dlrate, percent: rater(live, ulrate, dlrate, percent))

        playlist_engine = engine.Engine(
                maxworkers=1, 
                keepgoing=True, 
                name="player")

        def queue_update_playlist(filename, playlistname): 
            """Add a playlist addition job to the playlist_engine."""
            log.debug("Queueing %s on %s...", filename, playlistname)
            job = engine.CurryJob(playlist_engine, 
                    self.updateplaylist, filename, playlistname)
            playlist_engine.addjob(job)

        for encinfo in enclosures: ###
            job = DownloadJob(None, # replace with Engine
                              encinfo, 
                              self.download_enclosure,
                              queue_update_playlist,
                              #self.history, #history in db
                              self.state,
                              announcer,
                              downloadingannouncer,
                              downloadedhooks,
                              backannouncer,
                              config = self.config)
            download_engine.addjob(job, priority=count)
            #try: 
            #    job()
            #    if job.complete: 
            #        grabbed = grabbed + 1
            #except:
            #    log.exception("An error occurred; continuing with next enclosure.")

        counter(0, countmax)
        download_engine.hooks.add('counter', counter)
        
        try: 
            playlist_engine.start() # off it goes!
            download_engine.run() # run it
            playlist_engine.stopgoing() # tell playlist engine to stop 
                                        # after it runs out of jobs
            playlist_engine.join() # wait for it
            playlist_engine.catch() # and throw any exceptions from it
            grabbed = playlist_engine.donejobs
        except KeyboardInterrupt: 
            raise
        except: 
            log.exception("Unexpected exception during download")

        # Final hook calls.
        counter(count, countmax)
        ender(grabbed)
        log.info("Pass #2 ended.")
        return grabbed

    def download_enclosure(self, encinfo, downloadingannouncer, job=None):
        """Download one enclosure."""

        # These two variables get used in progress(). Ugh!
        self.m_f_downloaded_size = -1
        self.m_f_total_size = 0

        iscomplete = False

        enc = encinfo.url
        feed = encinfo.feed
        feed.mkdir()

        # Figure out if this is a BitTorrent response file.
        torrentfile = False
        encsplit = enc.split('/')
        filename = encsplit[-1]
        name, ext = os.path.splitext(filename)
        if ext == '.torrent':
            log.info("That looks like a BitTorrent response file to me.")
            torrentfile = True

        destFile = feed.get_target_filename(enc)
        partialFile = destFile + '.partial'
        try:
            log.info("Downloading %s", enc)
            encinfo.download_started = time.localtime()
            self.m_download_file = filename
            bg = grabbers.BasicGrabber(enc, partialFile, state=self.state)
            if job is not None: 
                job.hooks.add('stop', lambda: bg.stop(wait=False))
                job.grabber = bg
            else: 
                log.warn("Uh, we don't know the grabber...")
            bg.hooks.add('updated', 
                    lambda: self.progress(
                        (100*bg.fraction_done),
                        1.0, 
                        100))
            if downloadingannouncer:
                bg.hooks.add('updated',
                    lambda: downloadingannouncer(encinfo))
            encinfo.grabber = bg
            self.running_grabbers.append(bg)
            #self.progress(blocks, blocksize, size)
            destfilename, headers = bg()
            if job is not None: 
                job.hooks.reset()
                if job.abort: 
                    self.error("Download aborted on request.")
                    raise grabbers.UserAborted
            self.running_grabbers.remove(bg)
            if headers.get('content-type') == "application/x-bittorrent":
                #Failsafe for e.g. php scripts that return .torrents.
                log.debug("Detected application/x-bittorrent mime type.")
                torrentfile = True
            #Check to see if we should rename the file.
            cdisp = headers.get('content-disposition')
            if cdisp:
                log.debug("Detected content disposition: %s" % cdisp)
                if 'filename=' in cdisp:
                    matches = re.match('.*filename=([^;]+)',cdisp)
                    if matches:
                        newname = matches.group(1).strip().strip('"').strip("'")
                        #TODO: detect duplicates
                        destFile = os.path.join(dirname(partialFile),basename(newname))
                        log.debug("Remapped destFile to %s using what we found in the Content-Disposition header." % destFile)
            else:
                newurl = headers.get('__ipodder_redirected_destination_url')
                if newurl:
                    log.debug("Detected redirected destination url: %s" % newurl)
                    destFile = feed.get_target_filename(newurl)
                    log.debug("Remapped destFile to %s using the redirected destination url." % destFile)
                    log.info("Renaming file to %s" % destFile)
            log.debug("Header keys: %s", repr(headers.keys()))
            feed.grabbed = time.localtime()
            encinfo.download_completed = time.localtime()
            iscomplete = bg.complete
            if iscomplete: 
                misc.rename(partialFile, destFile)
                if not torrentfile: 
                    self.m_downloadlog.append(filename)
            else: 
                log.error("The download aborted for some reason.")

        except KeyboardInterrupt: 
            log.error("Keyboard interrupt. Abandoning download...")
        except grabbers.UserAborted:
            log.info("User aborted download of %s", str(enc))
            # Cancelled items will not be re-downloaded, unless the cancel
            # is a byproduct of quitting.
            if not self.quitting and not torrentfile:
                self.m_downloadlog.append(filename)
        except grabbers.GrabError, ex: 
            # Generic error but file not downloaded, set status
            log.error("Can't grab %s: %s", str(enc), ex.message)
            encinfo.status = "error"
            return False, None
        except:
            log.exception("Can't grab %s", enc)
        encinfo.grabber = None

        if not iscomplete: 
            encinfo.status = 'partial'
            return False, destFile

        if torrentfile:
            responseFile = destFile
            responseFilename = filename
            # Strip some variables to stop us from loading the response file's 
            # details into playlists, history, etc. 
            iscomplete = False
            encinfo.download_completed = None
            destFile = filename = ''
            try:
                torrent = grabbers.TorrentFile(responseFile)
                filename = torrent.name
                log.info("Payload name: %s", filename)
                historic = self.m_downloadlog.__contains__(filename)
                if historic and not feed.sub_state == 'force': 
                    log.info("History says we already got torrent "\
                             "payload %s", torrent.name)
                    self.m_downloadlog.append(responseFilename)
                else: 
                    destFile = feed.get_target_filename(filename)
                    log.info("Target filename: %s", destFile)
                    grabber = grabbers.TorrentGrabber(torrent, destFile)
                    grabber.hooks.add('updated', 
                            lambda: self.progress(
                                (100*grabber.fraction_done), 
                                1.0, 
                                100))
                    if downloadingannouncer:
                        grabber.hooks.add('updated',
                            lambda: downloadingannouncer(encinfo))
                    encinfo.grabber = grabber
                    self.m_download_file = filename
                    #torrentannouncer(filename, encinfo)
                    self.running_grabbers.append(grabber)
                    grabber()
                    self.running_grabbers.remove(grabber)
                    #torrentbackannouncer(filename, encinfo)
                    encinfo.download_completed = time.localtime()
                    iscomplete = grabber.complete
                    if iscomplete: 
                        if not historic: 
                            self.m_downloadlog.append(filename)
                            self.m_downloadlog.append(responseFilename)
                    else: 
                        log.error("BitTorrent aborted for some reason.")
            except KeyboardInterrupt: 
                log.error("Keyboard interrupt. Abandoning download...")
            except grabbers.GrabError, ex:
                log.error("Can't grab what %s points to: %s", 
                    str(enc), ex.message)
            except: 
                log.exception("Can't grab what %s points to", 
                    str(enc))
            encinfo.grabber = None

        if iscomplete: 
            encinfo.status = 'downloaded'
            return True, destFile

        encinfo.status = 'partial'
        return False, destFile

    def updateplaylist(self, filename, playlistname):
        player = self.config.player
        if player is not None:
                log.info("Updating playlist %s with %s", playlistname,
                                  os.path.basename(filename))
                player.append_and_create(filename, playlistname, self.config.play_on_download)

    def syncdevices(self):
        player = self.config.player
        if player is not None:
                player.sync()

    def handledeletes(self):
        "Handle scheduled deletions."
        try:
            del_log = open(self.config.delete_list_file, "r")
            for line in del_log:
                filename = line.rstrip()
                try:
                    os.remove(filename)
                except OSError, ex:
                    errno, message = ex.args
                    if errno != 2: # ENOFILE
                        log.exception("Unexpected IO error deleting file %s", filename)
                        # TODO: keep it in the delete list
            del_log.close()
            os.remove(self.config.delete_list_file)
        except IOError, ex:
                errno, message = ex.args
                if errno != 2: # ENOFILE
                    log.exception("Unexpected IO error handling delete list.")
        except:
            log.exception("Caught some problem trying to handle the delete list.")

    def absorbhistory(self):
        """Absorb the history file. We'll stop doing this once we know the
        state database is stable."""

        try:
            history = open(self.config.history_file, 'r')
        except IOError, ex:
            errno, args = ex.args
            if errno != 2:
                log.exception("Unexpected exception opening history file.")
            return
        try:
            entries = [entry.rstrip() for entry in history]
            history.close()
        except IOError, ex:
            log.exception("Unexpected exception reading history file.")
            return
        log.debug("Absorbing %d entries from the history file.", len(entries))
        seen = {}
        for item in self.m_downloadlog:
            seen[item] = 1
        for item in entries:
            if not seen.get(item, 0):
                seen[item] = 1
                self.m_downloadlog.append(item)

    def urlishistoric(self,url):
        urlsplit = url.split('/')
        filename = urlsplit[-1]
        return self.filenameishistoric(filename)

    def filenameishistoric(self,filename):
        if len(self.m_downloadlog) == 0:
            self.absorbhistory()
        return self.m_downloadlog.__contains__(filename)
        
    def appendurlshistory(self,urls):
        filenames = []
        for url in urls:
            urlsplit = url.split('/')
            filename = urlsplit[-1]
            filenames.append(filename)
        self.appendfilenameshistory(filenames)

    def autocleanup(self):
        """Clean up old files according to the user's feed settings."""
        log.info("Starting auto cleanup.")
        contenders = [feedinfo for feedinfo in self.feeds
                        if feedinfo.cleanup_enabled]
        count = 0
        for feedinfo in contenders:
            log.debug("Autocleaning up feed: %s" % feedinfo.title)
            files = self.get_files_to_clean_up(feedinfo)
            if len(files):
                log.info("Autocleanup: cleaning up %d files from %s.",
                    len(files),
                    feedinfo.title)
                count += len(files)
                try:
                    self.config.player.remove_files([(feedinfo.title, files)])
                except NotImplementedError:
                    att = 'warned_player_no_remove_files'
                    if not hasattr(self.autocleanup, att):
                        setattr(self, att, True)
                        log.warn("CastPodder doesn't support removing files " \
                                 "from your particular player. We'll remove " \
                                 "them from your computer, but you might " \
                                 "need to manually remove them from your " \
                                 "player if it won't automatically do it for" \
                                 "you.")
                self.remove_files(files)

        log.info("Finished auto cleanup.")
        return count

    def get_files_to_clean_up(self, feedinfo):
        """Determine which files for a given feed should be cleaned up."""
        log.info("Start getting file list.")
        try:
            min_age = feedinfo.cleanup_max_days

            player_finfos = self.config.player.playlist_fileinfos(
                    feedinfo.title,
                    max_days = min_age)

            target_directory_finfos = feedinfo.getfiles(min_age)

            # strip short filenames out of the file_info tuples
            filenames = [file_info[1]
                         for file_info
                         in player_finfos + target_directory_finfos]
        except:
            log.exception("Caught some problem trying to handle the player file list.")

        log.info("Finished getting file list.")
	return misc.unique(filenames)

    def remove_files(self, files):
        """Removes files and ensures that they're historic so we won't
        download them again."""

        # removing-files hooks get the files that are about to be removed
        self.hooks('removing-files',files)

        flushfiles = []
        for file in files:
            try:
                os.remove(file)
            except OSError, ex:
                errno, message = ex.args
                if errno != 2: # ENOFILE
                    log.exception("Unexpected IO error deleting file %s", file)

            basename = os.path.basename(file)
            if not self.filenameishistoric(basename):
                flushfiles.append(basename)
        if len(flushfiles) > 0:
            self.appendfilenameshistory(flushfiles)


    def removeurlfromhistory(self,url):
        urlsplit = url.split('/')
        filename = urlsplit[-1]

        if len(self.m_downloadlog) == 0:
            self.absorbhistory()

        while (self.m_downloadlog.count(filename)):
            self.m_downloadlog.remove(filename)
        self.appendfilenameshistory(None) #flushes to disk
        
    def start(self, progress, mask=None, catchup=0):
        self.running_grabbers = []
        self.ui_progress = progress

        # First, tell the grabbers module where the proxy server is. 
        # If we don't do this here, we have to pass objects around 
        # all over the place later on.
        self.init_proxy_config()

        try: 
            try: 
                self.absorbhistory()
                self.handledeletes()
                self.scanenclosures(mask,catchup)
                changes = self.download_enclosures()
                changes += self.autocleanup()
                if self.download_enclosures() > 0: 
                    self.syncdevices()
                self.history.clean_history(self.config.clean_history_max_age)
            except: 
                log.exception("Uncaught exception!")
        finally: 
            self.stop()

    def init_proxy_config(self):        
        if self.config.use_proxy_server: 
            grabbers.BasicGrabber.set_global_proxy('http', 
                    self.config.http_proxy_server, 
                    self.config.http_proxy_port,
                    self.config.http_proxy_username,
                    self.config.http_proxy_password)
        else: 
            grabbers.BasicGrabber.set_global_proxy('http', None, None, None, None)
        
    def __init__(self, config, state):
        """Initialise the iPodder.

        config -- configuration.Configuration object
        state -- shelve-style state database or dict
        """

        self.m_downloadlog = []
        self.m_user_os = platform.system();
        self.config = config
        self.state = state
        self.feeds = feeds.Feeds(self.config, self.state)
        self.ui_progress = None
        self.hooks = hooks.HookCollection()
        self.quitting = False
        self.scanner = None

    def stop(self):
        self.appendfilenameshistory(None) #flushes to disk
        
    def appendfilenameshistory(self,filenames):
        "Flush the history file."
        
        newfile = self.config.history_file + ".new"
        oldfile = self.config.history_file + ".old"
        histfile = self.config.history_file

        if len(self.m_downloadlog) == 0:
            self.absorbhistory()

        if filenames:
            for filename in filenames:
                if not self.m_downloadlog.__contains__(filename):
                    self.m_downloadlog.append(filename)
                
        try:
            exclude = open(newfile, "w")
            for filename in self.m_downloadlog:
                print >> exclude, filename
            exclude.close()

            try:
                os.remove(oldfile)
            except OSError, ex:
                errno, message = ex.args
                if errno != 2: # ENOFILE
                    log.exception("Unexpected IO error deleting file %s", oldfile)

            try:
                os.rename(histfile,oldfile)
            except OSError, ex:
                errno, message = ex.args
                if errno != 2: # ENOFILE
                    log.exception("Unexpected IO error renaming file %s", oldfile)

            os.rename(newfile,histfile)
            
        except (IOError, OSError), ex:
            log.exception("Problem flushing history to %s",
                                        self.config.history_file)

    def cancel(self, encinfos_to_cancel):
        "Cancel downloads."
        for encinfo in encinfos_to_cancel:
            log.debug("cancel: Looking for grabber that is downloading %s", encinfo.url)
            if hasattr(encinfo, 'grabber'): 
                grabber = encinfo.grabber
                if grabber is not None: 
                    try: 
                        grabber.stop()
                        encinfo.status = 'cancelled'
                    except: 
                        log.exception("Couldn't stop the grabber!?")
                else: 
                    log.error("Grabber for %s unknown; can't stop it.", encinfo.url)
            else: 
                log.error("encinfo lacks .grabber, so it shouldn't be on its way down.")
        return
        # This shouldn't go anywhere now...
        """
        for grabber in self.running_grabbers:
                if grabber.what == encinfo.url:
                    log.debug("Stopping grabber")
                    grabber.stop()
                    log.debug("Stopped grabber")
                    encinfo.status = 'cancelled'
            if encinfo.url.endswith(".torrent"): 
                log.debug("cancel: torrent: Looking for grabber that is downloading %s" % encinfo.url)
                for grabber in self.running_grabbers:
                    if 0:
                        #PUT HERE: a way to see if running torrentgrabber
                        #goes with the enclosure url.
                        log.debug("Stopping grabber")
                        grabber.stop()
                        log.debug("Stopped grabber")
                        encinfo.status = 'cancelled'
        """

    def cancel_scan(self):
        if self.scanner:
            self.scanner.stop(timeout=60)
 
def main():
    # Initialise the logging module and configure it for our console logging.
    # I'll factor this out soon so it's less convoluted.
    logging.basicConfig()
    handler = logging.StreamHandler()
    handler.formatter = conlogging.ConsoleFormatter("%(message)s", wrap=False)
    log.addHandler(handler)
    log.propagate = 0
    logging.addLevelName(SPAM, "SPAM")
    
    # Parse our configuration files.
    # I'll factor this out soon so it's less convoluted.
    parser = configuration.makeCommandLineParser()
    options, args = parser.parse_args()
    if args:
        parser.error("only need options; no arguments.")
    if options.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    config = configuration.Configuration(options)
    if options.debug: # just in case config file over-rode it
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    # Tweak our sub-log detail.
    hooks.log.setLevel(logging.INFO)
    
    # Open our state database.
    state = statemodule.open(config)
    
    # Initialise our iPodder.
    ipodder = iPodder(config, state)
    return ipodder
  
if __name__ == '__main__':
    ipodder = main()
    try: 
        ipodder.start(ipodder.console_progress)
    finally: 
        ipodder.state.close()
