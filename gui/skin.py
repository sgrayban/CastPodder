#
# CastPodder default configurations
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: skin.py 147 2006-11-07 08:17:03Z sgrayban $

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "Commercial"

import os
ATTS = [
    ("STRIPE_ODD_COLOR",'#EDF3FE'),
    ("STRIPE_EVEN_COLOR",'#FFFFFF'),
    ("PRODUCT_NAME",'CastPodder'),
    ("SCREEN_LANGUAGE", 'en'),
    ("CURRENT_VERSION_URL","http://www.castpodder.net/update/current_version_linux.xml"),
    ("DEFAULT_SUBS", [
        ('Default Channel', 'http://radio.weblogs.com/0001014/categories/ipodderTestChannel/rss.xml'), \
        ('CastPodder News', 'http://www.castpodder.net/podcasts/castpodder-users.xml'), \
        ('LugRadio', 'http://www.lugradio.org/episodes.rss')
        ]),

("PODCAST_DIRECTORY_ROOTS", [
        ('http://homepage.mac.com/dailysourcecode/DSC/ipodderDirectory.opml', 'iPodder.org: Podcasting Central'),
        ('http://www.podnova.com/xml_top40.opml', 'PodNova Top 40'),
        ('http://www.gigadial.net/public/opml/dial25.opml', 'GigaDial 25 Latest'),
        ('http://homepage.mac.com/dailysourcecode/opml/podSquad.opml', "Adam Curry's Pod Squad"),
        ('http://directory.ipodderx.com/opml/iPodderX_Popular.opml', 'iPodderX Most Popular'),
        ('http://directory.ipodderx.com/opml/iPodderX_Picks.opml', 'iPodderX Top Picks'),
        ('http://www.podcastalley.com/PodcastAlleyTop50.opml', 'Podcast Alley Top 50'),
        ('http://www.podcastalley.com/PodcastAlley10Newest.opml', 'Podcast Alley 10 Newest'),
        ('http://sportspodnet.com/opml/spn.opml', 'Sports Podcast Network'),
        ('http://podfeed.net/opml/podfeed.opml', 'Podfeed.net 20 Newest / All Categories'),
        ('http://podfeed.net/opml/podfeed_top_rated.opml', 'Podfeed.net Top Rated'),
        ('http://todmaffin.com/radio.opml', 'Radio'),
        ('http://www.techpodcasts.com/dir/tech.opml', 'Techpodcasts.com'),
        ('http://www.castpodder.net/opml/CastPodder.opml', 'CastPodder Team Directory'),
        ('http://www.podcastpickle.com/podPlayer/new/opmlGenres.php', 'PodcastPickle.com All Podcasts by Genre'),
        ('http://www.podcastpickle.com/podPlayer/new/opml25Newest.php', 'PodcastPickle.com newest 25'),
        ('http://www.podcastpickle.com/podPlayer/new/opml25Favorites.php','PodcastPickle.com Top 25'),
        ('http://www.sportpodcasts.com/podPlayer/new/opmlSections.php','SportPodcasts.com'),
        ('http://www.sportpodcasts.com/podPlayer/new/opml10Rated.php','SportPodcasts.com Top 10 Rated'),
        ('http://www.sportpodcasts.com/podPlayer/new/opml10Newest.php','SportPodcasts.com 10 Newest'),
        ]),

    ("SPLASH_LIFETIME", 3000),
    ("SPLASH_DESTROY", True),
    ("DIRECTORY_LINK_SCANNED", '#7F007F'),
    ("DIRECTORY_LINK_UNSCANNED", '#00007F'),
    ("DIRECTORY_LINK_SCANNING", '#7F0000'),
    ("SEARCHBOXFEEDS_FG", '#000000'),
    ("SEARCHBOXFEEDS_BG", '#FFFFFF'),
    ("SUBSCTRL_FG", None),
    ("SUBSCTRL_BG", None),
    ("EPISODES_FG", None),
    ("EPISODES_BG", None),
    ("DOWNLOADS_FG", None),
    ("DOWNLOADS_BG", None),
    ("CLEANUP_FG", '#000000'),
    ("CLEANUP_BG", '#FFFFFF'),
    ("DIRECTORY_FG", None),
    ("DIRECTORY_BG", None),
    ("PRELOAD_SUBS", None),
    ]

#Look for a skin
import os,sys
basepath = os.path.abspath(os.path.split(sys.argv[0])[0])
skinspath = os.path.join(basepath,"gui","skins")
reskin = None
if os.path.exists(skinspath):
    for f in os.listdir(skinspath):
        if f.endswith(".zip"):
            #dead simple for now: use first zip file we find.
            sys.path.append(os.path.join(skinspath,f))
            reskin = __import__('reskin',globals(),locals(),[''])

for att in ATTS:
    if reskin and hasattr(reskin,att[0]):
        globals()[att[0]] = getattr(reskin,att[0])
    else:
        globals()[att[0]] = att[1]

if reskin and hasattr(reskin,"ATTS"):
    for att in reskin.ATTS:
        globals()[att] = getattr(reskin,att)

def set_skin_opts(gui):

    if SEARCHBOXFEEDS_FG:
        gui.searchboxfeeds.SetBackgroundColour(SEARCHBOXFEEDS_BG)
    if SEARCHBOXFEEDS_BG:
        gui.searchboxfeeds.SetForegroundColour(SEARCHBOXFEEDS_FG)

    if SUBSCTRL_BG:
        gui.feedslist.SetBackgroundColour(SUBSCTRL_BG)
    if SUBSCTRL_FG:
        gui.feedslist.SetForegroundColour(SUBSCTRL_FG)


    if EPISODES_BG:
        gui.episodes.SetBackgroundColour(EPISODES_BG)
    if EPISODES_FG:
        gui.episodes.SetForegroundColour(EPISODES_FG)

    if DOWNLOADS_BG:
        gui.downloads.SetBackgroundColour(DOWNLOADS_BG)
    if DOWNLOADS_FG:
        gui.downloads.SetForegroundColour(DOWNLOADS_FG)

    if CLEANUP_BG:
        gui.cleanupepisodes.SetBackgroundColour(CLEANUP_BG)
    if CLEANUP_FG:
        gui.cleanupepisodes.SetForegroundColour(CLEANUP_FG)

    if DIRECTORY_BG:
        gui.opmltree.SetBackgroundColour(DIRECTORY_BG)
    if DIRECTORY_FG:
        gui.opmltree.SetForegroundColour(DIRECTORY_FG)

