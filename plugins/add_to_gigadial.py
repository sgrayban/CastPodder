#! python
# -*- coding: utf-8 -*-
#
# $Id: add_to_gigadial.py 158 2006-11-07 09:17:52Z sgrayban $
#
# CastPodder plugin adding a GigaDial menu of the feed in the downloads tab
#

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "GPL"

import wx, logging,sys
from urllib import quote_plus
import re

if sys.version_info[0] == 2 and sys.version_info[1] <= 3:
    import webbrowser
else:
    from ipodder.contrib import webbrowser

log = logging.getLogger('iPodder')
plugin_name = __name__.split('.')[-1]

class Plugin(object):
    """All plugins define a Plugin class."""

    def __init__(self):
        # Report successful load.
        log.info("Loading plugin: %s" % plugin_name)
        # Stores the enclosure after building the menu entry.
        self.enclosure = None
    
    def hook_download_right_click(self, menu, enclosure):
        """This method is called upon generating the right-click menu
        for downloaded episodes in the Downloads tab."""

        # Add a menu item for this enclosure.
        id = wx.NewId()
        menu.Append(id,"Add to GigaDial")

        # Bind a method to the event.
        wx.EVT_MENU(menu, id, self.launch_browser)

        # Save the enclosure info for when the GUI event fires.
        self.enclosure = enclosure

    def launch_browser(self, event):

        gigadial_url = "http://www.gigadial.net/public/choose-or-create"
        enclosure = self.enclosure

        # Strip HTML tags from description, and trim it down to keep IE happy.
        description = enclosure.description.replace('\s',' ')
        description = description.replace('\r\n',' ')        
        description = re.sub('<!--.*?-->', '', description)
        description = re.sub('<.*?>', '', description)
        description = description[0:1499]
        
        # Build up the enclosure data into a query argument.
        argspec = [ ("url", enclosure.url), \
                    ("title", enclosure.item_title), \
                    ("feed", enclosure.feed.url), \
                    ("description", description), \
                    ]

        args = "&".join(["%s=%s" % (k, quote_plus(v)) for (k,v) in argspec])

        launch_url = "%s?%s" % (gigadial_url, args)

        # Launch a web browser and hand off to the user.
        webbrowser.open(launch_url)
