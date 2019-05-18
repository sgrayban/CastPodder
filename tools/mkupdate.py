#!/usr/bin/env python
#
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: mkupdate.py 147 2006-11-07 08:17:03Z sgrayban $

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "Commercial"

import zipfile
import time
import os, os.path
import sys

assert os.path.isfile('CastPodderGui.py'), "Run this from the source directory!"

sys.path.insert(0, 'win32')
import setup

filename = "castpodder-%04d-%02d-%02d.zip" % time.localtime()[:3]
filename = os.path.join('dist', filename)
# zipfile.PyZipFile(filename, 'w').writepy('castpodder')
zf = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)

for top in ['ipodder', 'gui']: 
    for root, dirs, files in os.walk(top): 
        if os.path.split(root)[1] == 'CVS': 
            continue
        for file in files: 
            name, ext = os.path.splitext(file)
            if not ext in ['.py']: 
                continue
            print file
            zf.write(os.path.join(root, file))

for root, files in setup.kwargs['data_files']: 
    for file in files: 
        print file
        zf.write(file)

zf.close()
os.system(filename)
