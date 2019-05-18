#
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: clipboard.py 96 2006-07-10 19:50:46Z sgrayban $
#

import platform

enabled = False

def set_clipboard_text_win(text):
    try:
        win32clipboard.OpenClipboard(0)
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
    finally:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass

def set_clipboard_text_mac(text):
    ClearCurrentScrap()
    scrap = GetCurrentScrap()
    scrap.PutScrapFlavor('TEXT', 0, text)
    
if "Win" in platform.system():
    import win32clipboard
    enabled = True
    set_clipboard_text = set_clipboard_text_win
    
if "Darwin" in platform.system():
    from Carbon.Scrap import GetCurrentScrap, ClearCurrentScrap
    enabled = True
    set_clipboard_text = set_clipboard_text_mac
    
"""
if "Linux" in platform.system():
    from clipboard import GetCurrentScrap, ClearCurrentScrap
    enabled = True
    set_clipboard_text = set_clipboard_text_linux
"""
