#! python
# -*- coding: utf-8 -*-
#
#
# $Id: description_links.py 158 2006-11-07 09:17:52Z sgrayban $
#
# CastPodder plugin adding a description menu of the feed in the downloads tab
#

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "Commercial"

import wx, logging,sys
from sgmllib import SGMLParser

if sys.version_info[0] == 2 and sys.version_info[1] <= 3:
    import webbrowser
else:
    from ipodder.contrib import webbrowser

log = logging.getLogger('CastPodder')
plugin_name = __name__.split('.')[-1]

class Plugin(object):

    def __init__(self):
        log.info("Loading plugin: %s" % plugin_name)
        self.rclickmap = {}

    def hook_download_right_click(self,menu,enclosure):
        return self.hook_episode_right_click(menu,enclosure)
    
    def hook_episode_right_click(self,menu,enclosure):
        self.rclickmap = {}
        if hasattr(enclosure,"description"):
            parser = URLLister()
            try:
                parser.feed(enclosure.description)
                parser.close()
                if len(parser.urls) > 0:
                    submenu = wx.Menu()
                    for (text,url) in parser.urls:
                        if url == enclosure.url:
                            continue
                        id = wx.NewId()
                        submenu.Append(id,text)
                        wx.EVT_MENU(menu, id, self.launch_browser)
                        self.rclickmap[id] = url
                    if submenu.GetMenuItemCount() > 0:
                        id = wx.NewId()
                        menu.AppendMenu(id,"Links",submenu)
            except:
                pass
            
    def launch_browser(self,event):
        if self.rclickmap.has_key(event.GetId()):
            webbrowser.open(self.rclickmap[event.GetId()])

class URLLister(SGMLParser):
    def reset(self):
        SGMLParser.reset(self)
        self.urls = []
        self.achars = ""
        self.url = ""
        self.in_a = False
        
    def start_a(self, attrs):
        href = [v for k, v in attrs if k=='href']
        if href:
            self.url = href[0]
            self.in_a = True
            
    def handle_data(self, text):
        if self.in_a:
            self.achars += text
        
    def end_a(self):
        self.urls.append((self.achars,self.url))
        self.achars = ""
        self.url = ""
        self.in_a = False
