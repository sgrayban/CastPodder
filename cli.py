#!/usr/bin/env python
#
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: cli.py 145 2006-11-07 07:15:40Z sgrayban $

import updater
updater.loadupdates()
from ipodder.core import main
main()
