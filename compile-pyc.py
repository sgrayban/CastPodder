#!/usr/bin/env python
#
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: CastPodderGui.py 101 2006-07-25 04:58:40Z sgrayban $

"""
CastPodder is Copright © 2005-2006 Scott Grayban
Read the file Software_License_Agreement.txt for more info.

"""
__license__ = "Commercial"

import compileall

print "This may take a while!"

compileall.compile_dir(".", force=1)
