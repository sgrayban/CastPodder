#!/bin/bash
# distribution file for CastPodder
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: compile-me.py 167 2006-11-08 11:06:25Z sgrayban $

#!/bin/bash
# distribution file for CastPodder
# Copyright (c) 2005-2006 Scott Grayban and the CastPodder Team
#
# $Id: compile-me.py 167 2006-11-08 11:06:25Z sgrayban $

cxpath=/home/sgrayban/cx_Freeze/
targ="dist"
targName="CastPodder"
main=CastPodderGui.py

#remove the previous build first but nothing else *yet*
cd $targ
/bin/rm -fr CastPodder *.so
cd ..

#Build the program
$cxpath/FreezePython -c -O \
     --install-dir=$targ \
     --target-name=$targName  \
     --base-binary=$cxpath/bases/ConsoleKeepPath \
     --init-script=ConsoleSetLibPath.py \
     --include-modules=encodings.utf_8,encodings.ascii,encodings.utf_16_be,encodings.utf_16_le,encodings.idna \
     $main

# Following section removes hardcoded paths(rpath)
cd $targ
 for i in *.so
 do
     if chrpath $i 2>/dev/null | grep = >/dev/null
     then
         echo "Fixing $i"
         chrpath -d $i
     else
         echo "no rpath or runpath tag found for $i"
     fi
done
cd ..
/bin/rm -fr dist.tar.bz2
tar jcf dist.tar.bz2 dist/
