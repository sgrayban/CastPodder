#!/bin/bash
# CastPodder linux installer 2.1
#
# Created by Scott Grayban <sgrayban@castpodder.net>
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
# Numly ESN: 14249-060713-596240-84 (c) 2006
# http://www.numly.com/numly/verify.asp?id=14249-060713-596240-84
#
# Last updated: $Date: 2006-07-29 00:23:42 -0700 (Sat, 29 Jul 2006) $
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# $Id: install.sh 117 2006-07-29 07:23:42Z sgrayban $
#
#########################################################
#
# lets define all our variables first
# this really makes the script easier to change if needed

NAME="CastPodder"
NAME2="castpodder"
NAME3="iPodder"
INSTALLER_NAME="$NAME installer"
INSTALLER_VERSION="2.2"
INSTALLER_PATH="/opt/${NAME}"
INSTALLER_BIN="/usr/bin"
INSTALLER_COPYRIGHT="Copyright 2005-2006, ${NAME} Team"
INSTALLER_LICENSE="
${NAME} comes with ABSOLUTELY NO WARRANTY. This is free
software, and you are welcome to redistribute it under the terms
of the GNU General Public License.
See LICENSE for details.
"
SUPPORT="http://castpodder.phpbbweb.com/index.php?c=2"
WEBSITE="http://www.castpodder.net"

# Clean active window
clear

echo "Welcome to the ${INSTALLER_NAME}"
echo "${INSTALLER_NAME} written by Scott Grayban"
echo "${INSTALLER_NAME} ${INSTALLER_VERSION} (${INSTALLER_COPYRIGHT})"
echo "${INSTALLER_LICENSE}"
echo "---------------"
echo ""

#check if we are root to install
echo $N "Checking UID... "
if [ `id -u` = "0" ]
  then
    echo "GOOD! your root."
    echo ""
  else
    echo "Sorry, you have to be 'root'. Please su(do) and try again"
    echo ""
    exit 1
fi

# remove all pyc files so that they don't get "accidently" installed
for PYC in `find -name "*.pyc" -type f`; do /bin/rm -f $PYC; done
for PYO in `find -name "*.pyo" -type f`; do /bin/rm -f $PYO; done

# SVN commits/checkouts do some funky things that I dont like with
# file permissions so I'll fix them here
find . -type f -exec chmod 664 {} ";"
find . -name "*.sh" -type f -exec chmod 755 {} ";"
chmod 755 CastPodderGui.py

# lets remove the old historical directory first
if [ -d /opt/iSpider ]
  then
    /bin/rm -fr /opt/iSpider
fi

if [ -d /opt/iPodder ]
  then
    /bin/rm -fr /opt/iPodder
fi

echo "Starting installation/update"
echo ""
# lets check if ipodder has been installed before
# if so we just delete the contents to make sure they get the newest files
# if not we create it
if [ -d ${INSTALLER_PATH} ]
  then
echo "Install type:   Upgrade"
/bin/rm -fr ${INSTALLER_PATH}/*
  else
echo "Install type:   New"
mkdir ${INSTALLER_PATH}
fi

echo "Install path:   ${INSTALLER_PATH}"
echo "Bin path:       ${INSTALLER_BIN}"
echo -e '\E[1;33;44m\E[5m'"\033[1m***NOTE*** Please read README before installing\033[0m\n"
echo -n "Press any key to start or crtl+c to quit. "
read var

echo "Please wait....."
echo ""
echo "Making symbolic link to binary..."
ln -sf ${INSTALLER_PATH}/CastPodder.sh ${INSTALLER_BIN}/${NAME}
ln -sf ${INSTALLER_PATH}/CastPodder.sh ${INSTALLER_BIN}/${NAME2}
ln -sf ${INSTALLER_PATH}/CastPodder.sh ${INSTALLER_BIN}/${NAME3}
echo "Copying files..."
cd ..
cp -f -R castpodder/* ${INSTALLER_PATH}
cd castpodder/

echo "Byte-compiling files for faster start"
PWD=`pwd`
cd ${INSTALLER_PATH}
python compile.py
cd ${PWD}

echo "Installation finished"
echo ""
echo "Please read the files:
	${INSTALLER_PATH}/AUTHORS
	${INSTALLER_PATH}/README
	${INSTALLER_PATH}/ChangeLog
	${INSTALLER_PATH}/TODO
	${INSTALLER_PATH}/KNOWN-ISSUES
	${INSTALLER_PATH}/CREDITS
	${INSTALLER_PATH}/LICENSE
	${INSTALLER_PATH}/COPY
	${INSTALLER_PATH}/THANKS"
echo ""
echo -e "Webiste is at \033[4m${WEBSITE}\033[0m"
echo -e "If you need support goto \033[4m${SUPPORT}\033[0m"
echo ""
echo "You can start ${NAME} with: ${INSTALLER_BIN}/${NAME}"
echo ""
